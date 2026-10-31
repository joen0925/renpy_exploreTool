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
                )
            ]
        )
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
            on_click="living_room_safe_locked",
        ))
        room.add_hotspot(Hotspot(
            name="drawer",
            x=1880, y=740,
            width=240,height=95,
            condition=Condition(forbid=["drawer_key"]),
            events=[
                Event(
                    id="living_room.open_drawer",
                    sequence=10,
                    effect=Effect(
                        label="open_drawer",
                    ),
                    
                ),
                Event(
                    id="living_room.take_item",
                    sequence=20,
                    effect=Effect(
                        give_items=["drawer_key","note","photo"],
                        label="found_item",    
                    ),
                ),
            ]
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

##################################################
# 這個房間的 label
##################################################

label living_room_enter:
    "這客廳也太簡陋了吧，只有一張桌子和桌子!"
    "等等!"
    "那是寵物籠嗎?"
    return

label living_room_go_corridor:
    $ change_room("corridor")
    return

label living_room_door_closes:
    "身後傳來「砰」的一聲，門自己關上了。"
    return

label open_drawer:
    "打開抽屜"
    return

label found_item:
    me "裡面有好多東西喔，拿都拿"
    return

label found_flashlight_spare_battery:
    me "找到電池和手電筒了，走廊上似乎有個洞可以進去"
    return

label distribution_box_no_item:
    me "沒有東西了"
    return

label distribution_box_lock:
    me "該死，有鎖頭"
    return

label battery_even_full:
    me "電池還有電，不用換"
    return

label battery_swapped:
    me "換好電池了"
    return

label battery_no_spare:
    me "備用電池用完了，剩下的電要省著點用"
    return

label living_room_safe_locked:
    me "保險箱鎖著，要輸入密碼"
    return

label no_battery:
    me "沒電池了，好像只能重玩了"
    return