##################################################
# status_display.rpy
#
#   狀態欄畫面：把玩家的角色數值 (血量、體力、電池量……) 顯示在左上角。
#
#   用法：在探索畫面裡加一行
#       use status_display
#
#   顯示哪些數值「不是」由引擎決定 —— 引擎不知道你的遊戲有哪些數值，
#   也不該知道 rage 這種鬼的內部計數器不能給玩家看。
#   所以清單由遊戲內容那邊宣告，例如在 actors.rpy：
#
#       define player_status_display = [
#           {"stat": "hp",      "icon": "❤️"},
#           {"stat": "battery", "icon": "🔦", "name": "電量"},
#       ]
#
#   沒宣告的話狀態欄整個不顯示，不會出錯。
#
#   位置在左上角，跟 F9 的 debug 標點面板重疊 ——
#   那是刻意的：debug 面板只在開發時開，正式環境用不到，蓋住無所謂。
##################################################

init python:

    def player_status_rows():
        """
        狀態欄現在該顯示哪幾列，回傳 [(圖示, 名稱, 數值), ...]。

        兩層過濾：
        1. 只顯示 player_status_display 列出來的數值 (內容層決定)
        2. 其中「沒有被設定過」的跳過 —— 跟 ActorState.is_dead() 同一個約定：
           沒設過就是這個角色沒有這個概念，不是「有但等於 0」。
           這樣沒拿到手電筒的時候不會出現一列「🔦 0」。
        """
        rows = []

        for entry in getattr(store, "player_status_display", []):
            stat = entry.get("stat")

            if not stat or not store.game_state.actors.has_stat(PLAYER_ACTOR, stat):
                continue

            rows.append((
                entry.get("icon", ""),
                entry.get("name", ""),
                store.game_state.actors.get(PLAYER_ACTOR, stat),
            ))

        return rows


screen status_display():

    $ _status_rows = player_status_rows()

    # 一列都沒有就整個不畫，不要留一個空框在畫面上
    if _status_rows:

        frame:
            xalign 0.0
            xoffset 20
            yalign 0.0
            yoffset 20
            padding (16, 12)
            background "#000000aa"

            vbox:
                spacing 6

                text "【狀態】":
                    size 20
                    color "#aaaaaa"

                for _icon, _name, _value in _status_rows:
                    hbox:
                        spacing 8

                        if _icon:
                            text "[_icon]":
                                size 22

                        if _name:
                            text "[_name]":
                                size 22
                                color "#aaaaaa"

                        text "[_value]":
                            size 22
                            color "#e74c3c"
