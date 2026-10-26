##################################################
# state_image.rpy
#
#   「會跟著遊戲狀態換圖」的背景。
#
#   用在近景視窗最明顯 —— 抽屜裡的紙條被拿走之後，底圖要從
#   「有紙條的抽屜」變成「空抽屜」。但普通房間一樣能用
#   (走廊的燈打開之後換成亮的背景圖)。
#
#   用法：
#       Room(
#           name="drawer_inside",
#           background=state_image(
#               (Condition(require=["wet_note"]), "images/drawer_empty.png"),
#               default="images/drawer_note.png",
#           ),
#           ...
#       )
#
#   條件由上往下試，**第一個成立的就贏**，全都不成立才用 default。
#   所以要把「比較特殊的情況」寫在前面。
#
#   ---
#
#   為什麼不是在 Room 上新增一個 backgrounds 欄位
#
#   因為 Ren'Py 已經有 DynamicDisplayable 這個東西了 ——
#   它接一個函式，每次重畫時問那個函式「現在該顯示什麼」。
#   我們要做的只是把它跟專案既有的 Condition 接起來，
#   而不是在 Room 上再長一套平行的顯示規則
#   (那樣 explore 畫面、近景視窗、F9 標點面板都得各自知道怎麼挑圖)。
#
#   這樣寫的附帶好處：
#
#   1. **跟熱點的顯示條件是同一套東西。** 抽屜的底圖與紙條熱點
#      會寫成同一個條件的兩面，不會各自記一份狀態 ——
#      所以不可能出現「空抽屜裡還有一張點得到的紙條」。
#
#   2. **不會進存檔。** 這個物件掛在 Room.background 上，而
#      Room.__reduce__ 存檔時只存房間名稱 (見 room.rpy)，
#      所以它連被 pickle 的機會都沒有。
#      圖換了、條件改了，舊存檔一律馬上吃到新的。
#
#   3. **冪等。** 它是每次重畫時「問」出來的，不是某個時間點
#      「設定」進去的。所以讀任何存檔、倒帶幾次，圖都不會對不上狀態。
##################################################

init python:

    def pick_state_image(cases, default, view=None):
        """
        依目前狀態挑出該顯示的圖。回傳圖片 (或任何 displayable)。

        cases    [(Condition, 圖), ...]，由上往下試，第一個成立的就回傳
        default  全都不成立時回傳這個
        view     StateView。不給就用目前的遊戲狀態

        純函式，不改任何狀態 —— 所以可以直接餵假的 StateView
        測「什麼狀態下該顯示哪張圖」，完全不用啟動畫面。

        **唯讀是硬性要求**，不是禮貌：這個函式會在畫面重畫時被呼叫，
        跟 hotspot_is_shown() 一樣 (理由見 condition.rpy 的開頭)。
        Condition 只拿得到 StateView，結構上就改不到任何狀態。
        """
        if view is None:
            # game_state 是 default 變數，正常情況一定在。
            # 但 Ren'Py 的圖片預載 (predict) 可能在它存在之前就問過來，
            # 那時候回答 default 比直接當掉好。
            state = getattr(store, "game_state", None)

            if state is None:
                return default

            view = state.view()

        for condition, image in cases:
            if condition.test(view):
                return image

        return default


    def _state_image_render(st, at, cases, default):
        """
        DynamicDisplayable 的回呼。它會用 (st, at, *args) 的形式呼叫這裡。

        第二個回傳值是「幾秒後自動再問一次」，這裡給 None = 不自動輪詢。
        不需要輪詢的理由：事件跑完一定會重新整理畫面
        (run_event_labels 不是切畫面就是呼叫 renpy.restart_interaction())，
        而 DynamicDisplayable 每個互動開始時都會重新問一次。
        所以狀態一改，下一個互動就會看到新圖。
        """
        return (renpy.displayable(pick_state_image(cases, default)), None)


    def state_image(*cases, **kwargs):
        """
        建立一個會跟著狀態換圖的背景。見本檔開頭的用法。

        每個 case 是 (Condition, 圖) 的 tuple，default 是必填的 keyword。

        寫錯的話在 build_rooms() 當下就會爆掉 ——
        也就是遊戲一啟動就看得到，不用等玩家真的走到那個房間。
        這跟 Event 的 chance / delay 驗證是同一個理由：
        這類錯誤的症狀是「圖就是沒換」，靠試玩很難確定是哪裡的問題。
        """
        default = kwargs.pop("default", None)

        if kwargs:
            raise TypeError(
                f"state_image() 不認得這些參數：{sorted(kwargs)}。\n"
                f"條件請用 (Condition(...), \"圖\") 的 tuple 一個個傳進來，"
                f"最後再加 default=\"圖\"。"
            )

        if default is None:
            raise ValueError(
                "state_image() 一定要填 default=\"圖\"。\n"
                "那是所有條件都不成立時要顯示的圖 —— 沒有它的話，"
                "某些狀態下會變成完全沒有背景 (全黑)，而且很難查。"
            )

        if not cases:
            raise ValueError(
                "state_image() 至少要有一組 (Condition(...), \"圖\")。\n"
                "只有一張圖的話直接寫 background=\"圖\" 就好，不需要這個。"
            )

        checked = []

        for case in cases:
            # 常見手滑：把 tuple 的括號漏掉，變成一堆散的參數
            if not isinstance(case, (tuple, list)) or len(case) != 2:
                raise ValueError(
                    f"state_image() 的每一組要寫成 (Condition(...), \"圖\")，收到 {case!r}。\n"
                    f"是不是漏了括號？"
                )

            condition, image = case

            # 鴨子型別：只要有 test() 就收。這樣測試能餵假的條件物件進來，
            # 不用去建真的 Condition。
            if condition is None or not hasattr(condition, "test"):
                raise ValueError(
                    f"state_image() 每一組的第一個要是 Condition，收到 {condition!r}。\n"
                    f"想要「一定成立」的那一張請用 default=。"
                )

            checked.append((condition, image))

        return DynamicDisplayable(_state_image_render, checked, default)
