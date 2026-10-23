##################################################
# world.rpy
#
#   世界時鐘。「遊戲裡過了多少時間」這件事的唯一來源。
#
#   為什麼需要它：以前推動世界的 timer 長在 screen explore() 裡，
#   畫面一被收起來 (對話、解謎視窗、翻頁視窗) 時鐘就停了。
#   「解謎的時候鬼要繼續逼近」這種事在那個架構下做不出來。
#
#   所以時鐘改成純邏輯：
#
#     world.tick(dt)   唯一推進時間的入口，不碰畫面、不跳轉
#     world.paused     要不要暫停，集中在這一個地方表達
#
#   畫面只負責「每隔一段時間呼叫 tick 一次」，誰呼叫都可以。
#   測試要推進 10 秒就直接 world.tick(10.0)，不用真的等。
#
#   ---
#
#   暫停規則 (搬出畫面之後時鐘預設一直跑，要暫停就得明確講)：
#
#     對話 (run_event_labels)   暫停
#     翻頁視窗 (show_pages)     暫停
#     系統選單                  暫停 —— 不用寫程式，見下面 world_clock 的說明
#     解謎視窗                  繼續走 (玩家解謎時鬼照樣逼近)
#
#   ---
#
#   時間存在哪裡：全部都在 world 自己身上。
#
#   存檔會存 (world 是 default 變數，Ren'Py 會把它存進存檔)，
#   但「倒帶不會動它」—— 這是刻意的，跟 Camera 同一個待遇。
#
#   為什麼不放進 GameState：
#   GameState 是刻意被倒帶追蹤的 (物品、旗標本來就該隨倒帶還原)。
#   把每秒改 20 次的秒數放進去，倒帶系統會在檢查點把它還原回快照，
#   timer 累加的時間會被反覆抹掉 —— 症狀是讀檔後時鐘看起來凍住不動。
#   (這個 bug 真的發生過，2026-10-12 手動測試抓到的)
##################################################

init python:

    import time

    # 一次 tick 最多承認多少秒。
    #
    # 為什麼要夾上限：dt 是算真實經過的時間，遊戲視窗失焦、
    # 讀圖卡頓、或玩家把視窗拖著不放，兩次 tick 之間可能隔了好幾秒。
    # 不夾的話回到遊戲的瞬間鬼會往前跳一大步、直接抓到人，
    # 玩家完全不知道發生什麼事。
    #
    # 夾上限的代價是「卡頓期間的時間會被吃掉」—— 這是刻意選的方向：
    # 寧願鬼慢一點，也不要憑空瞬殺。
    WORLD_MAX_DT = 0.1

    # 時鐘的驅動頻率 (秒)。倒數計時用 20fps 綽綽有餘 ——
    # 這個 timer 跟鏡頭的 60fps 無關，鏡頭那個還留在 explore() 裡。
    WORLD_TICK_INTERVAL = 0.05


    class WorldClock(NoRollback):
        """
        世界時鐘。

        繼承 NoRollback 的理由跟 Camera 一樣：這上面放的是
        「現在暫停了嗎」這類每秒會變好幾次、沒有劇情意義的暫時狀態。
        玩家滾滑鼠滾輪倒帶時不該把它們一起還原
        (真正該被倒帶的累積秒數在 game_state.world 裡)。
        """

        def __init__(self):
            # 世界時鐘累積走過的秒數，從遊戲開始算起，暫停期間不累加。
            #
            # 存秒數而不是幀數：幀數會隨驅動頻率改變
            # (現在 20fps，以後改 30fps 的話舊存檔就錯了)，秒數不會。
            self.elapsed = 0.0

            # 進目前這個房間的那一刻，elapsed 是多少。
            #
            # TIMER 事件的倒數是從進房間開始算的，所以「現在在這個房間待了多久」
            # 就是 elapsed - room_entered_at。
            #
            # 換房間時重設這個值 —— 這一個動作同時實現了兩件事：
            # 「倒數從進房間開始算」與「換房間重置倒數」。
            # (使用者 2026-10-20 的決定：換房間本來就是躲鬼的手段。
            #  代價是來回走可以躲掉鬼，但躲的時候什麼進度都做不了，會自己收斂)
            #
            # 讀檔不用特別處理：這個值跟 elapsed 都在存檔裡，兩個是同一個基準。
            self.room_entered_at = 0.0

            # 正在暫停的理由 (字串)。
            #
            # 用 set 而不是 bool，因為暫停會疊：翻頁視窗開著的時候
            # 又跑了一段對話，對話結束時如果直接設成「不暫停」，
            # 視窗還開著時鐘就偷跑了。
            # 要所有理由都解除才會真的繼續走。
            self.pause_reasons = set()

            # 「時間到了，該中斷玩家手上的事」的旗標。
            #
            # 這裡只負責舉旗，不負責關任何視窗 ——
            # 解謎畫面自己每格檢查這面旗子，看到就走
            # 玩家按 ✕ 的同一條關窗路徑 (Return(PUZZLE_CLOSED))。
            # 從外面硬砍視窗的話，拖曳到一半的狀態、倒帶都要另外收拾。
            self.interrupt = False

            # 上一次 tick 的真實時間 (time.time())，None 代表還沒跑過。
            # 存這個是為了算 dt；它不是遊戲進度。
            self.last_real_time = None

            # suspend_pauses() 暫存起來的暫停理由。
            # 用堆疊而不是單一個欄位，這樣嵌套也不會互相蓋掉
            # (解謎裡面又開解謎的話，內層還原之後外層的那一份還在)。
            self.pause_stack = []

        # --- 暫停 ---

        def pause(self, reason):
            """
            以某個理由暫停時鐘。同一個理由重複呼叫沒有副作用。

            理由要成對解除，所以請用 resume() 配同一個字串。
            """
            self.pause_reasons.add(reason)

        def resume(self, reason):
            """
            解除某個暫停理由。還有別的理由在就繼續暫停。

            沒有這個理由時什麼都不做 (不丟例外) ——
            對話被 jump 打斷、沒跑到 resume 的情況難以完全避免，
            那時下一次 resume 不該連帶爆掉。
            """
            self.pause_reasons.discard(reason)

        def resume_all(self):
            """
            清掉所有暫停理由。讀檔之後用 (見檔案最下面)。
            """
            self.pause_reasons.clear()
            self.pause_stack = []

        def suspend_pauses(self):
            """
            暫時解除目前所有的暫停理由，讓這段期間世界照樣在走。
            一定要配一次 restore_pauses()。

            為什麼需要這個：解謎視窗是從熱點的 label 叫出來的，
            而那些 label 是 run_event_labels 執行的 —— 那裡為了對話
            已經把時鐘暫停了。解謎要「鬼繼續逼近」就得在這段期間
            把外面那層暫停先讓開，結束再放回去。

            不是直接 resume("dialogue") 了事，因為解謎不該知道
            外面是為了什麼而暫停的 —— 它只知道「我這段要讓世界跑」。
            """
            self.pause_stack.append(set(self.pause_reasons))
            self.pause_reasons.clear()

        def restore_pauses(self):
            """
            還原最近一次 suspend_pauses() 當時的暫停理由。

            沒有對應的 suspend 時什麼都不做 (不丟例外) ——
            跟 resume() 一樣，流程被 jump 打斷時不該連帶爆掉。
            """
            if self.pause_stack:
                self.pause_reasons = self.pause_stack.pop()

        @property
        def paused(self):
            """現在是不是暫停中。"""
            return bool(self.pause_reasons)

        # --- 推進時間 ---

        def tick(self, dt):
            """
            把世界往前推 dt 秒，回傳實際推進了多少秒 (暫停時回傳 0.0)。

            唯一推進時間的入口。純邏輯 —— 不碰畫面、不跳轉、不 call label。
            測試可以直接呼叫這個推進，不用真的等秒數過去。
            """
            if self.paused:
                return 0.0

            # 負的 dt 一律當成 0 —— 時間不倒流。
            # (系統時間被調整、或驅動端算錯都可能生出負值)
            dt = min(max(0.0, dt), WORLD_MAX_DT)

            if dt <= 0.0:
                return 0.0

            self.elapsed += dt

            return dt

        def reset_elapsed(self):
            """把時鐘歸零。開新遊戲或章節換場用。"""
            self.elapsed = 0.0
            self.room_entered_at = 0.0

        # --- 房間內的計時 ---

        @property
        def time_in_room(self):
            """在目前這個房間待了多少秒。TIMER 事件的倒數就是看這個。"""
            return self.elapsed - self.room_entered_at

        def mark_room_entered(self):
            """
            重設房間內的計時。change_room() 進到新房間時呼叫。

            刻意不叫 reset_timers() 之類的名字 —— 它記錄的是「進房間的時刻」，
            重置只是這件事的結果。
            """
            self.room_entered_at = self.elapsed

        def tick_real_time(self):
            """
            用「距離上次呼叫過了多久」當作 dt 推進時鐘。
            常駐畫面的 timer 呼叫這個，遊戲邏輯請呼叫 tick()。

            暫停期間照樣要更新 last_real_time，不然暫停 30 秒之後
            第一次 tick 會拿到 30 秒的 dt (雖然會被 WORLD_MAX_DT 夾掉，
            但那是在補破網，不是本來就對)。
            """
            now = time.time()
            previous = self.last_real_time
            self.last_real_time = now

            # 第一次呼叫沒有基準點可以比，這一格只記時間不推進。
            if previous is None:
                return 0.0

            return self.tick(now - previous)

        def __repr__(self):
            return (
                f"<WorldClock elapsed={self.elapsed:.1f}s "
                f"paused={sorted(self.pause_reasons)} interrupt={self.interrupt}>"
            )


    def world_clock_tick():
        """
        給常駐畫面的 timer 呼叫。**刻意不回傳任何東西。**

        ⚠️ 不要把 timer 的 action 直接接到 tick_real_time 上。

        Ren'Py 的畫面動作只要回傳非 None 的值，就等於
        「結束當前互動，並把這個值當成互動的結果回傳出去」。
        而 tick_real_time 會回傳推進的秒數 (一個 float) ——
        接上去的話這個時鐘每 0.05 秒就會把玩家正在進行的互動硬生生結束掉一次，
        症狀是翻頁視窗/解謎視窗一打開就自己關掉 (call screen 立刻返回)。

        這跟 puzzle.rpy 裡「Return() 不帶參數會回傳 True」是同一類地雷，
        explore_debug 的 timer 用 NullAction() 也是同一個理由。
        """
        world.tick_real_time()


    # 讀檔之後把暫停理由清掉。
    #
    # 為什麼需要：pause_reasons 雖然不進倒帶 (NoRollback)，但 world 是
    # default 變數，所以「存檔當下在暫停中」這件事會被存進存檔。
    # 玩家在對話中途存檔、讀回來之後，暫停理由還在，時鐘就永遠不會動了。
    #
    # 用 config.after_load_callbacks 而不是再寫一個 label after_load ——
    # game_state.rpy 已經有一個了，同名 label 會直接撞車。
    def world_clock_after_load():
        store.world.resume_all()
        store.world.interrupt = False

        # 讀檔那一瞬間到上次存檔之間隔了多久都無所謂，
        # 不清掉的話第一格會拿到一個很大的 dt。
        store.world.last_real_time = None

    config.after_load_callbacks.append(world_clock_after_load)


# 全域唯一的世界時鐘。
default world = WorldClock()


# 時鐘的動力來源：一個沒有任何視覺的常駐畫面。
#
# 為什麼掛 overlay 而不是放回 explore()：
#   - explore 被收起來時 (對話、事件) overlay 還在，時鐘不會跟著停
#   - 解謎視窗是 modal，modal 擋的是點擊，不會讓 overlay 的 timer 停下來
#     -> 這正是「解謎時鬼繼續逼近」要的效果
#   - 系統選單是另一個 context，overlay 畫面不會在那裡跑
#     -> 系統選單自動暫停，不用寫任何程式碼
#
# (用 if 擋一下，避免開發時重新載入腳本重複加入同一個名字，
#  跟 explore_debug_keys 同一個寫法)
init python:
    if "world_clock" not in config.overlay_screens:
        config.overlay_screens.append("world_clock")


screen world_clock():
    # action 一定要接 world_clock_tick (不回傳值的那一層)，
    # 不能直接接 world.tick_real_time —— 理由見那個函式的註解。
    timer WORLD_TICK_INTERVAL repeat True action Function(world_clock_tick)
