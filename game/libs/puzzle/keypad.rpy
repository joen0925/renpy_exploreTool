##################################################
# keypad.rpy
#
#   密碼鎖關卡。第一個 Puzzle 類型。
#
#   用法 (在內容層的 build_puzzles() 裡)：
#
#       puzzles["safe_keypad"] = KeypadPuzzle(
#           code="4721",
#           title="保險箱",
#           hint="生鏽的鐵牌上刻著四個數字",
#
#           on_success=Effect(set_flags=["safe_opened"],
#                             give_items=["documents"],
#                             label="safe_opens"),
#
#           # 答錯的代價。不填就是答錯沒事，可以一直重試。
#           on_failure=Effect(actor="player", stats={"hp": -1},
#                             label="safe_shock"),
#       )
#
#   然後在熱點的 label 裡 call run_puzzle("safe_keypad")。
#
#   答錯就關掉視窗、套用 on_failure，玩家要重試就再點一次熱點。
#   刻意不做「視窗留著一直試」——
#   因為 Effect 要跑 label，而 label 沒辦法在視窗開著的時候跑，
#   那樣「答錯扣一滴血」這種即時代價就做不出來了。
##################################################

init python:

    class KeypadPuzzle:
        """
        密碼鎖。不繼承任何東西 —— run_puzzle 只要求
        screen / on_success / on_failure / pausable 這四個屬性 (鴨子型別)。
        """

        def __init__(
            self,
            code,               # 正確密碼。數字或字串都可以，內部一律轉成字串
            on_success,         # 答對時套用的 Effect
            on_failure=None,    # 答錯時套用的 Effect，None = 答錯沒代價

            title="密碼鎖",     # 視窗標題
            hint=None,          # 標題底下的提示文字，可省略

            # 解謎途中世界要不要暫停。
            #
            #   True  (預設)  世界停下來等玩家。單純的謎題，想多久都沒關係。
            #   False         世界繼續走，鬼照樣逼近 —— 而且標了
            #                 interrupt=True 的計時事件到點時會把視窗
            #                 當場關掉 (回傳 PUZZLE_INTERRUPTED，不算答錯)。
            #
            # 被打斷的處理由 run_puzzle 自己掛上，關卡類型完全不用管
            # (見 game/libs/explore/interrupt_watch.rpy)。
            # 完整說明見 DEVELOPER_GUIDE.md 的「被鬼打斷」那一節。
            pausable=True,
        ):
            # run_puzzle 要找的四個屬性
            self.screen = "keypad_puzzle"
            self.on_success = on_success
            self.on_failure = on_failure
            self.pausable = pausable

            # 密碼鎖自己的設定
            self.code = str(code)
            self.title = title
            self.hint = hint

        def __repr__(self):
            return f"<KeypadPuzzle {self.title} ({len(self.code)} 位)>"


screen keypad_puzzle(puzzle):

    # 擋住後方所有東西，視窗開著時點不到底下的熱點。
    # 跟 page_popup 同一套做法，所以不需要先把探索畫面收起來。
    modal True

    zorder 200

    # 玩家目前按了哪些數字。
    #
    # 用 screen 自己的變數 (default) 而不是 store 變數 ——
    # 這是「按到一半」的臨時狀態，不是遊戲進度，
    # 關掉視窗就該消失，也不該存進存檔。
    default entered = ""

    $ _code_len = len(puzzle.code)
    $ _is_full = (len(entered) >= _code_len)

    # 按 ESC (或滑鼠右鍵) 關掉視窗 -> 不算答對也不算答錯。
    #
    # 一定要寫 Return(PUZZLE_CLOSED)，不能寫 Return() ——
    # Ren'Py 的 Return() 不帶參數時回傳的是 True 不是 None，
    # 那樣關閉鈕會被當成答對 (詳見 puzzle.rpy 的說明)。
    key "game_menu" action Return(PUZZLE_CLOSED)

    # 背景壓暗
    add "#000000cc"

    frame:
        align (0.5, 0.5)
        xysize (620, 780)
        padding (40, 32)
        background Frame(Solid("#1a1a1acc"), 0, 0)

        vbox:
            align (0.5, 0.5)
            spacing 20
            xfill True

            text puzzle.title:
                xalign 0.5
                color "#e67e22"
                size 38

            if puzzle.hint:
                text puzzle.hint:
                    xalign 0.5
                    text_align 0.5
                    color "#aaaaaa"
                    size 22

            # 已輸入的數字。還沒按滿的位數用 _ 補，讓玩家知道密碼有幾位。
            $ _display = entered + ("_" * (_code_len - len(entered)))

            text " ".join(_display):
                xalign 0.5
                color "#ffffff"
                size 52

            null height 4

            # 數字鍵盤 1-9 / 0
            grid 3 4:
                xalign 0.5
                spacing 12

                for _n in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
                    textbutton _n:
                        xysize (110, 80)
                        text_size 34
                        text_align 0.5
                        text_color "#e67e22"
                        text_hover_color "#ffffff"
                        # 按滿了就不能再按，避免輸入超過密碼長度
                        sensitive (not _is_full)
                        action SetScreenVariable("entered", entered + _n)

                textbutton "清除":
                    xysize (110, 80)
                    text_size 24
                    text_align 0.5
                    text_color "#888888"
                    text_hover_color "#ffffff"
                    sensitive (entered != "")
                    action SetScreenVariable("entered", "")

                textbutton "0":
                    xysize (110, 80)
                    text_size 34
                    text_align 0.5
                    text_color "#e67e22"
                    text_hover_color "#ffffff"
                    sensitive (not _is_full)
                    action SetScreenVariable("entered", entered + "0")

                # 按滿才能確認。
                #
                # 回傳值就是「對不對」—— screen 每次重畫都會重算這個判斷，
                # 所以按下去的當下拿到的是最新的 entered。
                textbutton "確認":
                    xysize (110, 80)
                    text_size 24
                    text_align 0.5
                    text_color "#2ecc71"
                    text_hover_color "#ffffff"
                    text_insensitive_color "#555555"
                    sensitive _is_full
                    action Return(PUZZLE_SOLVED if entered == puzzle.code else PUZZLE_FAILED)

    # 右上角關閉。不算失敗。
    textbutton "✕":
        align (0.97, 0.04)
        text_size 28
        text_color "#888888"
        text_hover_color "#ffffff"
        action Return(PUZZLE_CLOSED)
