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

        # 如果這個房間有設定 on_enter 而且還沒超過觸發次數上限，
        # 進來時自動講話/執行那個 label
        if room_target.can_trigger_on_enter():
            room_target.on_enter_count += 1
            renpy.call("say_in_room", room_target.on_enter)
        else:
            # 沒有 on_enter 的話，至少要讓畫面重新整理一次，
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
label say_in_room(next_label):
    hide screen explore
    show screen room_background

    call expression next_label from _call_expression

    # 把對話框收起來。
    # Ren'Py 的對話框不會因為「對話講完了」就自動消失，
    # 它會一直留在畫面上直到有人叫它收起來。
    # 不寫這行的話，回到探索狀態後最後一句話會一直掛在畫面下方。
    window hide

    hide screen room_background
    show screen explore

    return