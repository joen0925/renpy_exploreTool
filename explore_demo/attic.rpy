##################################################
# attic.rpy
#
#   第四個示範房間：角色數值 (ActorState) 的示範。
#
#   這裡示範三件事：
#     1. 扣玩家的血 → 對話演完 → 才死亡
#     2. 改別的角色的數值 (安妮的憤怒值)，並用它當熱點的顯示條件
#     3. 「只扣血、不講話」的進房事件
##################################################

init python:

    def build_attic():
        room = Room(
            name="attic",
            background=_build_demo_background(1920, 1080),
            bg_width=1920,
            on_enter="attic_enter",
        )

        room.add_hotspot(Hotspot(
            name="back",
            x=200,
            y=800,
            label="↩ 下樓",
            on_click="attic_go_back",
        ))

        # --- 惹安妮生氣 ---
        #
        # 改的是別的角色的數值，所以要指定 actor。
        room.add_hotspot(Hotspot(
            name="music_box",
            x=900,
            y=520,
            label="🎵 轉動音樂盒",
            events=[
                Event(
                    id="attic.wind_music_box",
                    effect=Effect(
                        actor="annie_ghost",
                        stats={"rage": +1},
                        label="attic_music_box",
                    ),
                    limit=None,
                ),
            ],
        ))

        # --- 憤怒值到 2 才出現的熱點 ---
        #
        # 顯示條件用 check 讀角色數值。跟其他 condition 一樣是唯讀的 ——
        # 這個 lambda 在探索畫面每一幀都會被求值。
        room.add_hotspot(Hotspot(
            name="annie",
            x=1400,
            y=400,
            label="👻 安妮",
            condition=Condition(check=lambda s: s.stats("annie_ghost", "rage") >= 2),
            events=[
                # 憤怒值很高的版本：扣得更兇。
                # sequence 小的先跑，所以暴怒版要排在普通版前面，
                # 再用 stop=True 擋掉後面那個，不然兩個都會扣。
                Event(
                    id="attic.annie_furious",
                    sequence=10,
                    condition=Condition(check=lambda s: s.stats("annie_ghost", "rage") >= 4),
                    effect=Effect(actor="player", stats={"hp": -3}, label="attic_annie_furious"),
                    limit=None,
                    stop=True,
                ),

                Event(
                    id="attic.annie_normal",
                    sequence=20,
                    effect=Effect(actor="player", stats={"hp": -1}, label="attic_annie_attack"),
                    limit=None,
                ),

                # 排在攻擊後面的收尾。
                #
                # 這一段存在的意義不只是演出：它是「扣血之後對話要完整演完
                # 才死亡」的守門員。如果哪天有人把死亡檢查改成
                # 「每跑完一個 label 就檢查」，被打死的那一次就不會跑到這裡，
                # actor_flow 會抓到。
                Event(
                    id="attic.annie_leaves",
                    sequence=30,
                    effect=Effect(label="attic_annie_leaves"),
                    limit=None,
                ),
            ],
        ))

        # --- 只扣血、不講話的進房事件 ---
        #
        # 這個 Effect 沒有 label，所以 collect_events 收集到的清單是空的。
        # 死亡檢查因此不能寫在「有 label 才做」的分支裡 ——
        # 這個熱點就是用來守住那個漏洞的。
        #
        # 條件是「詛咒已經啟動」，預設不會觸發，
        # 免得一般試玩的人走進閣樓就莫名其妙掉血。
        room.add_event(Event(
            id="attic.curse_drain",
            condition=Condition(require=["attic_cursed"]),
            effect=Effect(actor="player", stats={"hp": -1}),
            limit=None,
        ))

        # --- 第 3 次走進閣樓，她就站在門後 ---
        #
        # 「不靠計時器也能突然嚇人」的第一種做法：數次數，不數秒數。
        #
        # 計數器要自己掛一個 —— on_enter 講完開場白就死亡了，數不下去。
        # 計數器的 sequence 比條件事件小，所以「第 3 次」就是真的第 3 次。
        room.add_event(visit_counter("attic.visits"))

        room.add_event(Event(
            id="attic.third_visit_scare",
            condition=Condition(check=count_at_least("attic.visits", 3)),
            effect=Effect(set_flags=["attic_scared"], label="attic_third_visit"),
            limit=1,
        ))

        # --- 點下去完全不講話、只扣血的熱點 ---
        #
        # 這個熱點的事件沒有 label，也沒有 on_click，
        # 所以 _fire_hotspot 交給 run_event_labels 的是一個「空清單」。
        #
        # 死亡檢查如果寫在「有 label 才做」的分支裡，
        # 這個熱點就能把玩家扣到 0 卻什麼事都不發生。
        # silent_death 測的就是它。
        room.add_hotspot(Hotspot(
            name="rusty_nail",
            x=1200,
            y=760,
            label="🩸 生鏽的釘子",
            events=[
                Event(
                    id="attic.rusty_nail",
                    effect=Effect(actor="player", stats={"hp": -1}),
                    limit=None,
                ),
            ],
        ))

        # --- 機率型的嚇人：拉開衣櫃，四次有一次她在裡面 ---
        #
        # 「不靠計時器也能突然嚇人」的第二種做法：骰機率。
        #
        # 兩個事件配成一組：
        #   sequence 小的帶 chance + stop=True —— 骰中就演出，並擋掉後面那個
        #   sequence 大的是保底 —— 骰不中時講一句「什麼都沒有」
        #
        # 保底一定要寫。少了它，骰不中的時候點下去完全沒反應，
        # 玩家會以為這個熱點壞了。
        room.add_hotspot(Hotspot(
            name="wardrobe",
            x=1600,
            y=620,
            label="🚪 破舊的衣櫃",
            events=[
                Event(
                    id="attic.wardrobe_scare",
                    sequence=10,
                    chance=0.25,
                    effect=Effect(set_flags=["attic_scared"], label="attic_wardrobe_scare"),
                    limit=None,
                    stop=True,
                ),
                Event(
                    id="attic.wardrobe_empty",
                    sequence=20,
                    effect=Effect(label="attic_wardrobe_empty"),
                    limit=None,
                ),
            ],
        ))

        room.add_hotspot(Hotspot(
            name="curse_switch",
            x=600,
            y=760,
            label="🕯️ 點燃蠟燭",
            condition=Condition(forbid=["attic_cursed"]),
            events=[
                Event(
                    id="attic.light_candle",
                    effect=Effect(set_flags=["attic_cursed"], label="attic_light_candle"),
                    limit=None,
                ),
            ],
        ))

        room.add_hotspot(Hotspot(
            name="health",
            x=400,
            y=237,
            label="補血!!",
            condition=Condition(check=lambda s: s.stats("player", "hp") <= 2),
            events=[
                Event(
                    id="attic.health",
                    effect=Effect(
                        actor="player",
                        stats={"hp": +1},
                        label="attic_player_health"
                    ),
                    limit=None,
                ),
            ],
        ))

        return room


##################################################
# 這個房間的 label
##################################################

label attic_enter:
    "閣樓裡積滿了灰。角落有一個音樂盒。"
    return

label attic_go_back:
    $ change_room("demo_room")
    return

label attic_music_box:
    "你轉動發條，music box 發出走音的旋律。"
    "空氣冷了一點。"
    return

label attic_annie_attack:
    "有什麼東西從你背後掠過。"
    "你的手臂上多了一道抓痕。"
    return

label attic_annie_furious:
    # 用 annie 這個 Character 講話，對話框上會出現「安妮」。
    #
    # 這個 Character 定義在 characters/annie.rpy，名字只寫在那一個地方。
    # 旁白加引號 ("「……」") 也還是合法的寫法 —— 適合「你看不見的東西
    # 在說話」；有名字適合「她就站在你面前」。
    annie "你為什麼還在這裡。"
    "冰冷的手掐住你的喉嚨。"
    return

label attic_annie_leaves:
    "她的身影融進黑暗裡。"

    # 在 label 裡面改狀態 (而不是用 Effect)，是為了留下一個
    # 「這個 label 的內容真的被執行過」的證據 ——
    # Effect 是在派發的第一階段就套用的，證明不了 label 有沒有跑到。
    $ game_state.flags.set("annie_left")
    return

label attic_light_candle:
    "燭火亮起，牆上的影子開始晃動。"
    "從現在起，每次踏進這個房間都會讓你虛弱一點。"
    return

label attic_player_health:
    "RRRRRRRR，補血!!"
    return

label attic_third_visit:
    "你第三次推開閣樓的門。"
    "這一次，門後面站著一個人。"
    "等你眨完眼，那裡什麼都沒有。"
    return

label attic_wardrobe_scare:
    "你拉開櫃門 ——"
    "一張臉貼在你面前，鼻尖幾乎碰到你的。"
    "再看一眼，櫃子裡是空的。"
    return

label attic_wardrobe_empty:
    "櫃子裡只有幾件發霉的衣服。"
    return