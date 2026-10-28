##################################################
# event.rpy
#
#   事件本體，以及派發時傳進去的執行環境。
#
#   一個 Event 就是一句「在什麼時機、滿足什麼條件、就做什麼事」。
#
#     Event(
#         id="hall.door_open",
#         condition=Condition(require=["key"]),
#         effect=Effect(set_flags=["door_opened"], label="open_the_door"),
#         sequence=10,
#         limit=1,
#         stop=True,
#     )
#
#   Event 是靜態定義，跟 Room / Hotspot 一樣由 build_rooms() 產生，
#   所以「觸發過幾次」「死了沒」不存在這裡，存在 GameState.events。
##################################################

init python:

    class Event:
        def __init__(
            self,
            id,               # 全域唯一字串。慣例用 "房間名.事件名"，例如 "hall.ghost_warn" 一定要唯一：EventState 用它當 key，撞名會讓兩個事件共用狀態

            condition=None,   # Condition。None = 無條件，一定通過
            effect=None,      # Effect。None = 什麼都不做 (只用來記錄「來過了」時有意義)

            sequence=0,       # 同一個掛載點內的執行順序，小的先跑。每個房間各自獨立計算
            limit=1,          # 最多觸發幾次，用完自動死亡。None = 無限次
            stop=False,       # 這個 Event 觸發之後，就不再檢查後面的

            # 觸發機率，0.0 ~ 1.0。None = 100%，條件通過就一定觸發。
            #
            # 骰輸了「不算觸發過」—— 次數不會 +1，limit 也不會被消耗，
            # 跟條件不符是同一個待遇。不然 limit=1 的機率事件
            # 第一次骰輸就死亡，玩家永遠遇不到它。
            #
            # 骰點刻意不寫在 can_fire() 裡，在 collect_events()。理由見 can_fire。
            chance=None,

            # 觸發時機。None 代表「由掛載的位置決定」——
            # 掛在 Room.events 就是 ENTER_ROOM，掛在 Hotspot.events 就是 CLICK_HOTSPOT。
            # 之後 EXIT_ROOM 接上時，同一個 list 裡混兩種時機也能正確派發。
            trigger=None,

            # 進房間幾秒後觸發，單位是秒。只有 trigger=TriggerType.TIMER 能填。
            #
            # 從「進這個房間的那一刻」開始算，換房間會重新計時
            # (使用者 2026-10-20 的決定：換房間本來就是躲鬼的手段)。
            delay=None,

            # 到點時可不可以「打斷玩家手上的事」。只有 TIMER 事件能填。
            #
            # 預設 False = 乖乖排隊。玩家正在解謎或翻抽屜的時候，
            # 到點的事件會等他自己關掉視窗才發生 —— 這是原本的行為。
            #
            # True = 立刻把視窗關掉，讓事件馬上出場。
            # 這是給「鬼抓到人」用的：不打斷的話玩家躲在解謎視窗裡
            # 就永遠安全，pausable=False 等於沒有意義。
            #
            # 為什麼要設計者明確標記、而不是所有計時事件都打斷：
            # 氣氛用的台詞 (遠處的腳步聲) 不該把玩家從密碼鎖裡拽出來，
            # 還害他按到一半的號碼全沒了。「被打斷」要稀有才有意義。
            #
            # ⚠️ 不要跟 chance 一起用。中斷的判定是只讀的，不會骰骰子；
            # 所以骰輸的話視窗已經關了、事件卻沒發生 —— 玩家會覺得
            # 視窗莫名其妙自己關掉。要機率性的鬼，請讓它排隊 (不要標 interrupt)。
            interrupt=False,
        ):
            self.id = id
            self.condition = condition
            self.effect = effect
            self.sequence = sequence
            self.limit = limit
            self.stop = stop
            self.trigger = trigger
            self.chance = self._validate_chance(chance)
            self.delay = self._validate_delay(delay, trigger, limit)
            self.interrupt = self._validate_interrupt(interrupt, trigger)

        @staticmethod
        def _validate_chance(chance):
            """
            機率必須是 0.0 ~ 1.0 的數字，或 None (= 一定觸發)。

            寧可在建立房間時就爆掉，也不要讓一個永遠不觸發 (或永遠觸發)
            的事件安靜地混在遊戲裡 —— 機率事件本來就偶爾才發生，
            靠試玩幾乎抓不到。
            """
            if chance is None:
                return None

            # bool 是 int 的子類別，chance=True 幾乎一定是手滑
            if isinstance(chance, bool) or not isinstance(chance, (int, float)):
                raise ValueError(
                    f"Event 的 chance 要填 0.0 ~ 1.0 的數字，收到 {chance!r}。"
                )

            if not (0.0 <= chance <= 1.0):
                raise ValueError(
                    f"Event 的 chance 要在 0.0 ~ 1.0 之間，收到 {chance!r}。\n"
                    f"這是機率不是百分比 —— 25% 要寫 0.25，不是 25。"
                )

            return chance

        @staticmethod
        def _validate_delay(delay, trigger, limit=1):
            """
            delay 與 trigger=TIMER 必須成對出現，而且要是正數。

            兩種手滑都在建立房間時就爆掉，理由跟 chance 一樣 ——
            這兩種錯誤的症狀都是「那個事件永遠不會發生」，
            而「什麼都沒發生」靠試玩幾乎不可能發現。

            特別容易踩的是只填 delay 忘了寫 trigger：掛在 Room.events
            上的事件預設時機是 ENTER_ROOM，所以它會變成一個
            「一進房間就觸發」的事件 —— 看起來有在動，但時間完全沒生效。
            """
            is_timer = (trigger == TriggerType.TIMER)

            if delay is None:
                if is_timer:
                    raise ValueError(
                        "trigger=TriggerType.TIMER 的 Event 一定要填 delay，"
                        "不然不知道幾秒後要觸發。"
                    )
                return None

            if not is_timer:
                raise ValueError(
                    f"只有 trigger=TriggerType.TIMER 的 Event 能填 delay，收到 delay={delay!r}。\n"
                    f"是不是忘了寫 trigger=TriggerType.TIMER？"
                )

            # bool 是 int 的子類別，delay=True 幾乎一定是手滑
            if isinstance(delay, bool) or not isinstance(delay, (int, float)):
                raise ValueError(
                    f"Event 的 delay 要填秒數 (數字)，收到 {delay!r}。"
                )

            if delay <= 0:
                raise ValueError(
                    f"Event 的 delay 要大於 0，收到 {delay!r}。\n"
                    f"想要「一進房間就觸發」請用 trigger=TriggerType.ENTER_ROOM，不要用 delay=0。"
                )

            # 計時事件的 limit 只能是 1 (也就是預設值)。
            #
            # 為什麼擋得這麼死：探索主迴圈是每 0.2 秒檢查一次「誰到點了」，
            # 而時間一旦超過 delay 就「一直」都是超過。
            # limit 不是 1 的話，同一趟進房間裡它會每 0.2 秒觸發一次 ——
            # limit=None 是無限轟炸，limit=2 也會在 0.2 秒內連放兩次。
            #
            # 「發生一次就死」正好讓死亡的事件連條件都不再被檢查，
            # 所以不需要另外記「這趟已經放過了」。
            # 真的需要重複出現的鬼，之後再單獨設計 (例如換房間重新武裝)。
            if limit != 1:
                raise ValueError(
                    f"trigger=TriggerType.TIMER 的 Event 的 limit 只能是 1，收到 {limit!r}。\n"
                    f"時間過了之後會一直是「已經過了」，所以 limit 不是 1 的計時事件\n"
                    f"會在同一趟進房間裡每 0.2 秒重複觸發。\n"
                    f"limit 不填就是 1，通常直接拿掉就對了。"
                )

            return delay

        @staticmethod
        def _validate_interrupt(interrupt, trigger):
            """
            只有 TIMER 事件能標 interrupt，而且必須是 True / False。

            為什麼要擋：進房事件、點擊事件本來就是玩家自己的動作引發的，
            沒有「打斷」這回事 —— 標了也完全不會有任何效果，
            而「標了卻沒反應」是那種看不出來的錯誤。
            """
            if not isinstance(interrupt, bool):
                raise ValueError(
                    f"Event 的 interrupt 只能填 True 或 False，收到 {interrupt!r}。"
                )

            if interrupt and trigger != TriggerType.TIMER:
                raise ValueError(
                    "只有 trigger=TriggerType.TIMER 的 Event 能標 interrupt=True。\n"
                    "進房與點擊事件是玩家自己的動作引發的，沒有「打斷」可言。"
                )

            return interrupt

        def trigger_type(self, default_trigger):
            """實際的觸發時機。沒指定就用掛載位置的預設值。"""
            return self.trigger if self.trigger is not None else default_trigger

        def can_fire(self, context, default_trigger, trigger):
            """
            這次派發要不要執行這個 Event。

            這裡「只讀不寫」，可以安全地重複呼叫。
            實際的狀態改動在 Effect.apply()。

            chance 的骰點刻意「不」放在這裡：骰一次就會消耗掉一個亂數
            (而且 Ren'Py 會強制產生一個倒帶檢查點)，那就不是只讀了，
            重複呼叫的結果也會不一樣。
            骰點在 collect_events()，而且只在這個函式回傳 True 之後才骰 ——
            條件都不符的事件不該白骰。
            """
            if self.trigger_type(default_trigger) != trigger:
                return False

            # 死掉的事件直接跳過，連條件都不用算。
            # 這也是為什麼 sequence 的檢查成本會隨遊戲進行而遞減。
            if context.view.is_event_dead(self.id):
                return False

            if self.condition is not None and not self.condition.test(context.view):
                return False

            return True

        def __repr__(self):
            return f"<Event {self.id} seq={self.sequence}>"


    # --- 次數累積：「第 N 次進來／點第 N 下才發生」 ---
    #
    # 不靠計時器製造意外感的做法之一：數玩家的動作次數，而不是數秒數。
    # 次數本來就記在 GameState.events 裡，所以存檔、倒帶天生就對 ——
    # 不需要任何額外機制。
    #
    #     room.add_event(visit_counter("attic.visits"))
    #     room.add_event(Event(
    #         id="attic.ghost_scare",
    #         condition=Condition(check=count_at_least("attic.visits", 3)),
    #         effect=Effect(label="attic_ghost_scare"),
    #     ))
    #
    # 為什麼要一個專門的計數器，不能直接數 on_enter：
    # on_enter 的 limit 就是 on_enter_limit (預設 1)，開場白講完一次就死亡，
    # 而死掉的 Event 連 record_trigger 都不會再跑 —— 次數永遠停在 1。

    # 計數器的 sequence。
    #
    # 這個數字是 helper 的重點，不是隨便填的：
    # collect_events 是「跑完一個 Event 才換下一個」(套用 Effect、記錄次數、
    # 然後才輪到下一個)，所以計數器只要排在條件事件前面，
    # 第 3 次進來時條件讀到的就真的是 3，不會少一次。
    #
    # 比預設的 0 小 (排在一般事件前面)，但比 on_enter 的 -1000 大 (開場白還是先講)。
    VISIT_COUNTER_SEQUENCE = -900


    def visit_counter(event_id, sequence=None):
        """
        做一個「只負責計數」的 Event：沒有 Effect，永遠不死。

        掛在 Room.events 就是數進房次數，掛在 Hotspot.events 就是數點擊次數
        (跟一般的 Event 一樣，時機由掛載位置決定)。

        配 count_at_least() 使用。
        """
        return Event(
            id=event_id,
            effect=None,
            limit=None,
            sequence=VISIT_COUNTER_SEQUENCE if sequence is None else sequence,
        )


    def count_at_least(event_id, n):
        """
        回傳一個給 Condition(check=...) 用的判斷式：那個 Event 觸發過至少 n 次。

            Condition(check=count_at_least("attic.visits", 3))

        純讀取，所以掛在 Hotspot 的顯示條件上 (每幀求值) 也安全。
        """
        return lambda view: view.event_count(event_id) >= n


    def chance_passes(chance):
        """
        骰一次機率。None 或 >= 1.0 不骰直接算通過，<= 0.0 直接算沒中。

        用 renpy.random 而不是 Python 內建的 random ——
        renpy.random 產生的數字會被記進倒帶紀錄，倒帶時 pushback()
        會照原順序重新發一次，所以「倒帶回去重玩」骰出來的結果是一樣的。
        內建的 random 沒有這個保證，倒帶前後會不一致。

        兩件要注意的事：

        1. 每骰一次 Ren'Py 都會強制產生一個倒帶檢查點，
            所以不要在每幀都會跑的地方骰 —— 熱點的顯示條件就是每幀求值，
            機率因此只能掛在 Event 上，不能寫進 Hotspot.condition。

        2. 邊界值 (None / 0 / 1) 不骰，免得白白消耗亂數與檢查點。
        """
        if chance is None or chance >= 1.0:
            return True

        if chance <= 0.0:
            return False

        return renpy.random.random() < chance


    class EventContext:
        """
        派發事件時傳進去的執行環境。

        刻意不放角色定義 —— 角色是靜態定義，條件式要查就用
        actor_def(key) 現查（見 game/libs/state/actor.rpy）。
        放進這裡只會多一份可能跟目錄不同步的複本。
        """

        def __init__(self, game_state, current_room=None):
            self.game_state = game_state
            self.current_room = current_room

            # 唯讀視圖，給 Condition 用。
            # 它持有 game_state 的引用，所以查詢永遠是即時的 ——
            # 前面的 Effect 改了狀態，後面的 Condition 馬上看得到。
            #
            # 房間明確傳進去，而不是讓視圖自己去問 store.current_room：
            # 派發「離開房間」的事件時，條件式該看到的是正要離開的那一間。
            # 目前 change_room 剛好是先派發再換，所以兩者一致；
            # 傳進去是為了不依賴那個順序。
            self.view = game_state.view(room=current_room)

        def __repr__(self):
            room = self.current_room.name if self.current_room else None
            return f"<EventContext room={room}>"
