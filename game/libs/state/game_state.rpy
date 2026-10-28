##################################################
# game_state.rpy
#
#   遊戲狀態的總容器，以及給 Condition 用的唯讀視圖。
#
#   GameState 持有四個 section：
#     inventory  玩家有什麼東西
#     flags      做過什麼事
#     events     每個 Event 觸發過幾次、死了沒
#     actors     角色身上的數值 (血量、憤怒值……) 與死亡狀態
#
#   世界時鐘「不在」這裡 —— 它每秒被改 20 次，放進被倒帶追蹤的
#   GameState 會被倒帶抹掉。見 game/libs/explore/world.rpy 的說明。
#
#   四個 section 刻意「不」共用基底類別，只約定它們都有 reset()。
#   原因是 Ren'Py 會忽略 game/libs/ 底下第一層目錄名來決定載入順序
#   (見 game/libs/libs.txt)，所有檔案是混在一起按檔名字母序載入的，
#   有繼承關係的話基底類別很可能還沒定義就被拿來繼承。
#   Python 本來就不需要繼承才能統一管理，用不著為此冒險。
#
#   存檔：不用自己寫序列化。default game_state = GameState() 之後，
#   Ren'Py 會自動把它存進存檔。
#
#   倒帶：這一層刻意「不」用 NoRollback，跟 Room / Hotspot / Camera 相反。
#   那三個是場景定義；而物品與旗標是遊戲進度，
#   玩家滾滑鼠滾輪倒帶時本來就該跟著還原。
##################################################

init python:

    class GameState:
        def __init__(self):
            # 這裡刻意不逐行寫 self.inventory = ... ——
            # 讓「有哪些 section」只存在 _section_specs() 那一張表裡。
            self.ensure_sections()

        def _section_specs(self):
            """
            所有 section：(屬性名稱, 建構函式)。

            **新增 section 只要改這一張表**，sections() 與 ensure_sections()
            都從這裡讀。每個 section 要有 reset()。

            為什麼是方法不是類別屬性：Ren'Py 按檔名字母序載入 game/libs/，
            inventory_state.rpy 排在 game_state.rpy 後面，
            寫成類別屬性的話 class 建立當下 InventoryState 還不存在。
            """
            return [
                ("inventory", InventoryState),
                ("flags", FlagState),
                ("events", EventState),
                ("actors", ActorState),
            ]

        def ensure_sections(self):
            """
            補上缺少的 section，回傳這次補了哪些。

            存在的 section 一律不動 —— 讀舊存檔時進度不能被蓋掉。

            為什麼需要這個：存檔是把 GameState 的 __dict__ 原樣存起來，
            讀檔時**不會**呼叫 __init__。所以工具包多一個 section 之後，
            舊存檔讀回來身上就是沒有那個屬性，下一次 game_state.actors
            會直接 AttributeError。label after_load 會呼叫這裡補齊。
            """
            added = []
            for name, factory in self._section_specs():
                if getattr(self, name, None) is None:
                    setattr(self, name, factory())
                    added.append(name)
            return added

        def sections(self):
            """所有 section 物件。"""
            return [getattr(self, name) for name, _ in self._section_specs()]

        def reset(self):
            """把整個遊戲進度清空。debug 用，正常遊戲流程不會呼叫。"""
            for section in self.sections():
                section.reset()

        def view(self, room=None):
            """
            取得唯讀視圖，給 Condition 判斷用。

            room 可以指定「要以哪個房間為準」。不給的話視圖會去問
            store.current_room，也就是玩家現在真正在的房間。

            需要指定的情況只有一種：派發離開房間的事件時，current_room
            還沒被換掉（change_room 刻意先派發再換），但未來若順序改變，
            EventContext 傳自己的房間進來就永遠是對的。
            """
            return StateView(self, room)

        def __repr__(self):
            return f"<GameState {self.inventory} {self.flags} {self.events} {self.actors}>"


    class StateView:
        """
        GameState 的唯讀視圖。

        Condition 只拿得到這個，不是完整的 GameState ——
        所以條件式「結構上」就改不到任何狀態，不用靠自律。

        這件事很重要：熱點的顯示條件會在畫面每次重繪時被求值，
        探索畫面又是每 16ms 重繪一次。
        如果條件求值有副作用，每秒 60 次會把遊戲狀態改爛。
        """

        def __init__(self, game_state, room=None):
            # 底線開頭表示「不要碰」。這裡不提供任何會改狀態的方法。
            self._gs = game_state
            self._room = room

        # --- 物品 ---

        def has_item(self, key):
            return self._gs.inventory.has(key)

        def item_count(self, key):
            return self._gs.inventory.count_of(key)

        def item_keys(self):
            return self._gs.inventory.keys()

        # --- 旗標 ---

        def has_flag(self, key):
            return self._gs.flags.has(key)

        # --- 事件 ---

        def event_count(self, event_id):
            return self._gs.events.count_of(event_id)

        def is_event_dead(self, event_id):
            return self._gs.events.is_dead(event_id)

        # --- 所在的房間 ---

        def room_name(self):
            """
            玩家現在在哪個房間（字串）。還沒進任何房間時是 None。

                Condition(check=lambda s: s.room_name() == "chapel")

            為什麼只給名稱、不給 Room 物件：
            Room 身上有 hotspots 這種可以被改的東西，而條件式會在畫面
            每次重繪時被求值（每 16ms 一次）。把物件交出去就等於開了一道
            「每秒 60 次都能改場景」的門 —— 而 StateView 存在的全部意義
            就是讓條件式「結構上」改不到任何東西。

            用 getattr 問 store.current_room 是為了維持 game/libs/state/
            不依賴 explore 的獨立性（沒有探索工具包時回傳 None，不會爆）。
            """
            room = self._room

            if room is None:
                room = getattr(store, "current_room", None)

            return getattr(room, "name", None)

        def in_room(self, *names):
            """
            玩家是不是在這幾個房間之一。

                Condition(check=lambda s: s.in_room("chapel"))
                Condition(check=lambda s: s.in_room("chapel", "graveyard"))

            拿來做「安妮在有十字架的房間裡就一直是虛弱的」這種表情推導。
            """
            return self.room_name() in names

        # --- 角色數值 ---

        def stats(self, actor, name):
            """
            查一個角色的數值，沒有的話回傳 0。

                Condition(check=lambda s: s.stats("player", "hp") <= 1)
                Condition(check=lambda s: s.stats("annie_ghost", "rage") >= 5)

            名稱跟 Effect(stats={...}) 對齊，讀寫兩邊用同一個字。

            打錯角色 id 會直接報錯（見 _require_known_actor）。
            """
            self._require_known_actor(actor)
            return self._gs.actors.get(actor, name)

        def is_dead(self, actor):
            self._require_known_actor(actor)
            return self._gs.actors.is_dead(actor)

        def is_alive(self, actor):
            self._require_known_actor(actor)
            return self._gs.actors.is_alive(actor)

        def _require_known_actor(self, actor):
            """
            條件式裡的角色 id 打錯就直接報錯。

            為什麼讀取也要擋：Effect(actor=...) 的打錯字可以在啟動時
            靜態掃出來（見 find_unknown_actor_ids），但這種不行 ——

                Condition(check=lambda s: s.stats("anie_ghost", "rage") >= 2)

            字串在 lambda 裡面，靜態掃不到。而它的症狀是最難查的那種：
            回傳 0 → 條件永遠不成立 → 那個事件就是不會發生，
            畫面上完全看不出有什麼不對。

            為什麼 ActorState 不跟著嚴格 (它的 get 仍然「查不到回傳 0」)：
            那一層是「儲存」，像 dict 一樣寬鬆才好測 —— 單元測試要能
            餵假的角色 id 進去驗 is_dead 的四種情況，不該被迫把測試用的
            假角色塞進遊戲的角色目錄。
            StateView 是「設計者寫條件的介面」，打錯字在這裡完全看不出來，
            所以嚴格擋在這一層。
            (2026-10-28 改。原本這裡也是「查不到回傳 0」)

            沒有宣告角色目錄的專案一律跳過檢查 ——
            known_actor_ids() 在那種情況回傳 None（而不是空集合），
            所以「沒在用角色目錄」與「目錄是空的」分得出來。
            (actor.rpy 跟這個檔案同在 game/libs/state/，會一起被複製走，
            所以可以直接呼叫它)
            """
            known = known_actor_ids()

            if known is None or actor in known:
                return

            raise ValueError(
                f"條件式裡用了不存在的角色 \"{actor}\"。\n"
                f"目前有的是：{sorted(known)}\n"
                f"是不是拼錯了，或是忘了在 build_actors() 裡加進去？"
            )

        # --- 統一查詢 ---

        def has(self, key):
            """
            物品與旗標共用同一個命名空間：有一邊算「有」就算有。

            這樣寫條件時不用記住每個 key 屬於哪一類 ——
            對解謎來說「有鑰匙」跟「開過門」在判斷上就是同一件事。
            代價是物品與旗標不能取同樣的名字。
            """
            return self.has_item(key) or self.has_flag(key)

        def __repr__(self):
            return f"<StateView of {self._gs}>"


# 全域唯一的遊戲狀態。Ren'Py 會自動把它存進存檔。
default game_state = GameState()


# 讀檔之後 Ren'Py 會自動跑這個 label（不用自己呼叫）。
#
# 用途：工具包之後多一個 section（任務、鬼的計時器……）時，
# 更早之前存的檔身上沒有那個屬性，讀回來一碰就 AttributeError。
# 這裡替舊存檔補上預設值，已經有的進度完全不動。
#
# 注意這只補「整個 section 不見了」這種情況。
# section 內部的欄位改了形狀（例如 dict 換成 list）還是要自己寫轉換。
label after_load:
    $ game_state.ensure_sections()
    return
