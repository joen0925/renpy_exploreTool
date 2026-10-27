##################################################
# puzzles.rpy
#
#   解謎關卡目錄 (遊戲內容，不屬於 game/libs/puzzle/ 的引擎)
#
#   新增關卡的步驟：
#     1. 在下面 build_puzzles() 裡加一行 puzzles["xxx"] = 某種Puzzle(...)
#     2. 在熱點的 label 裡 call run_puzzle("xxx")
#
#   關卡「傳名稱不傳物件」——
#   label 的參數會進呼叫堆疊，而呼叫堆疊會被寫進存檔。
#   關卡是靜態定義，跟房間與物品目錄一樣不該進存檔。
##################################################

init python:

    def build_puzzles():
        puzzles = {}

        # 廚房的保險箱。
        #
        # 密碼寫在「潮濕的紙條」的描述裡 (4721) ——
        # 玩家要先用鑰匙開櫃子拿到紙條，再點物品欄看描述才知道密碼。
        # 這是刻意的示範：解謎的線索走物品欄，不是額外做一套筆記系統。
        puzzles["kitchen_safe"] = KeypadPuzzle(
            code="4721",
            title="保險箱",
            hint="門把旁邊有一個四位數的鍵盤。",

            on_success=Effect(
                set_flags=["safe_opened"],
                give_items=["documents"],
                label="kitchen_safe_opens",
            ),

            # 答錯的代價。
            #
            # 不填 on_failure 的話答錯就完全沒事，可以一直重試 ——
            # 那也是合法的寫法，看你要不要讓失敗有重量。
            #
            # 這裡故意讓它扣血，順便示範「解謎失敗也會接上死亡流程」：
            # 血扣到 0 一樣會跳 on_player_death，不用在解謎那邊另外寫。
            on_failure=Effect(
                actor="player",
                stats={"hp": -1},
                label="kitchen_safe_shock",
            ),
        )

        # playground 的舊手機：九宮格解鎖 (PatternPuzzle) 的示範。
        #
        # 圖形是一個 Z：
        #     1 → 2 → 3
        #           ↙
        #         5
        #       ↙
        #     7 → 8 → 9
        #
        # 提示就寫在 hint 裡，這個是拿來試手感的，不是正式謎題。
        puzzles["playground_phone"] = PatternPuzzle(
            pattern="1235789",
            title="舊手機",
            hint="螢幕上的指紋油漬，看起來像一個 Z。",

            on_success=Effect(
                set_flags=["playground_phone_unlocked"],
                label="playground_phone_unlocked",
            ),

            # 畫錯只講一句話、沒有代價，可以一直重試。
            # Effect 只帶 label、沒有 stats 的時候不用寫 actor。
            # 保險箱 (kitchen_safe) 示範的是另一種 —— 答錯會扣血。
            on_failure=Effect(label="playground_phone_wrong"),
        )

        # playground 的鎖櫃：pausable=False 的示範。
        #
        # 上面兩個關卡都是預設的 pausable=True —— 世界會停下來等玩家，
        # 想解多久都沒關係。這一個相反：解的時候鬼照樣逼近，
        # 而且標了 interrupt=True 的計時事件到點時會把視窗直接關掉。
        #
        # 怎麼試：進實驗區之後**先去點鎖櫃**，然後什麼都不要按。
        # 10 秒時會有腳步聲（那個事件沒標 interrupt，所以乖乖排隊，
        # 視窗不會動），20 秒時鬼會到 —— 視窗當場關掉。
        #
        # 被關掉**不算答錯**（run_puzzle 收到 PUZZLE_INTERRUPTED 時
        # 不套用任何 Effect），所以不會扣血。代價由那個計時事件自己收。
        puzzles["playground_locker"] = KeypadPuzzle(
            code="1958",
            title="鎖櫃",
            hint="四位數。鎖環上有人用指甲刻了「別在這裡待太久」。",

            pausable=False,

            on_success=Effect(
                set_flags=["playground_locker_opened"],
                label="playground_locker_opens",
            ),

            # 答錯只講一句話、不扣血 —— 這個關卡的壓力來自時間，
            # 不是來自答錯的代價。兩種壓力都加在同一個關卡上會太兇。
            on_failure=Effect(label="playground_locker_wrong"),
        )

        return puzzles


# 用 define 而不是 default —— 跟 item_catalog 同一個理由。
# 關卡是靜態定義，不該進存檔；改了密碼或獎勵，舊存檔也要馬上吃到新的。
define puzzle_catalog = build_puzzles()
