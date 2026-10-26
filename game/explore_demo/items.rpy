##################################################
# items.rpy
#
#   物品目錄 (遊戲內容，不屬於 game/libs/ 的引擎)
#
#   新增物品的步驟：
#     在下面 build_items() 裡加一行 items["xxx"] = Item(...)
#   之後就可以用 Effect(give_items=["xxx"]) 給玩家。
#
#   物品欄 (InventoryState) 裡只存 key 與數量，
#   名稱/圖示/描述一律用 item_def(key) 即時查這個目錄。
##################################################

init python:

    def build_items():
        items = {}

        items["key"] = Item(
            key="key",
            name="生鏽的鑰匙",
            description="一把沾滿鏽的舊鑰匙。\n看起來能開某個櫃子。",
            tag="鑰匙",
        )

        items["note"] = Item(
            key="note",
            name="潮濕的紙條",
            description="字跡被水暈開了，只勉強看得出來：\n\n「別相信廚房裡的聲音。」\n\n角落用原子筆潦草寫著：4721",
            tag="線索",
        )

        items["documents"] = Item(
            key="documents",
            name="牛皮紙袋",
            description="裝著一疊文件。\n第一頁的照片上，有人的臉被塗掉了。",
            tag="線索",
        )

        # 近景視窗示範用 (實驗區的抽屜)。
        # 拿走之後抽屜的底圖會跟著變空 —— 見 playground.rpy 的 state_image。
        items["torn_photo"] = Item(
            key="torn_photo",
            name="撕成兩半的照片",
            description="只剩右半邊。\n一隻手搭在某個人的肩膀上，\n而那個人不在這半張裡。",
            tag="線索",
        )

        items["coin10"] = Item(
            key="coin10",
            name="10元",
            description="用來買飲料",
            tag="娛樂",
        )

        # 檢查每一筆的 dict key 與 Item.key 是否一致，不一致就直接報錯。
        # 兩邊不一樣的話遊戲照跑、物品欄也正常，
        # 只有在照著 Item.key 寫條件時才會發現查不到 —— 那種問題最難查。
        return validate_item_catalog(items)


# 用 define 而不是 default —— 這是個刻意的決定。
#
# 物品目錄是「靜態定義」，裡面沒有任何會變動的東西
# (玩家有幾把鑰匙記在 GameState.inventory，不在這裡)。
# define 不會進存檔，所以改了物品名稱或描述之後，
# 連舊存檔都會馬上吃到新的。
#
# 如果用 default，整個目錄會被存進存檔，
# 就會重蹈 rooms 的覆轍：改了定義卻要重開新遊戲才看得到。
define item_catalog = build_items()
