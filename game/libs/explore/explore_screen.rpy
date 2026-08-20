##################################################
# explore_screen.rpy
#
#   探索畫面
##################################################

# 只顯示房間背景、沒有任何按鈕/熱點的畫面。
# 給對話還沒結束、但想先讓背景是該房間畫面的情況使用 (例如開場白)，
# 因為 explore() 裡的熱點按鈕會蓋住整個畫面、搶走點擊，
# 導致對話點不下去，所以對話進行時不能直接顯示那個互動用的畫面。
screen room_background():
    # 放在 master layer (跟 show 角色圖片同一層)，而不是 screen 預設的 screens layer。
    # screens layer 永遠畫在 master 上面，如果背景留在 screens layer，
    # 對話中用 show 顯示的立繪 (畫在 master layer) 就會被這個全螢幕背景整個蓋住。
    # 放到同一層之後，誰先 show 誰在下面，room_background 先顯示、立繪後顯示，順序就對了。
    layer "master"

    # current_room 理論上這時一定有值，但保險起見擋一下，
    # 避免極端情況 (例如剛好卡到倒帶/重新整理的瞬間) 直接讓遊戲當掉
    if current_room:
        fixed:
            xpos int(camera.offset)
            ypos 0

            add current_room.background:
                xsize current_room.bg_width
                ysize config.screen_height


screen explore():

    # 鏡頭的動力來源：每 0.016 秒 (約 60fps) 更新一次 camera.offset。
    # 這個 timer 同時也會重新整理整個畫面，
    # 讓下面那些每幀重算的 hover 判定能跟著更新。
    timer 0.016 repeat True action Function(camera.update)

    if current_room:
        # 抓取目前滑鼠的即時座標 (螢幕座標與房間相對座標)，給下面的 hover 判定用
        $ mouse_x, mouse_y = renpy.get_mouse_pos()
        $ room_x = mouse_x - int(camera.offset)

        # 用 fixed 容器包住背景與熱點，統一做相機位移 (xpos)
        fixed:
            xpos int(camera.offset)
            ypos 0

            # 1. 顯示背景：強制將高度鎖定為螢幕高度，寬度為房間真實寬度
            add current_room.background:
                xsize current_room.bg_width
                ysize config.screen_height # 自動抓取遊戲設定高度 (通常是 1080)

            # 2. 顯示熱點：可以直接使用絕對座標 hotspot.x / hotspot.y
            # 不需要手動加 camera.offset，因為外層的 fixed 已經幫忙位移了！
            for hotspot in current_room.hotspots:
                # 取得熱點寬高（若未指定則預設 100x100）
                $ w = hotspot.width if hotspot.width else 100
                $ h = hotspot.height if hotspot.height else 100

                # visible 是手動開關，condition 是由遊戲狀態推導的顯示條件，
                # 兩個都成立才畫出來。condition 只讀不寫，每幀求值也安全。
                if hotspot_is_shown(hotspot):
                    if hotspot.label:
                        # 文字/emoji 熱點 (例如撿取物品用的 "🔑 點我拿取鑰匙")
                        textbutton hotspot.label:
                            xpos hotspot.x
                            ypos hotspot.y
                            text_size hotspot.label_size
                            text_color hotspot.label_color
                            text_hover_color hotspot.label_hover_color
                            activate_sound hotspot.sound
                            action hotspot_action(hotspot)
                    else:
                        # 判定範圍：永遠存在，負責點擊 action 與 debug 紅框
                        # (不依賴 imagebutton 內建的 hover 機制，因為鏡頭是靠 timer 每幀自己位移，
                        #  滑鼠沒動時不會產生新的滑鼠事件，內建 hover 會卡住不更新)
                        button:
                            xpos hotspot.x
                            ypos hotspot.y
                            xsize w
                            ysize h
                            # 根據 debug 屬性決定背景顏色 (True 顯示紅框，False 完全透明)
                            background ("#ff000055" if hotspot.debug else None)
                            activate_sound hotspot.sound
                            action hotspot_action(hotspot)

                        # 靜態圖示 (idle)：只要熱點可見就一直顯示，縮放貼滿 width x height
                        if hotspot.idle:
                            add Transform(hotspot.idle, xysize=(w, h)):
                                xpos hotspot.x
                                ypos hotspot.y

                        # hover 圖示：每一幀都用「目前滑鼠的房間座標」即時判定是否落在範圍內
                        # 鏡頭移動或滑鼠離開，下一幀就會馬上消失，不會卡住
                        if hotspot.hover and (hotspot.x <= room_x < hotspot.x + w) and (hotspot.y <= mouse_y < hotspot.y + h):
                            add Transform(hotspot.hover, xysize=(w, h)):
                                xpos hotspot.x
                                ypos hotspot.y

    # 右上角物品欄。放在 fixed 外面，所以不會跟著鏡頭移動。
    # (左上角留給 F9 的 debug 標點面板)
    use inventory_display