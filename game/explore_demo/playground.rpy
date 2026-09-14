##################################################
# playground.rpy —— 實驗區
#
#   拿來試東西的房間，隨便改都沒關係。
#
#   其他 demo 房間 (demo_room / kitchen / attic) 是給人照抄的教學範例，
#   所以盡量保持乾淨；想實驗新寫法就丟這裡。
#
#   座標怎麼填：進遊戲按 F9 開標點面板，滑鼠移到想放的位置按 F10 釘住，
#   抄「釘住的房間座標」。
#
#   完整說明見 game/libs/explore/DEVELOPER_GUIDE.md
##################################################

init python:

    def build_playground():
        room = Room(
            name="playground",
            # bg_width 一定要跟背景圖的實際寬度一樣。
            #
            # 兩邊對不上的話不會出錯，但探索畫面是用 xsize bg_width 畫背景的，
            # 圖會被橫向拉伸 —— 背景上印的座標數字就會失準
            # (標著 400 的地方實際跑到 x=500)，F9 標點跟著對不上。
            background=_build_demo_background(2400, 1080),
            bg_width=2400,
            on_enter="playground_enter",
        )


        room.add_hotspot(Hotspot(
            name="exit",
            x=200, y=700,
            label="↩ 離開",
            on_click="playground_leave",
        ))

        # 九宮格解鎖 (PatternPuzzle) 的試玩點。
        #
        # 解開之後熱點不消失，想重玩就再點一次。
        room.add_hotspot(Hotspot(
            name="old_phone",
            x=1000, y=500,
            label="📱 舊手機",
            on_click="playground_open_phone",
        ))

        return room


label playground_enter:
    "實驗區。這裡的東西隨便改都沒關係。"
    return

label playground_open_phone:
    call run_puzzle("playground_phone") from _call_playground_open_phone
    return

label playground_phone_unlocked:
    "螢幕亮了起來。"
    "桌布是一張全家福，只有一個人的臉被刮花了。"
    return

label playground_leave:
    $ change_room("demo_room")
    return

label playground_phone_wrong:
    "螢幕震了一下。"
    "「圖形錯誤，請再試一次。」"
    return
