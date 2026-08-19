##################################################
#
#	房間物件
# 	屬性:背景、大小、各種hotspots位置
#   方法:熱點的新增、移除、查詢
##################################################

init python:
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
            on_enter_limit=1
        ):
            self.name = name
            self.background = background
            self.bg_width = bg_width
            self.music = music
            self.on_enter = on_enter
            self.on_enter_limit = on_enter_limit

            # on_enter 已經觸發過幾次。
            # 計數存在 Room 物件上，所以會跟著存檔走；
            # 但按 debug 面板的「重新載入房間資料」時整個 Room 會被重建，
            # 計數也會跟著歸零 (等於這個房間被重置成沒進來過)。
            self.on_enter_count = 0

            # 如果有傳入 hotspots 就使用傳入的列表，否則初始化為空列表
            self.hotspots = hotspots if hotspots is not None else []

        def can_trigger_on_enter(self):
            """這次進來還該不該觸發 on_enter。"""
            if not self.on_enter:
                return False

            # limit 是 None 代表不限次數，每次進來都觸發
            if self.on_enter_limit is None:
                return True

            return self.on_enter_count < self.on_enter_limit

        def add_hotspot(self, hotspot):
            self.hotspots.append(hotspot)

        def remove_hotspot(self, hotspot):
            if hotspot in self.hotspots:
                self.hotspots.remove(hotspot)

        def get_hotspot(self, name):
            for hotspot in self.hotspots:
                if hotspot.name == name:
                    return hotspot
            return None