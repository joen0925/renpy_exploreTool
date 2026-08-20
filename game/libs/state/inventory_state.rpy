##################################################
# inventory_state.rpy
#
#   物品欄：玩家身上有哪些東西、各有幾個。
#
#   這裡只存 key -> 數量，不存 Item 物件。
#   名稱/圖示/描述一律用 item_def(key) 即時查物品目錄，
#   這樣改了物品定義，連舊存檔都會馬上吃到新的。
#
#   這是 GameState 的一個 section，要有 reset()。
##################################################

init python:

    class InventoryState:
        def __init__(self):
            # key -> 數量。數量為 0 的物品會直接移除，不留空殼。
            self.items = {}

        def add(self, key, count=1):
            """加入物品。已經有的話數量累加。"""
            if count <= 0:
                return

            self.items[key] = self.count_of(key) + count

        def remove(self, key, count=1):
            """
            移除物品。數量歸零或變負就整個拿掉。

            移除不存在的物品不會出錯，直接忽略 ——
            因為 Effect 的 remove_items 常常寫成「有就拿掉」，
            不該逼呼叫端每次都先檢查一遍。
            """
            if key not in self.items:
                return

            remaining = self.items[key] - count

            if remaining > 0:
                self.items[key] = remaining
            else:
                del self.items[key]

        def has(self, key):
            return key in self.items

        def count_of(self, key):
            return self.items.get(key, 0)

        def keys(self):
            """目前持有的所有 key，依加入順序。"""
            return list(self.items.keys())

        def reset(self):
            self.items = {}

        def __repr__(self):
            return f"<InventoryState {self.items}>"
