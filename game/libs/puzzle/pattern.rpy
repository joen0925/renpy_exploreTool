##################################################
# pattern.rpy
#
#   九宮格解鎖 (像手機的圖形鎖)。第二個 Puzzle 類型。
#
#   用法 (在內容層的 build_puzzles() 裡)：
#
#       puzzles["old_phone"] = PatternPuzzle(
#           pattern="1235789",          # 點的編號，也可以寫 [1, 2, 3, 5, 7, 8, 9]
#           title="舊手機",
#           hint="螢幕上有一道一道的指紋油漬。",
#           on_success=Effect(set_flags=["phone_unlocked"], label="phone_unlocked"),
#           on_failure=None,            # 畫錯沒代價
#       )
#
#   點的編號跟手機一樣，由左到右、由上到下：
#
#       1   2   3
#       4   5   6
#       7   8   9
#
#   規則 (照 Android)：
#     1. 按住一個點開始拖，放開就送出
#     2. 同一個點不能用兩次
#     3. 直線跨過的點會自動算進去 —— 從 1 拖到 3，中間的 2 一定會被連到
#     4. 少於 min_length 個點就放開，當成「手滑」，不算一次嘗試
#        (視窗不關、不套用 on_failure，只顯示提示)
#
#   第 3 條的後果是：有些圖形「畫不出來」，例如 [1, 3]。
#   PatternPuzzle 建立時會把圖形重播一次檢查，畫不出來就直接報錯 ——
#   Puzzle 是在 build_puzzles() 裡建立的，所以遊戲一啟動就會發現，
#   不會等到玩家怎麼畫都解不開才知道。
##################################################

init python:

    import pygame

    # 連線區的大小 (正方形的邊長，像素)。九個點平均分布在裡面。
    PATTERN_PAD_SIZE = 480

    # 連線區底下留給「至少要連 N 個點」提示文字的高度
    PATTERN_PAD_MESSAGE_HEIGHT = 60

    # 點的外觀
    PATTERN_DOT_RADIUS = 18
    PATTERN_DOT_COLOR = (170, 170, 170, 255)
    PATTERN_DOT_ACTIVE_COLOR = (230, 126, 34, 255)
    PATTERN_LINE_COLOR = (230, 126, 34, 200)
    PATTERN_LINE_WIDTH = 8

    # 判定範圍比畫出來的點大，手指 (滑鼠) 不用剛好點在圓心上。
    # 用間距的比例表示，不要大到跟隔壁的點重疊 (0.5 就碰到了)。
    PATTERN_HIT_RATIO = 0.28


    def pattern_pad_pos():
        """
        連線區在螢幕上的左上角座標。

        刻意用固定位置而不是跟著外框排版，理由是測試要能算出
        每個點在螢幕上的位置去模擬拖曳 (見 pattern_dot_screen_pos)。
        在執行期才算，不在 init 時算 —— 那時 config.screen_width 不一定設好了。
        """
        return ((config.screen_width - PATTERN_PAD_SIZE) // 2, 300)


    def pattern_dot_center(dot, size=PATTERN_PAD_SIZE):
        """編號 1-9 的點，在連線區裡的中心座標 (x, y)。"""
        row, col = divmod(dot - 1, 3)
        spacing = size / 3.0
        return (spacing * (col + 0.5), spacing * (row + 0.5))


    def pattern_dot_screen_pos(dot):
        """編號 1-9 的點，在螢幕上的座標。給測試模擬拖曳用。"""
        pad_x, pad_y = pattern_pad_pos()
        cx, cy = pattern_dot_center(dot)
        return (int(pad_x + cx), int(pad_y + cy))


    def pattern_dot_at(x, y, size=PATTERN_PAD_SIZE):
        """
        連線區裡的座標 (x, y) 碰到哪個點，回傳編號 1-9；都沒碰到回傳 None。
        """
        radius = (size / 3.0) * PATTERN_HIT_RATIO

        for dot in range(1, 10):
            cx, cy = pattern_dot_center(dot, size)
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                return dot

        return None


    def pattern_extend(path, dot):
        """
        把一個點接到目前的連線上，回傳「新的」連線 (不改傳進來的 list)。

        規則：
          - 已經連過的點不能再用 -> 原樣回傳
          - 從上一個點直線跨過一個還沒連的點時，那個點會先被自動接上
            (1 -> 3 會變成 1, 2, 3；1 -> 9 會變成 1, 5, 9)

        純函式，方便直接測規則，不用真的去拖滑鼠。
        """
        if dot in path:
            return list(path)

        new_path = list(path)

        if new_path:
            last = new_path[-1]
            last_row, last_col = divmod(last - 1, 3)
            row, col = divmod(dot - 1, 3)

            # 兩點的列、行差都是偶數，中間才剛好有一個格點
            if (last_row + row) % 2 == 0 and (last_col + col) % 2 == 0:
                middle = ((last_row + row) // 2) * 3 + (last_col + col) // 2 + 1

                if middle not in (last, dot) and middle not in new_path:
                    new_path.append(middle)

        new_path.append(dot)
        return new_path


    def pattern_normalize(pattern):
        """把 "1235" 或 [1, 2, 3, 5] 都統一成 [1, 2, 3, 5]。"""
        if isinstance(pattern, str):
            return [int(c) for c in pattern]
        return [int(d) for d in pattern]


    class PatternPuzzle:
        """
        九宮格解鎖。不繼承任何東西 —— run_puzzle 只要求
        screen / on_success / on_failure / pausable 這四個屬性 (鴨子型別)。
        """

        def __init__(
            self,
            pattern,            # 正確的圖形，"1235789" 或 [1, 2, 3, 5, 7, 8, 9]
            on_success,         # 答對時套用的 Effect
            on_failure=None,    # 答錯時套用的 Effect，None = 畫錯沒代價

            title="圖形鎖",
            hint=None,

            # 少於幾個點就放開算「手滑」。預設 4，跟 Android 一樣。
            min_length=4,

            # 解謎途中世界要不要暫停。目前還沒有實際效果，理由同 KeypadPuzzle。
            pausable=True,
        ):
            # run_puzzle 要找的四個屬性
            self.screen = "pattern_puzzle"
            self.on_success = on_success
            self.on_failure = on_failure
            self.pausable = pausable

            # 圖形鎖自己的設定
            self.pattern = pattern_normalize(pattern)
            self.min_length = min_length
            self.title = title
            self.hint = hint

            self._validate()

        def _validate(self):
            """
            圖形畫不畫得出來。畫不出來就直接爆掉。

            Puzzle 在 build_puzzles() 裡建立，所以這個錯誤會在遊戲啟動時就跳出來。
            """
            for dot in self.pattern:
                if not 1 <= dot <= 9:
                    raise ValueError(f"圖形鎖的點編號只能是 1-9，但圖形 {self.pattern} 裡有 {dot}。")

            if len(set(self.pattern)) != len(self.pattern):
                raise ValueError(f"圖形鎖 {self.pattern} 裡有重複的點。同一個點不能用兩次。")

            if len(self.pattern) < self.min_length:
                raise ValueError(
                    f"圖形鎖 {self.pattern} 只有 {len(self.pattern)} 個點，"
                    f"但 min_length={self.min_length}。玩家畫出來會被當成手滑，永遠解不開。"
                )

            # 照規則重播一次：直線跨過的點會被自動接上，
            # 所以像 [1, 3] 這種圖形實際畫出來一定是 [1, 2, 3]。
            replay = []
            for dot in self.pattern:
                replay = pattern_extend(replay, dot)

            if replay != self.pattern:
                raise ValueError(
                    f"圖形鎖 {self.pattern} 畫不出來 —— 照著畫實際會變成 {replay}。\n"
                    f"直線跨過的點會被自動連進去 (例如從 1 拖到 3，中間的 2 一定會被連到)。"
                )

        def __repr__(self):
            return f"<PatternPuzzle {self.title} ({len(self.pattern)} 點)>"


    class PatternPad(renpy.Displayable):
        """
        實際讓玩家拖曳連線的那一塊。

        「連到一半的路徑」存在這個物件上，不在 store 裡 ——
        那是臨時狀態，不是遊戲進度。它由 screen 的 default 建立，
        視窗關掉就跟著消失。
        """

        def __init__(self, pattern, min_length, **kwargs):
            super(PatternPad, self).__init__(**kwargs)

            self.pattern = list(pattern)
            self.min_length = min_length

            self.path = []          # 目前連到的點
            self.dragging = False
            self.cursor = None      # 拖曳中的滑鼠位置 (畫「跟著手指的那一段線」用)
            self.too_short = False  # 上一次是不是因為點太少被忽略

        def render(self, width, height, st, at):
            rv = renpy.Render(PATTERN_PAD_SIZE, PATTERN_PAD_SIZE + PATTERN_PAD_MESSAGE_HEIGHT)
            canvas = rv.canvas()

            # --- 連線 ---
            points = [pattern_dot_center(d) for d in self.path]

            # 拖曳中的話，最後一段線跟著滑鼠走
            if self.dragging and points and self.cursor is not None:
                points = points + [self.cursor]

            for i in range(len(points) - 1):
                start = (int(points[i][0]), int(points[i][1]))
                end = (int(points[i + 1][0]), int(points[i + 1][1]))
                canvas.line(PATTERN_LINE_COLOR, start, end, PATTERN_LINE_WIDTH)

            # --- 九個點 (畫在線的上面) ---
            for dot in range(1, 10):
                cx, cy = pattern_dot_center(dot)
                color = PATTERN_DOT_ACTIVE_COLOR if dot in self.path else PATTERN_DOT_COLOR
                canvas.circle(color, (int(cx), int(cy)), PATTERN_DOT_RADIUS)

            # --- 手滑提示 ---
            if self.too_short:
                message = renpy.render(
                    Text("至少要連 %d 個點" % self.min_length, size=24, color="#e67e22"),
                    PATTERN_PAD_SIZE, PATTERN_PAD_MESSAGE_HEIGHT, st, at,
                )
                mw, _ = message.get_size()
                rv.blit(message, (int((PATTERN_PAD_SIZE - mw) / 2), PATTERN_PAD_SIZE + 12))

            return rv

        def event(self, ev, x, y, st):
            """
            處理拖曳。放開時回傳結果 —— displayable 的 event() 回傳非 None
            就會結束這次互動，那個值就是 call screen 的回傳值。

            回傳值一律用 PUZZLE_SOLVED / PUZZLE_FAILED，理由見 puzzle.rpy。
            """
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                dot = pattern_dot_at(x, y)

                # 跟手機一樣，一定要從某個點上開始拖
                if dot is not None:
                    self.dragging = True
                    self.too_short = False
                    self.path = [dot]
                    self.cursor = (x, y)
                    renpy.redraw(self, 0)

            elif ev.type == pygame.MOUSEMOTION and self.dragging:
                self.cursor = (x, y)

                dot = pattern_dot_at(x, y)
                if dot is not None:
                    self.path = pattern_extend(self.path, dot)

                renpy.redraw(self, 0)

            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and self.dragging:
                path = self.path

                self.dragging = False
                self.cursor = None
                self.path = []
                renpy.redraw(self, 0)

                # 點太少 = 手滑。不結束互動、不算失敗，只顯示提示。
                if len(path) < self.min_length:
                    self.too_short = True
                    return None

                return PUZZLE_SOLVED if path == self.pattern else PUZZLE_FAILED

            return None


screen pattern_puzzle(puzzle):

    # 跟 keypad_puzzle 同一套：modal 擋掉底下的點擊，不用先收起探索畫面。
    modal True

    zorder 200

    # 連線區。用 default 建立，整個視窗開著的期間都是同一個物件，
    # 連到一半的路徑才不會因為畫面重畫而消失。
    default pad = PatternPad(puzzle.pattern, puzzle.min_length)

    # ESC / 右鍵關掉 -> 不算答對也不算答錯。
    # 一定要寫 Return(PUZZLE_CLOSED)，不能寫 Return() (詳見 puzzle.rpy)。
    key "game_menu" action Return(PUZZLE_CLOSED)

    add "#000000cc"

    frame:
        align (0.5, 0.5)
        xysize (620, 860)
        padding (40, 32)
        background Frame(Solid("#1a1a1acc"), 0, 0)

        vbox:
            xalign 0.5
            spacing 16
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

    # 連線區放在固定位置 (不在 frame 裡排版)，測試才算得出每個點的螢幕座標
    add pad:
        pos pattern_pad_pos()

    textbutton "✕":
        align (0.97, 0.04)
        text_size 28
        text_color "#888888"
        text_hover_color "#ffffff"
        action Return(PUZZLE_CLOSED)
