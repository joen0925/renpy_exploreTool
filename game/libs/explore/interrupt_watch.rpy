##################################################
# interrupt_watch.rpy
#
#   「鬼到了就把玩家手上的視窗關掉」的共用機制。
#
#   解謎視窗 (run_puzzle) 與近景視窗 (open_closeup) 都用這一份。
#
#   ---
#
#   為什麼需要它
#
#   這兩種視窗都是 renpy.call_screen，而 call_screen 會**卡住執行**。
#   計時事件的派發點在 explore_loop 裡 (見 room_manager.rpy)，所以
#   視窗開著的期間：
#
#     - 時鐘**在走** (Puzzle.pausable=False 與近景都是這樣)
#     - 但**沒有人在檢查「誰到點了」** —— explore_loop 被卡在熱點的 label 裡
#
#   什麼都不做的話，鬼的時間到了也要等玩家自己關掉視窗才會發生 ——
#   也就是**玩家躲在解謎視窗裡就永遠安全**，pausable=False 等於沒有意義。
#
#   ---
#
#   怎麼關窗：讓畫面動作回傳值
#
#   Ren'Py 的規則是「畫面動作回傳非 None 就結束當前互動，而那個回傳值
#   就是 call_screen 的結果」。所以這裡的 timer 到點時回傳
#   PUZZLE_INTERRUPTED / CLOSEUP_INTERRUPTED，沒到點就回傳 None
#   (= 什麼都沒發生，互動繼續)。
#
#   這條路等於玩家自己按 ✕ —— 視窗正常收尾，拖曳到一半的狀態、
#   倒帶紀錄都由既有的流程處理，不必從外面硬砍視窗。
#
#   (這個機制是「意外證明」的：2026-10-22 世界時鐘的 timer 誤把 dt
#    回傳出去，當場把翻頁視窗與解謎視窗全部關掉。那個 bug 就是這裡的做法)
#
#   ---
#
#   為什麼是獨立的一個 screen，而不是寫在每個解謎畫面裡
#
#   因為 run_puzzle 的契約是「只認四個屬性」(見 puzzle.rpy)，
#   寫新的關卡類型不該還要記得掛一個中斷用的 timer —— 忘記掛的人
#   會做出一個「鬼抓不到玩家」的關卡，而這件事試玩不會發現。
#
#   改成由 run_puzzle 自己 show 這個畫面之後，關卡類型完全不用知道
#   它的存在。近景視窗同理。
#
#   ---
#
#   狀態：沒有。
#
#   刻意不留「該中斷了」的旗標 (原本的 world.interrupt 已經刪掉)。
#   旗標要有人舉、有人降，還要處理讀檔與倒帶時的殘留；
#   而每次重新問一遍是冪等的 —— 讀任何存檔、倒帶幾次，答案都跟
#   當下的狀態一致。這跟熱點用 condition 推導顯隱、而不是命令式
#   hide() 是同一個選擇。
##################################################

init python:

    # 多久問一次「鬼到了嗎」。
    #
    # 0.2 秒跟 explore_loop 設鬧鐘的下限 (WORLD_WAIT_FLOOR) 一致 ——
    # 兩邊是同一件事的兩種情況 (閒晃中 / 視窗開著)，反應速度沒道理不同。
    WORLD_INTERRUPT_POLL = 0.2

    def world_interrupt_result(result):
        """
        視窗的 timer action。該中斷就回傳 result，不該就回傳 None。

        ⚠️ 回傳 None 是有意義的，不是「忘了回傳」——
        畫面動作回傳 None 代表「什麼都沒發生、互動不要結束」。
        回傳非 None 才會結束 call_screen 並把那個值交出去。

        純查詢，不改任何狀態 (pending_interrupt 保證只讀)，
        所以每 0.2 秒呼叫一次是安全的。
        """
        room = store.current_room

        if room is None:
            return None

        event = pending_interrupt(
            room.events,
            store.world.time_in_room,
            EventContext(store.game_state, room),
        )

        if event is None:
            return None

        return result


# 掛在視窗旁邊的守望畫面。沒有任何看得見的東西，只有一個 timer。
#
# 用法 (在開視窗之前)：
#     show screen world_interrupt_watch(PUZZLE_INTERRUPTED)
#     $ _result = renpy.call_screen(...)
#     hide screen world_interrupt_watch
#
# 為什麼是另一個 screen 而不是塞進 call_screen 的那個畫面：
# 同一個互動裡任何畫面的動作都能結束它，所以守望可以完全獨立 ——
# 關卡畫面與近景畫面都不用改一行。
screen world_interrupt_watch(result):
    timer WORLD_INTERRUPT_POLL repeat True action Function(world_interrupt_result, result)
