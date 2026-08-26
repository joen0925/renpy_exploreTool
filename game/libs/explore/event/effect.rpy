##################################################
# effect.rpy
#
#   事件的結果。這是整個事件系統裡唯一「會改狀態」的部分。
#
#   Effect 只做 state mutation，所有欄位全部都是改 GameState。
#   劇情 (講話、換房間、播動畫) 一律走 label ——
#   Ren'Py 已經有一整套流程控制，沒必要再實作一套。
#
#   刻意「沒有」的兩個欄位：
#
#   change_room  換房間是流程控制，寫在 label 裡 ($ change_room("kitchen"))
#                順序才自然 (先講「你推開門」再換過去)。
#                放進 Effect 反而要多定一條「label 跟換房間誰先跑」的規則。
#
#   熱點顯隱     那是 Room 物件上的狀態，不是 GameState。
#                Room 會被「重新載入房間資料」重建，命令式改的顯隱會消失。
#                改用 Hotspot.condition 由條件推導，冪等而且 reload 安全：
#                  Hotspot(..., condition=Condition(forbid=["key"]))
#                撿走鑰匙後這個熱點自動消失，不需要任何人去 hide 它。
##################################################

init python:

    class Effect:
        def __init__(
            self,
            give_items=None,    # 給物品。可寫 ["key"] 或 [("coin", 3)] 指定數量
            remove_items=None,  # 拿走物品。同樣支援 (key, count)
            set_flags=None,     # 設旗標
            clear_flags=None,   # 清旗標
            kill_events=None,   # 讓指定 event_id 死亡，可以殺別的房間的事件

            # 角色數值的「增減量」，不是設定值：
            #     Effect(actor="player", stats={"hp": -1})           玩家扣一滴血
            #     Effect(actor="annie_ghost", stats={"rage": +1})    安妮的憤怒值 +1
            #     Effect(actor="player", stats={"battery": -10, "hp": -1})  一次改多個
            #
            # 一個 Effect 只對一個角色。要同時改兩個角色就寫兩個 Event ——
            # 這比讓 key 變成 ("annie_ghost", "rage") 這種 tuple 好讀太多。
            stats=None,

            # stats 要改到誰身上。有 stats 就一定要填，沒填會直接報錯。
            #
            # 刻意不給「沒填就是主角」的預設值：
            # Effect(stats={"hp": -1}) 這種寫法看不出來扣的是誰的血，
            # 而扣錯角色的血是那種「遊戲照跑、幾天後才發現」的錯誤。
            # 寧可多打幾個字。
            actor=None,

            # 狀態改完之後要跑的 label。可省略。
            label=None,
        ):
            self.give_items = self._as_list(give_items)
            self.remove_items = self._as_list(remove_items)
            self.set_flags = self._as_list(set_flags)
            self.clear_flags = self._as_list(clear_flags)
            self.kill_events = self._as_list(kill_events)
            self.stats = dict(stats) if stats else {}
            self.actor = actor
            self.label = label

            # 有 stats 卻沒指定 actor 就直接爆掉。
            #
            # Effect 是在 build_rooms() 裡建立的，所以這個錯誤會在遊戲啟動時
            # 就跳出來，不會等到玩家真的點到那個熱點才發現。
            if self.stats and self.actor is None:
                raise ValueError(
                    f"Effect 有 stats={self.stats} 卻沒有指定 actor。\n"
                    f"要改誰的數值一定要寫清楚，例如 "
                    f"Effect(actor=\"player\", stats={self.stats})。"
                )

        @staticmethod
        def _as_list(value):
            if value is None:
                return []
            if isinstance(value, str):
                return [value]
            return list(value)

        @staticmethod
        def _split(entry):
            """
            物品條目可以是 "key" 或 ("key", 數量)，統一拆成 (key, count)。
            """
            if isinstance(entry, str):
                return entry, 1
            key, count = entry
            return key, count

        def apply(self, game_state):
            """
            套用所有狀態改動，回傳要跑的 label (沒有就是 None)。

            執行順序是固定的：
            給物品 → 拿物品 → 設旗標 → 清旗標 → 殺事件 → 改角色數值。
            這個順序由引擎決定，寫 Effect 的人不用去想它 ——
            因為各種改動彼此不相依，順序不會影響結果。
            """
            for entry in self.give_items:
                key, count = self._split(entry)
                game_state.inventory.add(key, count)

            for entry in self.remove_items:
                key, count = self._split(entry)
                game_state.inventory.remove(key, count)

            for key in self.set_flags:
                game_state.flags.set(key)

            for key in self.clear_flags:
                game_state.flags.clear(key)

            for event_id in self.kill_events:
                game_state.events.kill(event_id)

            # stats 是增減量，所以用 add() 不是 set()。
            # add() 會夾在 0 以上，扣過頭不會變負數。
            for stat, delta in self.stats.items():
                game_state.actors.add(self.actor, stat, delta)

            return self.label

        def __repr__(self):
            return f"<Effect label={self.label}>"
