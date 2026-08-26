##################################################
#
#	房間物件
# 	屬性:背景、大小、各種hotspots位置
#   方法:熱點的新增、移除、查詢
##################################################

init python:

    def room_by_name(name):
        """
        把房間名稱換回房間物件。存檔還原時會用到 (見 Room.__reduce__)。

        用 getattr 而不是直接寫 store.rooms，是因為 rooms 由遊戲內容那邊宣告，
        引擎不能假設它一定存在。
        """
        room = getattr(store, "rooms", {}).get(name)

        if room is None:
            raise ValueError(
                f"讀檔失敗：存檔裡記著玩家在 \"{name}\"，但目前的房間清單裡沒有這個房間。\n"
                f"是不是把它從 build_rooms() 裡刪掉或改名了？"
            )

        return room


    # 繼承 NoRollback：這是場景資料，不是劇情狀態，
    # 不該被 Ren'Py 的倒帶(rollback)系統追蹤/還原，
    # 不然滑鼠滾輪不小心倒帶時，current_room 等變數可能被還原成不一致的狀態。
    class Room(NoRollback):
        def __init__(
            self,
            name,
            background,
            bg_width=1920,
            music=None,
            hotspots=None, # 這個房間的熱點列表，預設為 None
            on_enter=None, # 進入這個房間時要自動呼叫的 label 名稱 (字串)，可以在裡面講話/做任何事

            # on_enter 最多觸發幾次，預設 1 = 只有第一次進來會講。
            # 想每次進來都觸發就填 None (無限次)，想前兩次都講就填 2。
            on_enter_limit=1,

            # 進房事件清單。需要條件分支的用這個，
            # 裡面的 Event 沒指定 trigger 的話預設是 ENTER_ROOM。
            events=None
        ):
            self.name = name
            self.background = background
            self.bg_width = bg_width
            self.music = music
            self.on_enter = on_enter
            self.on_enter_limit = on_enter_limit

            self.events = list(events) if events else []

            # on_enter 是簡寫，內部就轉成一個「無條件的 Event」，
            # 這樣進房行為只有一套機制，不會有兩個地方可以掛。
            #
            # 觸發次數不記在這裡 —— Room 是 build_rooms() 產生的靜態定義，
            # 按「重新載入房間資料」時會被整個重建，記在這裡會跟著歸零。
            # 次數與死亡狀態統一存在 GameState.events，跟著存檔走。
            if on_enter:
                self.events.append(Event(
                    id=f"{name}.on_enter",
                    effect=Effect(label=on_enter),
                    # 排在最前面：開場白通常要先講完，才輪到其他條件事件
                    sequence=-1000,
                    limit=on_enter_limit,
                ))

            # 如果有傳入 hotspots 就使用傳入的列表，否則初始化為空列表
            self.hotspots = []
            for hotspot in (hotspots or []):
                self.add_hotspot(hotspot)

        def __reduce__(self):
            """
            存檔時「只存房間名稱」，讀檔時再從目前的 rooms 查回來。

            為什麼需要這個：
            current_room 是 default (會進存檔)，所以它指到的整棵
            Room / Hotspot 物件樹都會被 pickle。但 Hotspot 可以帶
            Condition(check=lambda ...)，而那個 lambda 定義在 build_xxx()
            函式內部 —— Python 存不了函式內的區域物件，存檔會直接爆掉：
                AttributeError: Can't get local object 'build_attic.<locals>.<lambda>'

            順便解決另一個長期的痛：房間是靜態定義，把它整個存進存檔的話，
            之後改了熱點座標、改了文字、加了新熱點，舊存檔統統吃不到。
            改成只存名稱之後，讀檔拿到的永遠是「目前的」房間定義。
            這跟物品欄只存 key、名稱圖示即時查 item_catalog 是同一個道理。
            """
            return (room_by_name, (self.name,))

        def add_event(self, event):
            self.events.append(event)

        def add_hotspot(self, hotspot):
            # 記住它屬於哪個房間 —— 存檔時要靠這個把熱點還原回來
            # (見 Hotspot.__reduce__)
            hotspot.room_name = self.name
            self.hotspots.append(hotspot)

        def remove_hotspot(self, hotspot):
            if hotspot in self.hotspots:
                self.hotspots.remove(hotspot)

        def get_hotspot(self, name):
            for hotspot in self.hotspots:
                if hotspot.name == name:
                    return hotspot
            return None