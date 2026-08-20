##################################################
#
#	互動點
# 	屬性:背景、大小、各種hotspots位置
#   方法:顯示、隱藏、可用、不可用
#
#   點擊行為有兩種寫法，簡單的用 on_click，需要條件分支的用 events：
#
#     # 點一下講句話
#     Hotspot(name="sign", x=520, y=500, label="🪧 讀看板",
#             on_click="demo_look_sign")
#
#     # 有鑰匙才開得了門
#     Hotspot(name="door", x=800, y=400,
#             events=[
#                 Event(id="hall.door_open",
#                       condition=Condition(require=["key"]),
#                       effect=Effect(set_flags=["door_opened"], label="open_door"),
#                       stop=True),
#                 Event(id="hall.door_locked",
#                       effect=Effect(label="door_is_locked"), limit=None),
#             ])
#
#   兩者的差別不只是寫法：
#     on_click  每次點都執行，沒有條件也沒有次數限制 (就是原本 action 的角色)
#     events    有條件、有次數、會依 sequence 排序，狀態記在 GameState
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

            # 點一下要跑的 label 名稱 (字串)。簡寫，等同於「無條件、每次都執行」。
            on_click=None,

            # 完整的事件清單，需要條件分支或次數限制時用。
            # 裡面的 Event 沒指定 trigger 的話，預設是 CLICK_HOTSPOT。
            events=None,

            # 顯示條件 (Condition)。條件不成立時這個熱點不會出現在畫面上。
            #
            # 用條件推導而不是命令式的 hide()，好處是冪等：
            #   Hotspot(..., condition=Condition(forbid=["key"]))
            # 撿走鑰匙後這個熱點自動消失，不管讀哪個存檔、reload 幾次都一致。
            # 命令式的 hide() 得靠「當初有沒有正確執行過」來維持狀態。
            condition=None,

            visible=True,
            enabled=True,

            width=None,
            height=None,

            tag=None,
            examine=None,

            data=None,
            debug=False,

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
        ):
            # 基本資訊
            self.name = name

            # 位置 (背景圖座標，不是螢幕座標；顯示時由外層容器統一做鏡頭位移)
            self.x = x
            self.y = y

            # 圖片
            self.idle = idle
            self.hover = hover

            # 點擊行為
            self.on_click = on_click
            self.events = list(events) if events else []

            # 顯示條件
            self.condition = condition

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

            # 點擊音效
            self.sound = sound

            # 文字/emoji 熱點樣式
            self.label = label
            self.label_size = label_size
            self.label_color = label_color
            self.label_hover_color = label_hover_color

        def add_event(self, event):
            self.events.append(event)

        def show(self):
            self.visible = True

        def hide(self):
            self.visible = False

        def enable(self):
            self.enabled = True

        def disable(self):
            self.enabled = False


    def hotspot_is_shown(hotspot):
        """
        這個熱點現在該不該出現在畫面上。

        visible 是手動開關，condition 是由遊戲狀態推導的條件，兩個都要成立。

        注意這個函式會在探索畫面「每一幀」被呼叫 (畫面每 16ms 重繪一次)，
        所以它必須是唯讀的 —— Condition 只拿得到 StateView，
        結構上就改不到任何狀態。
        """
        if not hotspot.visible:
            return False

        if hotspot.condition is None:
            return True

        return hotspot.condition.test(store.game_state.view())


    def hotspot_action(hotspot):
        """
        探索畫面幫每個熱點的按鈕組 action 時呼叫這個。

        點擊的實際處理在 label _fire_hotspot 裡 ——
        因為事件可能要跑好幾個 label，而 screen action 裡沒辦法連續跳轉。
        """
        return Call("_fire_hotspot", hotspot)


# 點擊熱點的入口。
#
# 先用純 Python 收集要跑的 label (檢查條件、改狀態)，
# 再交給 run_event_labels 依序執行。
label _fire_hotspot(hotspot):
    python:
        _ctx = EventContext(store.game_state, store.current_room)

        _labels = collect_events(
            hotspot.events,
            TriggerType.CLICK_HOTSPOT,
            _ctx,
            TriggerType.CLICK_HOTSPOT,
        )

        # on_click 是簡寫，沒有條件也沒有次數限制，永遠排在 events 後面執行
        if hotspot.on_click:
            _labels.append(hotspot.on_click)

    call run_event_labels(_labels) from _call_fire_hotspot

    return
