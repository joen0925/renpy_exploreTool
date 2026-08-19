##################################################
# camera.rpy
#
# FNAF Style Camera v0.1
#
#   屬性:鏡頭位移、背景寬度、平滑度
#   方法:進入房間、每幀更新
##################################################

init python:

    # 繼承 NoRollback：offset 每秒會被改寫約 60 次，
    # 如果讓 Ren'Py 的倒帶(rollback)系統追蹤它，
    # 一來 rollback log 會被這些沒有劇情意義的數值灌爆，
    # 二來玩家滾滑鼠滾輪倒帶時 offset 可能被還原成舊房間的值，
    # 跟 current_room 對不起來 (跟 Room / Hotspot 用 NoRollback 是同一個理由)。
    class Camera(NoRollback):

        def __init__(self):

            # 鏡頭位移：負值代表背景往左推 (畫面看到的是右邊的內容)
            self.offset = 0

            # 目前房間背景圖的實際寬度
            self.bg_width = 1920

            # 平滑度：每幀往目標位置靠近的比例，越小越慢、越滑順
            self.smooth = 0.10

        def enter_room(self, room):

            self.bg_width = room.bg_width

            # 一進房間先讓鏡頭對齊整張背景圖的正中間，
            # 而不是每次都貼在最左邊 (0)。
            # 圖比螢幕窄的話 (差值是正的) 就不偏移，維持貼左。
            screen_width = renpy.config.screen_width
            self.offset = min(0, -(self.bg_width - screen_width) / 2.0)

        def update(self):

            screen_width = renpy.config.screen_width

            mouse_x, _ = renpy.get_mouse_pos()

            # 滑鼠在螢幕上的水平比例 (最左 0.0、最右 1.0)
            ratio = mouse_x / float(screen_width)

            # 滑鼠可能跑到視窗外面，夾在 0.0 ~ 1.0 之間避免鏡頭超出背景
            ratio = max(0.0, min(1.0, ratio))

            # 目標位移：滑鼠在最左時為 0 (看背景左緣)，
            # 最右時為 -(bg_width - screen_width) (看背景右緣)
            target = -(self.bg_width - screen_width) * ratio

            # 指數逼近：不直接跳到 target，每幀只走 smooth 的比例，做出滑順的跟隨感
            self.offset += (target - self.offset) * self.smooth


# 全域唯一的鏡頭實例，explore()/room_background() 畫面與 change_room() 都直接用它。
default camera = Camera()