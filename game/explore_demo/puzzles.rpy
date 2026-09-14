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

        return puzzles


# 用 define 而不是 default —— 跟 item_catalog 同一個理由。
# 關卡是靜態定義，不該進存檔；改了密碼或獎勵，舊存檔也要馬上吃到新的。
define puzzle_catalog = build_puzzles()
