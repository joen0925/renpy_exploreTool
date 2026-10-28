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

# 20 秒那個事件 (playground.ghost_arrives) 要用哪一種演出。
#
#   "approach"   對話模式：鬼從左邊慢慢走到右邊的主角身上（普通的 Ren'Py）
#   "jumpscare"  小鬼撲到全螢幕、視窗自己關掉（通用元件 show_jumpscare）
#
# 兩種都做好了，改這一行就能換。扣的 3 滴血兩邊共用，不會跟著改。
#
# 兩者的差別不只是外觀：
#   approach   能配台詞、能慢慢加壓，但玩家可以用點擊加速跳過
#   jumpscare  長度由設計者決定、點擊也跳不掉，但沒有鋪陳的空間
define PLAYGROUND_GHOST_STYLE = "approach"

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

        # pausable=False 解謎的試玩點。
        #
        # 點下去會開一個密碼鎖，而**解的時候世界不會停** ——
        # 20 秒時下面那個 interrupt=True 的事件會把視窗直接關掉。
        room.add_hotspot(Hotspot(
            name="locker",
            x=600, y=500,
            label="🗃 鎖櫃",
            condition=Condition(forbid=["playground_locker_opened"]),
            on_click="playground_open_locker",
        ))

        room.add_event(Event(
            id="playground.timer_demo",
            trigger=TriggerType.TIMER,
            delay=10,
            effect=Effect(label="playground_timer_demo"),
        ))

        # interrupt=True 的示範：這個事件會「打斷玩家手上的事」。
        #
        # 上面那個腳步聲事件沒有標 interrupt，所以玩家在解謎或翻抽屜時
        # 它會乖乖排隊，等視窗關掉才發生。這一個相反 ——
        # 到點時會把 pausable=False 的解謎視窗與近景視窗當場關掉。
        #
        # 為什麼氣氛台詞不該標 interrupt：把玩家從密碼鎖裡拽出來、
        # 還害他按到一半的號碼全沒了，只為了一句遠處的腳步聲。
        # 「被打斷」要稀有才有意義。
        #
        # sequence 比腳步聲大，所以兩個同時到點時腳步聲先跑
        # (實際上不會同時 —— 腳步聲 10 秒就死了)。
        room.add_event(Event(
            id="playground.ghost_arrives",
            trigger=TriggerType.TIMER,
            delay=20,
            interrupt=True,
            sequence=10,
            effect=Effect(label="playground_ghost_arrives"),
        ))

        return room


label playground_enter:
    "實驗區。這裡的東西隨便改都沒關係。"
    "（在這裡站著別動 10 秒，會有東西自己發生。20 秒時還有一個。）"
    "（右邊的抽屜可以拉開來看 —— 那是近景視窗。）"
    "（鎖櫃解的時候世界不會停，20 秒那個事件會把視窗直接關掉。）"
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


label playground_ghost_arrives:
    # 兩種演出都做了，改這一行就能換 (見檔案最上面的 PLAYGROUND_GHOST_STYLE)
    if PLAYGROUND_GHOST_STYLE == "approach":
        call playground_ghost_approach from _call_pg_ghost_approach
    else:
        call playground_ghost_jumpscare from _call_pg_ghost_jumpscare

    # 演完才扣血。
    #
    # 為什麼扣血寫在這裡、而不是寫在那個 Event 的 Effect 上：
    #
    # 引擎的順序是「先套用 Effect，再跑它帶的 label」(見 collect_events)。
    # 所以血如果掛在 Effect 上，左上角的 ❤️ 會在演出**之前**就少掉 ——
    # 玩家先看到自己掉血，才看到為什麼。
    #
    # 搬到這裡之後順序就對了：演完 → 才扣血。
    # 死亡檢查不受影響，它在整串 label 都跑完之後才做
    # (見 run_event_labels)，所以扣到 0 一樣會走 on_player_death。
    #
    # 放在分支外面是刻意的 —— 兩種演出共用同一個代價，
    # 換演出方式不會不小心改到扣幾滴血。
    $ Effect(actor="player", stats={"hp": -3}).apply(game_state)

    # 收尾的台詞一律排在扣血**之後**。
    #
    # 兩種演出的子 label 都刻意不講收尾的話 —— 中間插一句要等玩家推進的
    # 台詞，就等於把「演完馬上扣血」變成「演完、等玩家按一下、才扣血」。
    # (寫這一版時真的插進去了，測試抓到：視窗關了但血還是 5)
    "牠從你身上穿過去了。"
    "（扣了 3 滴血。這是 interrupt=True 的計時事件：如果你剛剛正在解鎖櫃"
    "或翻抽屜，視窗會被它當場關掉，而血是在演出結束之後才扣的。）"
    return


# 演出 A：小鬼撲到全螢幕，視窗自己關掉。
#
# 刻意不講任何話 —— 收尾的台詞在上面那個 label，排在扣血之後。
label playground_ghost_jumpscare:
    call show_jumpscare("annie scare") from _call_playground_ghost_scare
    return


# 演出 B：對話模式，鬼從左邊慢慢走到右邊的主角身上。
#
# 這一段**完全是普通的 Ren'Py**：show / at / with / 對話。
# 沒有用到工具包的任何新元件 —— 因為「演出」本來就是 Ren'Py 的部門
# (見 effect.rpy 開頭：劇情走 label，不要再實作一套流程控制)。
# 想在別的房間做同樣的事，照抄這個 label 改台詞與位置就好。
#
# ⚠️ 最後一定要 hide。
#    這些立繪畫在 master layer 上，跟房間背景同一層。run_event_labels
#    收尾時只會換畫面 (hide room_background / show explore)，**不會**
#    幫你收立繪 —— 忘記 hide 的話，一隻巨大的 👻 會從此黏在探索畫面上。
label playground_ghost_approach:

    # 主角站在右邊。
    #
    # 想改成第一人稱 (沒有主角立繪、鬼直接朝鏡頭走來)，
    # 把這兩行跟最後那行 hide 刪掉就好，其他完全不用動。
    show me back at stand(0.86, 0.85)
    with dissolve

    "背後有腳步聲。你回過頭。"

    # 第一步：很遠，所以很小。第一次出場用 stand 定位。
    show annie mood at stand(0.06, 0.30)
    with dissolve

    "走廊的另一頭站著一個東西。"

    # 之後每一步只寫目標位置，補間自動從現在的位置開始 (見 characters.rpy 的 step)。
    #
    # 每一步都配一句話，所以「走多快」其實是玩家自己的閱讀速度 ——
    # 動畫在講話的同時進行，讀完這句它剛好走到。
    show annie mood at step(0.30, 0.50, 1.2)
    "它往前了一點。你聽見自己的呼吸聲變大。"

    show annie mood at step(0.55, 0.75, 1.1)
    "近到看得出它沒有臉。"

    show annie mood at step(0.78, 1.15, 0.9)
    "它站到你面前。"

    # 最後一步刻意又快又大 ——
    # 前面慢慢靠近就是為了讓這一下的加速有對比。
    show annie mood at step(0.86, 2.0, 0.22)
    "——"

    hide annie
    hide me
    with dissolve

    return


label playground_open_locker:
    call run_puzzle("playground_locker") from _call_playground_open_locker
    return


label playground_locker_opens:
    "鎖環彈開了。"
    "裡面只有一件疊得很整齊的外套，口袋是空的。"
    return


label playground_locker_wrong:
    "鎖環沒有動。"
    "（答錯不扣血 —— 這個關卡的壓力來自時間。）"
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
