##################################################
# effect.rpy
#
#   事件的結果。這是整個事件系統裡唯一「會改狀態」的部分。
#
#   Effect 只做 state mutation，六個欄位全部都是改 GameState。
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

            # 狀態改完之後要跑的 label。可省略。
            label=None,
        ):
            self.give_items = self._as_list(give_items)
            self.remove_items = self._as_list(remove_items)
            self.set_flags = self._as_list(set_flags)
            self.clear_flags = self._as_list(clear_flags)
            self.kill_events = self._as_list(kill_events)
            self.label = label

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

            執行順序是固定的：給物品 → 拿物品 → 設旗標 → 清旗標 → 殺事件。
            這個順序由引擎決定，寫 Effect 的人不用去想它 ——
            因為六種改動彼此不相依，順序不會影響結果。
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

            return self.label

        def __repr__(self):
            return f"<Effect label={self.label}>"
