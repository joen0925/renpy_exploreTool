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

    def _build_closeup_background(width, height, caption, color):
        """
        近景示範用的假背景，不需要任何美術檔案。

        跟 _build_demo_background 一樣用 Solid / Text 拼出來，
        但畫成「框」的尺寸而不是整個螢幕寬，而且每 200px 一條 ——
        近景的框比房間窄很多，刻度太疏會看不出座標。
        """
        parts = [(width, height)]
        parts += [(0, 0), Transform(Solid(color), xysize=(width, height))]

        for x in range(0, width, 200):
            parts += [(x, 0), Transform(Solid("#00000022"), xysize=(100, height))]
            parts += [(x + 8, 12), Text(str(x), size=28, color="#ffffff55")]

        parts += [(40, height - 70), Text(caption, size=36, color="#ecf0f1")]

        return Composite(*parts)


    def build_playground_drawer():
        """
        近景視窗的示範：實驗區那個抽屜的內部。

        這是一個**普通的 Room**，差別只在它不會被 change_room() 進去，
        而是由 open_closeup("playground_drawer") 畫成一個框。

        看這個範例要注意的重點：底圖的條件與熱點的條件是
        **同一件事的兩面** —— 照片在不在物品欄裡。
        所以不可能出現「空抽屜裡還有一張點得到的照片」。
        """
        return Room(
            name="playground_drawer",

            # 照片被拿走之後換成空抽屜的圖。
            # 條件由上往下試，第一個成立的就贏 (見 state_image.rpy)。
            background=state_image(
                (
                    Condition(require=["torn_photo"]),
                    _build_closeup_background(1280, 720, "抽屜裡面（空了）", "#4a3b2a"),
                ),
                default=_build_closeup_background(1280, 720, "抽屜裡面", "#6b5436"),
            ),

            # 框的大小。近景一定要填 bg_height，不填會被 closeup_misuse 擋下來。
            bg_width=1280,
            bg_height=720,

            hotspots=[
                # 照片：還沒拿走才看得到。
                #
                # 熱點座標是「框裡面的座標」，不是房間座標 ——
                # 所以 F9 標點面板的數字不能直接抄到這裡。
                Hotspot(
                    name="photo",
                    x=420, y=300,
                    label="🖼 撕成兩半的照片",
                    condition=Condition(forbid=["torn_photo"]),
                    events=[Event(
                        id="playground_drawer.take_photo",
                        effect=Effect(
                            give_items=["torn_photo"],
                            label="playground_drawer_take_photo",
                        ),
                    )],
                ),

                # 抽屜的底板：怎麼點都在，拿來示範「看細節」。
                # 每次都講同一句話，所以用 on_click 簡寫就夠了。
                Hotspot(
                    name="lining",
                    x=120, y=560,
                    label="🔍 抽屜底板",
                    on_click="playground_drawer_lining",
                ),
            ],
        )


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

        # 計時事件 (TriggerType.TIMER) 的示範：
        # 進這個房間 10 秒後自動發生，不用點任何東西。
        #
        # 倒數從進房間開始算，換房間會重新計時 (走出去再進來就重新算 10 秒)。
        # 對話、翻頁視窗、系統選單期間時鐘是暫停的；解謎視窗**不**暫停。
        #
        # limit 只能是 1 (預設值)，所以整場遊戲只會發生一次 ——
        # 想再看一次要開新遊戲。理由見 Event._validate_delay 的註解。
        # 近景視窗 (open_closeup) 的試玩點。
        #
        # 點下去會跳出一個框顯示抽屜內部，框裡面可以點。
        # 拿走裡面的照片之後，抽屜的底圖會跟著變成空的。
        room.add_hotspot(Hotspot(
            name="drawer",
            x=1600, y=600,
            label="🗄 抽屜",
            on_click="playground_open_drawer",
        ))

        room.add_event(Event(
            id="playground.timer_demo",
            trigger=TriggerType.TIMER,
            delay=10,
            effect=Effect(label="playground_timer_demo"),
        ))

        return room


label playground_enter:
    "實驗區。這裡的東西隨便改都沒關係。"
    "（在這裡站著別動 10 秒，會有東西自己發生。）"
    "（右邊的抽屜可以拉開來看 —— 那是近景視窗。）"
    return


label playground_timer_demo:
    "背後傳來腳步聲。"
    "（這是計時事件：進房間 10 秒後自動觸發，你沒有點任何東西。）"
    return

label playground_open_drawer:
    # 近景是從這裡叫出來的，所以「打開抽屜」這句話要寫在呼叫之前 ——
    # 近景房間寫 on_enter 是沒有用的 (closeup_misuse 會擋下來)。
    "你拉開抽屜。"
    call open_closeup("playground_drawer") from _call_playground_open_drawer
    "你把抽屜推回去。"
    return


label playground_drawer_take_photo:
    "你把照片收進口袋。"
    "（這是近景視窗：框消失、講話、框再回來——而照片已經不在抽屜裡了。）"
    return


label playground_drawer_lining:
    "底板翹起一角，下面什麼都沒有。"
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
