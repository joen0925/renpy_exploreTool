##################################################
# condition.rpy
#
#   條件判斷。這是整個事件系統裡唯一「只讀不寫」的部分。
#
#   Condition.test() 收到的是 StateView (唯讀視圖) 而不是 GameState，
#   所以條件式結構上就改不到任何狀態，不用靠自律。
#
#   為什麼堅持唯讀：熱點的顯示條件會在畫面每次重繪時被求值，
#   而探索畫面是每 16ms 重繪一次。
#   如果條件求值有副作用，每秒 60 次會把遊戲狀態改爛。
#
#   物品與旗標共用同一個命名空間 —— view.has(key) 兩邊都查，
#   有一邊算「有」就算有。寫條件時不用記住每個 key 屬於哪一類。
##################################################

init python:

    class Condition:
        def __init__(
            self,
            require=None,      # 全部都要有 (AND)
            require_any=None,  # 至少要有一個 (OR)
            forbid=None,       # 全部都不能有 (NOT)

            # 逃生艙：接收 StateView 的函式，回傳 True/False。
            # 上面三個欄位表達不了的條件才用它，例如
            #   check=lambda v: v.item_count("coin") >= 3
            check=None,
        ):
            # 允許直接傳字串，不用每次都包成 list
            self.require = self._as_list(require)
            self.require_any = self._as_list(require_any)
            self.forbid = self._as_list(forbid)
            self.check = check

        @staticmethod
        def _as_list(value):
            if value is None:
                return []
            if isinstance(value, str):
                return [value]
            return list(value)

        def test(self, view):
            """
            view 是 StateView。全部條件都通過才回傳 True。

            四個欄位都沒設的話永遠回傳 True (無條件)。
            """
            for key in self.require:
                if not view.has(key):
                    return False

            if self.require_any:
                if not any(view.has(key) for key in self.require_any):
                    return False

            for key in self.forbid:
                if view.has(key):
                    return False

            if self.check is not None and not self.check(view):
                return False

            return True

        def __repr__(self):
            parts = []
            if self.require:
                parts.append(f"require={self.require}")
            if self.require_any:
                parts.append(f"any={self.require_any}")
            if self.forbid:
                parts.append(f"forbid={self.forbid}")
            if self.check:
                parts.append("check=<fn>")
            return f"<Condition {' '.join(parts) or 'always'}>"
