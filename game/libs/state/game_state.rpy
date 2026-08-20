##################################################
# game_state.rpy
#
#   遊戲狀態的總容器，以及給 Condition 用的唯讀視圖。
#
#   GameState 持有三個 section：
#     inventory  玩家有什麼東西
#     flags      做過什麼事
#     events     每個 Event 觸發過幾次、死了沒
#
#   三個 section 刻意「不」共用基底類別，只約定它們都有 reset()。
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
            self.inventory = InventoryState()
            self.flags = FlagState()
            self.events = EventState()

        def sections(self):
            """所有 section。新增 section 時記得加進這裡，並確保它有 reset()。"""
            return [self.inventory, self.flags, self.events]

        def reset(self):
            """把整個遊戲進度清空。debug 用，正常遊戲流程不會呼叫。"""
            for section in self.sections():
                section.reset()

        def view(self):
            """取得唯讀視圖，給 Condition 判斷用。"""
            return StateView(self)

        def __repr__(self):
            return f"<GameState {self.inventory} {self.flags} {self.events}>"


    class StateView:
        """
        GameState 的唯讀視圖。

        Condition 只拿得到這個，不是完整的 GameState ——
        所以條件式「結構上」就改不到任何狀態，不用靠自律。

        這件事很重要：熱點的顯示條件會在畫面每次重繪時被求值，
        探索畫面又是每 16ms 重繪一次。
        如果條件求值有副作用，每秒 60 次會把遊戲狀態改爛。
        """

        def __init__(self, game_state):
            # 底線開頭表示「不要碰」。這裡不提供任何會改狀態的方法。
            self._gs = game_state

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
