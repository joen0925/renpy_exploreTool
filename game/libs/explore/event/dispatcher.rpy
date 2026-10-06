##################################################
# dispatcher.rpy
#
#   事件派發：把「檢查條件、改狀態」跟「跑劇情」切成兩個階段。
#
#   為什麼要切兩段：
#   一個房間可能同時觸發多個 Event，每個 Effect 都可能帶一個 label。
#   但 renpy.call() 只能跳一次 —— 它會終止當前語句直接跳走，
#   後面的 Python 程式碼不會執行，所以沒辦法在一個函式裡連續跑好幾個 label。
#
#   第一階段 collect_events()  純 Python，不跳轉。
#                              排序 → 跳過死的 → 檢查條件 → 骰機率 → 改狀態 →
#                              把 label 收集成清單 → 記錄次數 → 遇到 stop 中斷
#
#   第二階段 run_event_labels  label 驅動。收起探索畫面 → 依序 call 那些 label
#                              → 放回探索畫面
#
#   切開的附帶好處：第一階段是純函式，可以直接餵假的 GameState 測
#   「什麼條件下會收集到哪些 label」，完全不用啟動畫面。
##################################################

init python:

    def collect_events(events, trigger, context, default_trigger=None):
        """
        第一階段：檢查條件、套用狀態改動，回傳要依序執行的 label 清單。

        events           要檢查的 Event 清單 (Room.events 或 Hotspot.events)
        trigger          這次派發的觸發時機 (TriggerType)
        context          EventContext
        default_trigger  Event 沒指定 trigger 時採用的時機

        這個函式「不會」跳轉，也不會碰畫面，跑完才由 run_event_labels 接手。
        """
        if not events:
            return []

        if default_trigger is None:
            default_trigger = trigger

        game_state = context.game_state
        labels = []

        # sequence 小的先跑。每個掛載點 (房間/熱點) 各自獨立排序。
        for event in sorted(events, key=lambda e: e.sequence):

            if not event.can_fire(context, default_trigger, trigger):
                continue

            # 機率事件：骰輸了就當作這次沒發生。
            #
            # 排在 can_fire 之後才骰，有兩個理由：
            #   1. 條件都不符的事件不該白骰 —— 每骰一次 Ren'Py 都會
            #      強制產生一個倒帶檢查點。
            #   2. can_fire 要維持「只讀、可重複呼叫」的契約。
            #
            # 骰輸「不算觸發過」：底下的 record_trigger 不會跑到，
            # 所以次數不加、limit 不消耗。不然 limit=1 的機率事件
            # 第一次骰輸就死亡，玩家永遠遇不到它。
            if not chance_passes(event.chance):
                continue

            # 條件通過，這裡開始才會改狀態
            if event.effect is not None:
                label = event.effect.apply(game_state)
                if label:
                    labels.append(label)

            # 記錄觸發次數，次數用完會自動轉成死亡
            game_state.events.record_trigger(event.id, event.limit)

            if event.stop:
                break

        return labels


    def find_duplicate_event_ids(rooms):
        """
        檢查所有房間裡有沒有重複的 event id，回傳重複的 id 清單。

        id 必須全域唯一 —— EventState 用它當 key，
        兩個 Event 撞名的話會共用觸發次數與死亡狀態，
        症狀是「另一個房間的事件莫名其妙不觸發了」，非常難查。

        debug 面板會呼叫這個做檢查。
        """
        seen = set()
        duplicates = []

        for room in rooms.values():
            # 用 getattr 是因為 Room / Hotspot 不一定都有 events
            # (簡寫的 on_enter / on_click 也可能還沒展開成 Event)
            events = list(getattr(room, "events", None) or [])

            for hotspot in room.hotspots:
                events.extend(getattr(hotspot, "events", None) or [])

            for event in events:
                if event.id in seen:
                    duplicates.append(event.id)
                else:
                    seen.add(event.id)

        return duplicates


    def player_death_label():
        """
        玩家死了的話，回傳要跳過去的 label 名稱；還活著或內容層沒宣告就回傳 None。

        死亡 label 由遊戲內容宣告，引擎不寫死名字：
            define on_player_death = "game_over"

        沒宣告的話這裡回傳 None，玩家死掉就只是「hp 是 0」這個狀態，
        遊戲會繼續跑 —— 不會當掉，但也不會有 Game Over。
        """
        if not store.game_state.actors.is_dead(PLAYER_ACTOR):
            return None

        return getattr(store, "on_player_death", None)


# 第二階段：依序執行第一階段收集到的 label。
#
# 用法 (從 python 呼叫)：
#     renpy.call("run_event_labels", labels)
#
# 跟 say_in_room 是同一套畫面切換：先把熱點按鈕收起來
# (不然按鈕會搶走點擊，對話點不下去)，只留房間背景，
# 全部跑完再恢復成可以互動的探索畫面。
label run_event_labels(labels):

    # 沒有 label 要跑就不要白白閃一次畫面。
    # 注意「什麼都不做」不等於「直接 return」—— 底下的死亡檢查一定要跑到，
    # 因為 Effect 可能只扣血、不講話。
    if labels:

        hide screen explore
        show screen room_background

        # labels 是 label 的參數，Ren'Py 會幫它做 scope。
        # 所以就算某個 label 裡面又觸發了新的事件 (例如換房間)，
        # 內外層的清單也不會互相蓋掉。
        while labels:
            $ _next_event_label = labels.pop(0)
            call expression _next_event_label from _call_event_label

        # 收起對話框。不做的話最後一句話會一直掛在畫面下方。
        window hide

        hide screen room_background
        show screen explore

    else:
        # 沒有 label 要跑：不切畫面 (不要白白閃一次)，
        # 但還是要讓畫面重新整理一次 ——
        # 換房間如果沒有任何進房對話，新房間的背景與熱點要馬上換上去。
        $ renpy.restart_interaction()

    # 死亡檢查。
    #
    # 刻意等「整串 label 都跑完」才檢查，而不是每跑完一個就檢查：
    # 這樣「鬼撲上來」的對話與動畫才有機會完整演完，
    # 不會扣完血就被硬生生打斷。
    #
    # 用 jump 不是 call —— 死掉不該回到探索迴圈。
    # 所以死亡 label 不會 return 回來，它要自己收尾
    # ($ MainMenu()、jump 回檢查點、或 renpy.full_restart())。
    $ _death_label = player_death_label()

    if _death_label:
        # 跳走之前先把探索畫面收起來。
        # 上面已經 show 回去了，不收的話死亡演出期間熱點還點得到。
        hide screen explore
        jump expression _death_label

    return
