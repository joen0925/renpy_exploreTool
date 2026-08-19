##################################################
#
#	互動點
# 	屬性:背景、大小、各種hotspots位置
#   方法:顯示、隱藏、可用、不可用
##################################################
init python:
    # 繼承 NoRollback：這是場景資料，不是劇情狀態，
    # 不該被 Ren'Py 的倒帶(rollback)系統追蹤/還原，
    # 不然滑鼠滾輪不小心倒帶時，變數可能被還原成不一致的狀態。
    class Hotspot(NoRollback):
        def __init__(
            self,
            name,
            x,
            y,

            idle=None,
            hover=None,

            action=None,

            visible=True,
            enabled=True,

            width=None,
            height=None,

            tag=None,
            examine=None,

            data=None,
            debug=False,

            # 撿取物品用：設定後，玩家撿過這個熱點就會自動消失。
            # v0.1 還沒有 inventory 模組，這個欄位目前不會被任何地方消費，
            # 等 inventory 接上後才會在 explore() 畫面裡生效。
            item=None,

            # 點擊這個熱點時要播放的音效 (例如打開工具箱的「開箱」聲)，
            # 用 Ren'Py 按鈕內建的 activate_sound 播放，不用自己寫 renpy.play()，
            # 也不會有「在 interaction 裡面播放」的問題。可省略 (預設不播放)。
            sound=None,

            # 文字/emoji 熱點 (例如 "🔑 點我拿取鑰匙")，設定後這個熱點會畫成 textbutton，
            # 而不是用 idle/hover 圖片或 debug 紅框。
            label=None,
            label_size=28,
            label_color="#e67e22",
            label_hover_color="#ffffff",

            # 點擊前檢查 inventory 有沒有這個物品：
            #   require_item 設定後，每次點擊當下才會檢查
            #   - 有該物品 -> 執行 action
            #   - 沒有該物品 -> 改執行 action_if_missing (例如講一句話、放嚇人音效)
            # v0.1 還沒有 inventory 模組，這兩個欄位目前不會被 hotspot_action() 消費，
            # 一律執行 action。
            require_item=None,
            action_if_missing=None,
        ):
            # 基本資訊
            self.name = name

            # 位置 (背景圖座標，不是螢幕座標；顯示時由外層容器統一做鏡頭位移)
            self.x = x
            self.y = y

            # 圖片
            self.idle = idle
            self.hover = hover

            # 點擊事件
            self.action = action

            # 狀態
            self.visible = visible
            self.enabled = enabled

            # 判定範圍(需要時才用)
            self.width = width
            self.height = height

            # 額外資訊
            self.tag = tag
            self.examine = examine

            # 除錯模式開關
            self.debug = debug

            # 自訂資料
            self.data = data if data is not None else {}

            # 撿取物品
            self.item = item

            # 點擊音效
            self.sound = sound

            # 文字/emoji 熱點樣式
            self.label = label
            self.label_size = label_size
            self.label_color = label_color
            self.label_hover_color = label_hover_color

            # 點擊前的物品檢查
            self.require_item = require_item
            self.action_if_missing = action_if_missing

        def show(self):
            self.visible = True

        def hide(self):
            self.visible = False

        def enable(self):
            self.enabled = True

        def disable(self):
            self.enabled = False


    def hotspot_action(hotspot):
        # explore() 畫面幫每個熱點的按鈕組 action 時，
        # 都是呼叫這個函式，而不是直接讀 hotspot.action，
        # 這樣才能在「每次點擊當下」即時做檢查，
        # 而不是房間資料建立時 (build_rooms()) 就把結果固定死。
        #
        # v0.1 沒有 inventory，所以這裡一律回傳 hotspot.action。
        # inventory 模組接上後，這裡要加回下面這段：
        #
        #     if hotspot.require_item and not has_all_items(hotspot.require_item):
        #         return hotspot.action_if_missing
        #
        return hotspot.action