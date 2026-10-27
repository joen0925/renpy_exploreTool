##################################################
# jumpscare.rpy
#
# 嚇人視窗：畫面壓黑、一張圖撲到正中央、自己關掉。
#
# 這個檔案不依賴探索工具包的任何東西 (Room / Camera / Hotspot 都沒用到)，
# 可以單獨複製到別的 Ren'Py 專案使用。
#
# 用法：在任何 label 裡寫
#
#     call show_jumpscare("ghost_face")
#
# 呼叫端會停在這裡，等視窗自己關掉才往下走 ——
# 所以「扣血」「講話」這些後續直接寫在下一行就好，順序一定對。
#
#     label ghost_arrives:
#         call show_jumpscare("ghost_face")
#         $ Effect(actor="player", stats={"hp": -3}).apply(game_state)
#         "牠碰到你了。"
#         return
#
# 圖怎麼給：傳「圖片名稱」而不是 displayable 物件。
#
#     image ghost_face = Text("👻", size=420)
#
# 傳名稱是刻意的 —— label 的參數會進呼叫堆疊，而呼叫堆疊會被寫進存檔。
# 傳字串進去永遠存得起來；傳一個現做的 displayable 就要賭它能不能被
# pickle。這跟 Room / Hotspot / Puzzle 都只傳名稱是同一個理由。
#
# 沒有美術素材也能用：上面那行 Text("👻", size=420) 就是一張合法的圖。
#
# 時間長度：預設 JUMPSCARE_DURATION，想單獨調就傳第二個參數
#
#     call show_jumpscare("ghost_face", 2.0)
#
# 音效：這個視窗刻意不管聲音。要配尖叫就在呼叫之前自己播
#
#     $ renpy.play("audio/scream.ogg")
#     call show_jumpscare("ghost_face")
#
# 這樣聲音與畫面誰先誰後由你決定，而不是由這個檔案替你決定。
##################################################

init python:

    # 視窗關掉時的回傳值。
    #
    # ⚠️ 不能用 Return() 不帶參數 —— 那會回傳 True 而不是 None
    #    (理由見 game/libs/puzzle/puzzle.rpy 開頭的長註解)。
    #    這裡其實沒人看這個回傳值，但還是給它一個具名字串：
    #    哪天有人要分辨「自己關掉」與「被玩家跳過」就有地方掛。
    JUMPSCARE_DONE = "jumpscare_done"

    # 預設停留幾秒。
    #
    # 1.2 秒是「看清楚了但來不及反應」的長度。再長會變成「在看一張圖」，
    # 再短玩家會懷疑自己是不是眼花。
    JUMPSCARE_DURATION = 1.2


screen jumpscare(image, duration):
    # 擋住後方所有東西。嚇人期間不該點得到任何熱點。
    modal True

    # 比近景視窗 (200) 更上面 —— 嚇人一定要蓋在所有東西上。
    zorder 300

    # 壓得比翻頁視窗黑 (那邊是 cc)，讓圖整個跳出來。
    add "#000000ee"

    add image:
        align (0.5, 0.5)

    # 自己關掉。
    #
    # 刻意**沒有**關閉鈕、也不吃點擊 —— 嚇人的長度要由設計者決定，
    # 不是由玩家的手速決定。玩家連點的話，提早關掉就不嚇人了。
    #
    # 不是 repeat：只要響一次。
    timer duration action Return(JUMPSCARE_DONE)


# 顯示嚇人視窗並「等它自己關掉才繼續」的入口。
label show_jumpscare(image, duration=None):

    # 收掉對話框(黑框)，不然會疊在圖上面
    window hide

    $ _js_duration = JUMPSCARE_DURATION if duration is None else duration

    # 倒帶要跳過這個視窗。
    #
    # call screen 本來是倒帶的停靠點，而這個視窗是 modal，會擋住
    # quick menu 的「返回」鈕。雖然它會自己關掉 (所以不像翻頁視窗那樣
    # 會把玩家困死)，但倒帶停進去的話玩家會莫名其妙又被嚇一次，
    # 而且那 1.2 秒內什麼都按不到。
    #
    # 跳過之後，倒帶會從「嚇完之後的對話」直接退回「事件發生之前」——
    # 連扣掉的血都會一起還原，因為那是在這之後才扣的。
    $ renpy.suspend_rollback(True)

    # 嚇人期間世界時鐘暫停。這是一段演出，不是玩家在操作。
    #
    # 用 getattr 問一下是為了維持這個檔案的獨立性 ——
    # 單獨複製到沒有 world 的專案也能用。
    # (跟 page_popup.rpy 同一個寫法)
    $ _js_world = getattr(store, "world", None)

    if _js_world is not None:
        $ _js_world.pause("jumpscare")

    call screen jumpscare(image=image, duration=_js_duration)

    if _js_world is not None:
        $ _js_world.resume("jumpscare")

    $ renpy.suspend_rollback(False)

    return
