##################################################
# explore_debug.rpy
#
#   標點用的 debug 面板。
#
#   F9  顯示/隱藏面板
#   F10 把目前滑鼠座標「釘住」，方便抄下來寫進 Hotspot(x=..., y=...)
#
#   這個檔案只畫面板，不碰 explore() 的任何渲染邏輯，
#   是疊在探索畫面上面的一層 overlay。
#   (刻意不做成「複製一份 explore() 再加面板」的 debug 版畫面，
#    那樣熱點的顯示邏輯會有兩份，改一邊忘另一邊就會出現
#    「debug 模式正常、正式模式壞掉」這種最難查的問題。)
##################################################

# F10 釘住的滑鼠螢幕座標，還沒釘過時是 None
default debug_pinned_pos = None

# 「重新載入房間資料」的確認狀態
default explore_debug_confirm_reload = False


init python:

    # 按鍵設定。Ren'Py 內建已經佔用 F1/F2/F3/F4/F7/F8/F11，F9/F10 是空的。
    # 想換鍵改這裡就好。
    config.keymap["explore_debug_toggle"] = ["K_F9"]
    config.keymap["explore_debug_pin"] = ["K_F10"]

    # 把接收按鍵的 screen 掛成 overlay，這樣在任何畫面下按 F9 都有效
    # (用 if 擋一下，避免開發時重新載入腳本重複加入同一個名字)
    if "explore_debug_keys" not in config.overlay_screens:
        config.overlay_screens.append("explore_debug_keys")


    def toggle_explore_debug():
        """F9：切換 debug 面板的顯示/隱藏。"""
        if renpy.get_screen("explore_debug"):
            renpy.hide_screen("explore_debug")
        else:
            renpy.show_screen("explore_debug")

        renpy.restart_interaction()


    def pin_debug_pos():
        """
        F10：把目前滑鼠位置釘住。

        用按鍵而不是用點擊來記錄座標，是因為想標的位置常常就在某個熱點附近，
        點下去會直接觸發那個熱點跳出對話。用按鍵就不會誤觸。

        重點：房間座標必須在「按下去的當下」就換算好存起來。
        只存螢幕座標、事後在畫面上用當下的 camera.offset 去換算是錯的 ——
        鏡頭隨著滑鼠一直在動，offset 一直變，
        換算出來的房間座標就會跟著跳，等於根本沒釘住。
        """
        mouse_x, mouse_y = renpy.get_mouse_pos()
        room_x = mouse_x - int(camera.offset)

        store.debug_pinned_pos = (mouse_x, mouse_y, room_x)
        renpy.restart_interaction()


    def reload_rooms():
        """
        重新執行內容層的 build_rooms()，用新的房間資料取代現有的。

        為什麼需要這個：rooms 是用 default 宣告的，會存進存檔。
        所以改完 hotspot 座標之後，讀舊存檔還是舊座標，
        本來得回標題重開新遊戲才吃得到 —— 標點是個反覆微調的過程，
        每次都重開太慢。

        注意這會把所有 Room / Hotspot 物件整個重建，
        遊戲中改過的狀態 (例如某個 hotspot.visible 被設成 False) 會全部回到初始值。
        """
        # 房間清單屬於遊戲內容，引擎這邊只約定它叫 build_rooms
        builder = getattr(store, "build_rooms", None)

        if builder is None:
            renpy.notify("找不到 build_rooms()，無法重新載入")
            return

        current_name = store.current_room.name if store.current_room else None

        store.rooms = builder()

        # 盡量留在同一個房間
        if current_name and current_name in store.rooms:
            store.current_room = store.rooms[current_name]
            camera.enter_room(store.current_room)

        renpy.notify("房間資料已重新載入")
        renpy.restart_interaction()


# 只負責接收按鍵，沒有任何視覺。掛在 config.overlay_screens 上全域常駐。
screen explore_debug_keys():
    key "explore_debug_toggle" action Function(toggle_explore_debug)
    key "explore_debug_pin" action Function(pin_debug_pos)


screen explore_debug():
    # 疊在探索畫面上面
    zorder 100

    # 自己更新，不依賴 explore() 的 timer。
    # 不然對話進行中 (explore 被 say_in_room 收起來時) 面板的座標會凍住。
    # 20fps 對讀座標來說夠用，不需要跟 explore() 一樣 60fps。
    timer 0.05 repeat True action NullAction()

    $ mouse_x, mouse_y = renpy.get_mouse_pos()
    $ cam_offset = int(camera.offset)

    # 房間座標 = 螢幕座標 - 鏡頭位移。
    # 這就是要填進 Hotspot(x=..., y=...) 的數字。
    $ room_x = mouse_x - cam_offset

    frame:
        xpos 20
        ypos 20
        background "#000000cc"
        padding (18, 14)

        vbox:
            spacing 6

            text "=== 標點 Debug 面板 (F9 關閉) ===":
                size 18
                color "#00ff00"
                bold True

            if current_room:
                text "房間: [current_room.name]  (bg_width=[current_room.bg_width])":
                    size 15
                    color "#88ff88"
            else:
                text "房間: 尚未進入任何房間":
                    size 15
                    color "#ff4444"

            text "鏡頭 camera.offset: [cam_offset]":
                size 15
                color "#aaaaaa"

            null height 6

            text "滑鼠螢幕座標: [mouse_x], [mouse_y]":
                size 16
                color "#ffffff"

            text "滑鼠房間座標: [room_x], [mouse_y]":
                size 20
                color "#ffff00"
                bold True

            null height 6

            if debug_pinned_pos is not None:
                # 房間座標是按 F10 當下就算好存進來的，這裡不重算
                $ pinned_x, pinned_y, pinned_room_x = debug_pinned_pos

                text "釘住的螢幕座標: [pinned_x], [pinned_y]":
                    size 15
                    color "#00ffff"

                text "釘住的房間座標: [pinned_room_x], [pinned_y]":
                    size 20
                    color "#ff8800"
                    bold True
            else:
                text "按 F10 可以釘住目前座標":
                    size 15
                    color "#888888"

            null height 10

            # 重新載入：按下去先問一次，避免玩到一半誤觸把狀態洗掉
            if explore_debug_confirm_reload:
                text "重新載入會重設所有房間狀態，確定？":
                    size 15
                    color "#ff8800"

                hbox:
                    spacing 20

                    textbutton "確定重新載入":
                        text_size 15
                        text_color "#ff4444"
                        text_hover_color "#ffffff"
                        action [
                            SetVariable("explore_debug_confirm_reload", False),
                            Function(reload_rooms),
                        ]

                    textbutton "取消":
                        text_size 15
                        text_color "#888888"
                        text_hover_color "#ffffff"
                        action SetVariable("explore_debug_confirm_reload", False)

            else:
                textbutton "重新載入房間資料":
                    text_size 15
                    text_color "#00ffff"
                    text_hover_color "#ffffff"
                    action SetVariable("explore_debug_confirm_reload", True)
