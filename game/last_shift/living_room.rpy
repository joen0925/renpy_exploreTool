##################################################
# living_room.rpy
#
# 客廳
# 
#
##################################################

init python:
    
    def build_living_room():
        room = Room(
            name="living_room",
            background="images/bg_living_room.png",
            bg_width=2400,
            on_enter="living_room_enter",
            on_enter_limit=1,
            events=[
                Event(
                    id="living_room.door_closes",       # 名字自己取，不能跟別的事件重複
                    trigger=TriggerType.EXIT_ROOM,      # 離開時才觸發
                    limit=None,                         # 每次離開都講
                    effect=Effect(label="living_room_door_closes"),
                ),
                Event(
                    id="living_room.drain",                      # 三間要不一樣
                    condition=Condition(require=["flashlight"]),
                    effect=Effect(actor="player", stats={"battery": -1}),
                    limit=None,                               # 每次進來都扣
                ),
                Event(id="living_room.sister_appears",
                    trigger=TriggerType.TIMER, delay=5,
                    condition=Condition(require=["sister_phone_unlocked"]),
                    effect=Effect(set_flags=["sister_warned"], label="sister_appears")
                ),
            ]
        )

        room.add_event(Event(
            id="living_room.chase",
            condition=Condition(require=["sister_warned"]),
            trigger=TriggerType.TIMER,
            delay=7,
            effect=Effect(
                label="demage_by_father",
                actor="player",
                give_items=[("spare_battery", 1)],
                stats={"hp": -2},
            ),
        ))

        room.add_hotspot(Hotspot(
            name="back_corridor",
            x=705, y=230,
            width=390,height=730,
            on_click="living_room_go_corridor",
        ))
        room.add_hotspot(Hotspot(
            name="safe",
            x=1300, y=330,
            width=200,height=170,
            condition=Condition(forbid=["safe_opened"]),
            on_click="living_room_safe_locked",
        ))
        room.add_hotspot(Hotspot(
            name="drawer",
            x=1880, y=740,
            width=240,height=95,
            on_click="open_drawer",
        ))
        room.add_hotspot(Hotspot(
            name="distribution_box",
            x=2190, y=235,
            width=180,height=285,
            events=[
                Event(
                    id="living_room.distribution_box.take_item",
                    condition=Condition(require=["drawer_key"]),
                    sequence=10,
                    effect=Effect(
                        set_flags=["panel_opened"],
                        give_items=["flashlight",("spare_battery", 5)],
                        actor="player", stats={"battery": +5},
                        label="found_flashlight_spare_battery",
                    ),
                    stop=True,
                    limit=1
                ),
                Event(
                    id="living_room.distribution_box.lock",
                    condition=Condition(forbid=["panel_opened"]),
                    sequence=20,
                    effect=Effect(
                        label="distribution_box_lock",
                    ),
                    limit=None
                ),
                Event(
                    id="living_room.distribution_box.no_item",
                    condition=Condition(require=["panel_opened"]),
                    sequence=20,
                    effect=Effect(
                        label="distribution_box_no_item",
                    ),
                    limit=None
                ),
            ]
        ))
        room.add_hotspot(Hotspot(
            name="flashlight_charge",
            x=1340, y=700,
            label="補充電池",
            condition=Condition(require=["flashlight"]),
            events=[
                Event(
                    id="living_room.charge",
                    sequence=10,                              # 扣電是 0，這個排在後面
                    condition=Condition(
                        require=["spare_battery"],
                        check=lambda s: s.stats("player", "battery") == 0,
                    ),
                    effect=Effect(remove_items=["spare_battery"],
                                actor="player", stats={"battery": +5},
                                label="battery_swapped"),
                    limit=None,
                    stop=True
                ),
                Event(
                    id="living_room.no_charge",
                    sequence=20,                              # 扣電是 0，這個排在後面
                    condition=Condition(
                        require=["spare_battery"],
                        check=lambda s: s.stats("player", "battery") > 0,
                    ),
                    effect=Effect(label="battery_even_full"),
                    limit=None,
                ),
                Event(
                    id="living_room.no_spare_but_lit",
                    sequence=25,
                    condition=Condition(
                        forbid=["spare_battery"],
                        check=lambda s: s.stats("player", "battery") > 0,
                    ),
                    effect=Effect(label="battery_no_spare"),
                    limit=None,
                    stop=True
                ),
                Event(
                    id="living_room.no_battery",
                    sequence=30,
                    condition=Condition(
                        forbid=["spare_battery"],
                        check=lambda s: s.stats("player", "battery") == 0,
                    ),
                    effect=Effect(label="no_battery"),
                    limit=None,
                    stop=True
                ),
                
            ]
        ))
        return room

    def build_drawer_inside():
        room = Room(
            name="drawer_inside",
            background="images/closeup_drawer.png",
            bg_width=1280,
            bg_height=720,          # 近景一定要填
        )
        room.add_hotspot(Hotspot(
            name="key",
            x=900, y=200,
            width=220, height=120,                    # 照原圖比例
            idle="images/item_key.png",
            condition=Condition(forbid=["drawer_key"]),   # 拿過就消失
            events=[Event(id="drawer_inside.take_key",
                        effect=Effect(give_items=["drawer_key"], label="drawer_inside_take_key"))],
        ))
        room.add_hotspot(Hotspot(
            name="note",
            x=300, y=400,
            width=340, height=240,                    # 照原圖比例
            idle="images/item_note.png",
            condition=Condition(forbid=["note"]),   # 拿過就消失
            events=[Event(id="drawer_inside.take_note",
                        effect=Effect(give_items=["note"], label="drawer_inside_take_note"))],
        ))


        return room

##################################################
# 這個房間的 label
##################################################

label living_room_enter:
    "這客廳空得不像有人住過，只剩一張桌子。"
    "等等。"
    "角落那個……是寵物籠嗎？"
    return

label living_room_go_corridor:
    $ change_room("corridor")
    return

label living_room_door_closes:
    "身後傳來「砰」的一聲，門自己關上了。"
    return

label open_drawer:
    "你拉開抽屜。"
    call open_closeup("drawer_inside")
    return

label found_flashlight_spare_battery:
    me "一支手電筒，還有幾顆備用電池。"
    me "有了光，走廊盡頭那個洞應該爬得進去。"
    return

label distribution_box_no_item:
    me "裡面已經空了。"
    return

label distribution_box_lock:
    me "該死，上鎖了。"
    me "鑰匙會放在哪……"
    return

label battery_even_full:
    me "還有電，先不用換。"
    return

label battery_swapped:
    me "換好了。光又回來了。"
    return

label battery_no_spare:
    me "備用電池用完了……剩下的電得省著用。"
    return

label living_room_safe_locked:
    me "保險箱上了鎖，要四位數的密碼。"
    call run_puzzle("safe")
    return

label no_battery:
    me "電池全用完了……"
    me "在這片黑暗裡，我哪裡也去不了。"
    return

label living_room_safe_opens:
    me "我還以為裡面會有錢……"
    me "結果只有一張照片。有必要鎖得這麼嚴嗎？"
    return

label living_room_safe_shock:
    me "好痛！鍵盤裡竟然藏著針……"
    me "按錯就扎手，這家人到底在防誰？"
    return

label drawer_inside_take_key:
    me "一把鑰匙……牌子上寫著「配電」。"
    return

label drawer_inside_take_note:
    me "一張發黃的紙條，摸起來濕濕黏黏的，還有股怪味。"
    return

label sister_appears:
    call show_jumpscare("sister_scare")
    sister "快...逃..爸爸要回來了"
    play music "bgm/halloween_moonlight.mp3" fadein 1.0 volume 0.5
    $ Effect(actor="player", stats={"battery": -99}).apply(game_state)   # 電量歸 0
    me "手電筒...沒電了?!"
    return

label demage_by_father:
    father "誰？！誰在我家裡？！"
    "（刀刃擦過你的手臂。）"
    me "啊——！得快點離開這裡！"
    return