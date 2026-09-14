##################################################
# puzzle.rpy
#
#   解謎關卡的共同流程。
#
#   什麼東西該做成 Puzzle：
#     有「臨時內部狀態」的關卡 —— 密碼鎖按到一半的數字、拼圖現在的排列、
#     連線連到一半。那個狀態不是遊戲進度，不該進存檔、也不該污染 GameState。
#
#   什麼東西「不用」做成 Puzzle：
#     「打開抽屜 -> 裡面有小物可以拿」這種近景觀察，用一個
#     bg_width=1920 的房間就好 (等於螢幕寬，鏡頭不會捲動 = 定格特寫)。
#     熱點、條件、事件、物品欄全部照舊能用，零行新程式碼。
#
#   用法：
#     1. 內容層宣告一份目錄
#            define puzzle_catalog = build_puzzles()
#     2. 熱點的 label 裡呼叫
#            call run_puzzle("safe_keypad")
#
#   為什麼傳「名稱」不傳物件：
#   label 的參數會進呼叫堆疊，而呼叫堆疊會被寫進存檔。
#   Puzzle 是靜態定義，跟 Room / item_catalog 一樣不該進存檔。
#   (Room 與 Hotspot 是用 __reduce__ 只存名稱來解決同一個問題)
#
#   ---
#
#   關卡類型怎麼擴充：不要繼承。
#
#   game/libs/ 底下的檔案是混在一起按檔名字母序載入的 (見 libs.txt)，
#   繼承的話基底類別很可能還沒定義就被拿來繼承。
#   所以這裡用鴨子型別 —— run_puzzle 只碰下面四個屬性：
#
#     screen      要顯示哪個 screen (字串)。那個 screen 會收到 puzzle=自己
#     on_success  答對時套用的 Effect
#     on_failure  答錯時套用的 Effect，可以是 None (答錯沒代價)
#     pausable    解謎途中世界要不要暫停 (見下面的說明)
#
#   任何有這四個屬性的物件都能跑。KeypadPuzzle 就是這樣的一個普通類別，
#   之後要做拼圖、連線，再寫一個類別 + 一個 screen 就好，引擎完全不用改。
#
#   ---
#
#   screen 要回傳三種值其中之一 (用下面的常數，不要自己寫字串)：
#
#     PUZZLE_SOLVED   答對了    -> 套用 on_success
#     PUZZLE_FAILED   答錯了    -> 套用 on_failure (沒設就什麼都不做)
#     PUZZLE_CLOSED   關掉視窗  -> 什麼都不做，不算失敗
#
#   關掉視窗刻意不算失敗 —— 這樣才有「可以關掉，但沒有放棄的選項」的效果。
#
#   ⚠️ 為什麼是字串常數而不是 True / False / None
#
#   因為 Ren'Py 的 Return() 不帶參數時「回傳的是 True 不是 None」：
#
#       class Return(Action):
#           def __call__(self):
#               if self.value is None:
#                   ...
#                   return True        # ← 這裡
#               else:
#                   return self.value
#
#   理由是畫面動作回傳 None 代表「什麼都沒發生、互動不要結束」，
#   所以 Return() 必須回傳一個非 None 的值才停得下來。
#
#   結果就是：關閉鈕寫 Return() 的話，run_puzzle 會收到 True ——
#   如果契約是「True = 答對」，玩家一按 ✕ 就直接開鎖了。
#   (這個 bug 真的發生過，keypad_flow 測試抓到的)
#
#   用具名字串就完全避開這個地雷，而且看程式碼就知道是什麼意思。
#   收到任何預期外的值一律當成「什麼都不做」—— 失敗方向偏安全。
##################################################

init python:

    # 關卡 screen 的回傳值。三個都刻意是非空字串，不要改成 True/False/None。
    PUZZLE_SOLVED = "solved"
    PUZZLE_FAILED = "failed"
    PUZZLE_CLOSED = "closed"

    def puzzle_def(key):
        """
        從解謎目錄查一個關卡的定義。查不到回傳 None。

        目錄由遊戲內容那邊宣告，例如：
            define puzzle_catalog = build_puzzles()
        引擎不宣告它，因為關卡清單屬於遊戲內容。
        """
        return getattr(store, "puzzle_catalog", {}).get(key)


    def puzzle_result_effect(puzzle, result):
        """
        依照關卡的結果挑出該套用的 Effect，沒有對應的就回傳 None。

        純函式，不改任何狀態 —— 這樣可以直接餵假的結果測「哪種結果配哪個 Effect」，
        不用真的把畫面叫出來。
        """
        if result == PUZZLE_SOLVED:
            return puzzle.on_success

        if result == PUZZLE_FAILED:
            return puzzle.on_failure

        # PUZZLE_CLOSED (關掉視窗)，或任何預期外的值，都不套用任何 Effect。
        # 預期外的值也走這條路是刻意的：新的關卡類型如果不小心寫了
        # Return()，收到的會是 True —— 那時候「什麼都不做」比「當成答對」安全。
        return None


# 開一個解謎關卡，等玩家做完，再依結果套用 Effect。
#
# 用法 (在熱點的 label 裡)：
#     call run_puzzle("safe_keypad")
#
# 畫面處理跟 page_popup 同一套：關卡的 screen 自己是 modal，
# 所以不用先把探索畫面收起來 —— modal 已經擋掉底下的點擊了。
# (底下的鏡頭仍然會跟著滑鼠移動，跟翻頁視窗一樣，這是刻意允許的)
label run_puzzle(puzzle_key):

    python:
        _puzzle = puzzle_def(puzzle_key)

        if _puzzle is None:
            renpy.error(
                f"找不到名稱為 {puzzle_key} 的解謎關卡！\n"
                f"是不是忘了在 build_puzzles() 裡加進去？"
            )

    # 收掉對話框，不然會疊在關卡視窗上
    window hide

    # 倒帶要跳過關卡畫面 —— 跟翻頁視窗 (page_popup) 同一個問題：
    #
    # 關卡的 screen 是 modal，會擋住 quick menu 的「返回」。
    # 如果倒帶會停在這裡，玩家關掉關卡之後按返回就會回到關卡裡，
    # 在裡面又按不到返回，形成出不去的迴圈。
    #
    # 跳過之後，倒帶會從「解謎結果的對話」直接退回「打開關卡之前」，
    # 而結果套用的 Effect (例如答錯扣的血) 也會一起被倒帶還原。
    $ renpy.suspend_rollback(True)

    # 玩家在這裡操作，直到 screen 執行 Return(...)
    $ _puzzle_result = renpy.call_screen(_puzzle.screen, puzzle=_puzzle)

    $ renpy.suspend_rollback(False)

    python:
        # 依結果套用 Effect，並收集要跑的 label。
        # 這裡只改狀態、不跳轉 —— 跟 collect_events 是同一個分工。
        _puzzle_labels = []
        _puzzle_effect = puzzle_result_effect(_puzzle, _puzzle_result)

        if _puzzle_effect is not None:
            _next = _puzzle_effect.apply(store.game_state)
            if _next:
                _puzzle_labels.append(_next)

    # 交給既有的第二階段執行。
    #
    # 走這裡而不是自己 call，是為了把死亡檢查一起吃下來 ——
    # on_failure 可以是 Effect(actor="player", stats={"hp": -1})，
    # 扣到 0 就會走既有的 on_player_death 流程，不用在這裡再寫一次。
    call run_event_labels(_puzzle_labels) from _call_run_puzzle

    return
