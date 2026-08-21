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

        # 執行切換房間與鏡頭設定
        current_room = room_target
        camera.enter_room(current_room)

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

        labels = collect_events(
            current_room.events,
            TriggerType.ENTER_ROOM,
            context,
            TriggerType.ENTER_ROOM,
        )

        if labels:
            # 第二階段交給 run_event_labels 依序執行那些 label
            renpy.call("run_event_labels", labels)
        else:
            # 沒有事件要跑的話，至少要讓畫面重新整理一次，
            # 新房間的背景與熱點才會馬上換上去
            renpy.restart_interaction()


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
        # hard=True 代表不能用點擊/空白鍵跳過這個暫停，
        # 但畫面上的熱點按鈕仍然可以正常點擊。
        $ renpy.pause(hard=True)


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