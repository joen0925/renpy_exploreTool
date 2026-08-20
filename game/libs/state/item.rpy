##################################################
# item.rpy
#
#   物品
#
#   注意這裡刻意「不」繼承 NoRollback，跟 Room / Hotspot / Camera 相反。
#   那三個是場景定義，不該被玩家倒帶影響；
#   但物品是遊戲進度，玩家滾滑鼠滾輪倒帶時，本來就應該跟著還原成當時的狀態。
#   Ren'Py 在 init python 裡定義的類別預設就是可倒帶的，所以不加任何東西就是對的。
##################################################

init python:

    class Item:
        def __init__(
            self,
            key,            # 唯一識別字串，條件判斷用的就是這個，例如 "key"
            name,           # 顯示名稱，例如 "地下室鑰匙"
            description=None,  # 詳細描述，點物品欄時顯示
            icon=None,      # 圖示，物品欄顯示用；可以是圖片路徑或任何 displayable
            count=1,        # 數量，可堆疊物品用
            tag=None,       # 分類標籤，例如 "鑰匙類" / "線索類"，方便篩選或分頁
        ):
            self.key = key
            self.name = name
            self.description = description
            self.icon = icon
            self.count = count
            self.tag = tag

        def __repr__(self):
            return f"<Item {self.key}>"


    def item_def(key):
        """
        從物品目錄查一個物品的定義。查不到回傳 None。

        物品欄 (InventoryState) 裡只存 key 與數量，
        名稱/圖示/描述一律即時查這個目錄 ——
        這樣改了物品定義，連舊存檔都會馬上吃到新的。
        (rooms 就是因為把整個物件存進存檔，才會發生「改了座標舊存檔看不到」的問題)

        目錄由遊戲內容那邊宣告，例如：
            default item_catalog = build_items()
        引擎不宣告它，因為物品清單屬於遊戲內容。
        """
        return getattr(store, "item_catalog", {}).get(key)
