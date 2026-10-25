##################################################
# room_manager.rpy
#
#   房間切換與「探索中途講話」的進出流程
##################################################

# 玩家目前所在的房間，還沒進任何房間時是 None。
default current_room = None

# 注意：change_room() 支援用字串指定房間 (例如 change_room("demo_room"))，
# 這需要遊戲內容那邊自己宣告一個 rooms 字典，例如：
#     default rooms = build_rooms()
# 函式庫這邊刻意不宣告 rooms，因為房間清單屬於遊戲內容、不屬於引擎。

init python:

    def change_room(room_target):
        """
        切換到指定房間。

        room_target 可以直接傳 Room 物件，
        也可以傳房間名稱字串 (例如 "demo_room")，會從 store.rooms 裡面找。
        """
        global current_room

        # 如果傳進來的是字串 (例如 "demo_room")，從 rooms dict 中尋找該物件。
        # 用 getattr 而不是直接寫 store.rooms，是因為 rooms 由遊戲內容那邊宣告，
        # 函式庫不能假設它一定存在 (忘了宣告時給一個看得懂的錯誤，而不是直接當掉)。
        if isinstance(room_target, str):
            all_rooms = getattr(store, "rooms", {})
            if room_target in all_rooms:
                room_target = all_rooms[room_target]
            else:
                renpy.error(f"找不到名稱為 {room_target} 的房間！")
                return

        # 離開舊房間：派發 EXIT_ROOM。
        #
        # 一定要在下面蓋掉 current_room 之前做 —— 蓋掉之後就找不到舊房間了。
        # 第一次進房間 (還沒有舊房間) 沒有東西可離開。
        #
        # default_trigger 給 ENTER_ROOM：掛在 Room.events 沒指定 trigger 的事件
        # 預設是進房事件，所以只有明確寫了 trigger=TriggerType.EXIT_ROOM 的才會跑。
        exit_labels = []

        if current_room is not None:
            exit_labels = collect_events(
                current_room.events,
                TriggerType.EXIT_ROOM,
                EventContext(store.game_state, current_room),
                TriggerType.ENTER_ROOM,
            )

            # 離開時就死了：不進新房間，也不派發新房間的進房事件。
            # 不然玩家會先演完新房間的開場白才死，順序不對。
            # 房間維持在舊的那間；死亡跳轉由 run_event_labels 處理。
            if store.game_state.actors.is_dead(PLAYER_ACTOR):
                renpy.call("run_event_labels", exit_labels)

        # 執行切換房間與鏡頭設定
        current_room = room_target
        camera.enter_room(current_room)

        # 重設房間內的計時：TIMER 事件的倒數從現在開始算。
        #
        # 一定要排在進房事件派發之前 —— 進房事件可能講一長串話，
        # 而對話期間時鐘是暫停的，所以講多久都不影響倒數；
        # 但如果先派發再記時刻，那段對話就會被算進「在房間待了多久」。
        world.mark_room_entered()

        # 房間背景音樂。
        #
        # music 是 None 的房間完全不碰音樂 —— 維持現在正在播的那首。
        # 這樣共用同一首 BGM 的房間不用每間都填，想安靜下來時
        # 自己在 label 裡呼叫 renpy.music.stop() 即可。
        #
        # if_changed=True：同一首歌不會因為走進走出而從頭重播。
        if current_room.music:
            renpy.music.play(current_room.music, if_changed=True)

        # 派發進房事件。
        # 第一階段是純 Python：檢查條件、改狀態、收集要跑的 label。
        context = EventContext(store.game_state, current_room)

        # 離開的 label 排在前面：先演完「離開」，再演「進來」。
        # 兩串合成一次交給 run_event_labels —— renpy.call() 只能跳一次。
        labels = exit_labels + collect_events(
            current_room.events,
            TriggerType.ENTER_ROOM,
            context,
            TriggerType.ENTER_ROOM,
        )

        # 第二階段交給 run_event_labels 依序執行那些 label。
        #
        # 就算 labels 是空的也要走這一趟：死亡檢查在那裡面，
        # 而進房事件可能只扣血、不講話 (Effect(...) 沒帶 label)。
        #
        # 畫面重新整理 (讓新房間的背景與熱點換上去) 也在那邊做 ——
        # 不能寫在這裡，因為 renpy.call() 會直接跳走，
        # 接在它前面的 renpy.restart_interaction() 等於沒用。
        renpy.call("run_event_labels", labels)


# 探索狀態的主迴圈：把控制權交給玩家，讓遊戲一直停在探索畫面上。
#
# 用法：進完房間之後 jump explore_loop
#
# 為什麼需要這個迴圈，不能只寫一句 renpy.pause()：
# 熱點的 Call("say_in_room", ...) 會中斷 pause 去跑對話，
# 講完 return 回來時，返回點是「pause 的下一句」而不是 pause 本身。
# 只寫一句 pause 的話，玩家點第一個熱點、講完話，
# 執行就會往下衝出去 (label 結束 -> 遊戲結束 -> 回主選單)。
# 包成 while True 之後，返回點會落在迴圈裡，再繞回下一次 pause，
# 玩家就能一直探索下去。
#
# 要離開探索狀態時，直接從熱點的 label 裡 jump 到別的地方即可。
label explore_loop:
    while True:
        # 這個房間要不要「設鬧鐘」。
        #
        # 關鍵是 Ren'Py 的這條規則：renpy.pause **沒有**時間限制時會留下
        # 倒帶檢查點，**有**時間限制時不會
        # (renpy.pause 的原始碼：delay 不是 None 時 checkpoint=False)。
        #
        # 所以不能一律用定時輪詢 —— 那會讓整個遊戲在探索狀態下
        # 一個檢查點都沒有，影響的是「讀檔從哪裡接回去」。
        # 改成只有真的有計時事件的房間才設鬧鐘，
        # 其他房間維持原本的寫法，檢查點的行為完全不變。
        python:
            _wait = None

            if current_room is not None:
                _wait = next_timer_wait(
                    current_room.events,
                    world.time_in_room,
                    store.game_state,
                )

        if _wait is None:
            # 沒有計時事件：睡到玩家動作為止 (原本的寫法，留檢查點)。
            #
            # hard=True 代表不能用點擊/空白鍵跳過這個暫停，
            # 但畫面上的熱點按鈕仍然可以正常點擊。
            $ renpy.pause(hard=True)

        else:
            # 有計時事件：睡到下一個到點時間。
            #
            # 醒來之後下面會重新計算，所以「提早醒」沒有任何後果 ——
            # 玩家點熱點會打斷睡眠、系統選單期間時鐘是暫停的，
            # 這兩種情況醒來時都還沒到點，重算之後再睡就是了。
            # 真正要避免的是睡過頭 (事件該發生卻沒發生)，
            # 而睡的長度就是「還剩幾秒」，不會超過。
            $ renpy.pause(_wait, hard=True)

        # 到點的計時事件在這裡派發。
        #
        # 為什麼派發點是這裡，而不是讓時鐘主動打斷玩家：
        # 玩家一點熱點，上面那個 pause 就結束了，執行權跑到熱點的 label
        # (解謎視窗就是從那裡開的)。所以底下這幾行「只會在玩家真的在閒晃
        # 探索時」跑到 —— 那正好就是唯一適合讓事件出場的時機。
        #
        # 反過來若讓時鐘去打斷互動，它分不出現在是探索中的 pause 還是
        # 解謎視窗的 call_screen —— 打斷後者等於把視窗當場關掉。
        python:
            _timer_labels = []
            _timer_fired = False

            # world.dispatching：正在演別的事件就不插隊，等下一輪再看。
            if current_room is not None and not world.dispatching:
                _due = due_timer_events(current_room.events, world.time_in_room)

                if _due:
                    # 「有沒有真的觸發」不能只看回傳的 label：
                    # 事件可能只扣血不講話 (Effect 沒帶 label)，
                    # 那時 label 是空的，但死亡檢查一定要跑到。
                    # 所以比對觸發次數有沒有變。
                    _counts_before = {}
                    for _e in _due:
                        _counts_before[_e.id] = store.game_state.events.count_of(_e.id)

                    # max_fires=1：同時好幾個到點時只放最重要的那一個，
                    # 但「最重要的那個」條件不成立時要往下找。
                    _timer_labels = collect_events(
                        _due,
                        TriggerType.TIMER,
                        EventContext(store.game_state, current_room),
                        TriggerType.TIMER,
                        max_fires=1,
                    )

                    for _e in _due:
                        if store.game_state.events.count_of(_e.id) != _counts_before[_e.id]:
                            _timer_fired = True

        if _timer_fired:
            call run_event_labels(_timer_labels) from _call_timer_events


# 所有「探索中途要講話」的入口都走這裡：熱點的 action、Room.on_enter 都可以用。
# 用法：action Call("say_in_room", "你寫的label名稱")
# 或是在 python 裡：renpy.call("say_in_room", "你寫的label名稱")
#
# 用途：先把熱點按鈕收起來 (不然按鈕會搶走點擊，對話點不下去)，
# 只留房間背景，講完/做完事之後再自動恢復成可以互動探索的畫面。
# 內部就是「只跑一個 label 的 run_event_labels」，
# 畫面切換、收對話框的邏輯完全共用，不再各寫一份。
label say_in_room(next_label):
    call run_event_labels([next_label]) from _call_say_in_room
    return