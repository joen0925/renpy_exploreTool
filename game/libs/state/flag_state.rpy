##################################################
# flag_state.rpy
#
#   旗標：記錄「做過某件事」的布林標記。
#
#   跟 inventory 的差別是這不是「拿到一個東西」，不會進物品欄。
#   例如：剪斷過電線、拉過拉桿、看過某段對話、解開某個機關。
#
#   這是 GameState 的一個 section。所有 section 都要有 reset()，
#   GameState 靠這個約定統一重置（刻意不用繼承，避免 libs 的載入順序問題）。
##################################################

init python:

    class FlagState:
        def __init__(self):
            # 用 set 而不是 dict：旗標只有「有」跟「沒有」兩種狀態，
            # 不需要存值。要存值的東西應該放 inventory 或另開 section。
            self.flags = set()

        def set(self, key):
            self.flags.add(key)

        def clear(self, key):
            self.flags.discard(key)

        def has(self, key):
            return key in self.flags

        def all_flags(self):
            return sorted(self.flags)

        def reset(self):
            self.flags = set()

        def __repr__(self):
            return f"<FlagState {sorted(self.flags)}>"
