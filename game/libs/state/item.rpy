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


    def validate_item_catalog(items):
        """
        檢查物品目錄裡每一筆的 dict key 與 Item.key 是否一致，回傳原本的 dict。

        用法：在 build_items() 的最後包一層
            return validate_item_catalog(items)

        為什麼需要這個檢查：
        真正被使用的是 dict 的 key —— give_items / require / item_def 查的都是它。
        Item.key 只是給人看的。所以兩邊不一致的話遊戲照跑，物品欄也顯示正常，
        只有在你照著 Item.key 寫條件時才會發現「明明有這個物品卻查不到」，
        而那時候你多半不會聯想到是目錄寫錯了。

        這種靜默的不一致最難查，所以寧可在遊戲啟動時就直接爆掉。
        """
        for dict_key, item in items.items():
            if item.key != dict_key:
                raise ValueError(
                    f"物品目錄不一致：這一筆放在 \"{dict_key}\" 底下，"
                    f"但 Item.key 寫的是 \"{item.key}\"。\n"
                    f"實際被使用的是 \"{dict_key}\" (give_items / require / item_def 查的都是它)，"
                    f"請把兩邊改成一樣。"
                )

        return items


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
