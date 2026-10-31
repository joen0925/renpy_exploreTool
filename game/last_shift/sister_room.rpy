##################################################
# sister_room.rpy
#
# 妹妹的房間
# 
#
##################################################

init python:

    def build_sister_room():
        room = Room(
            name="sister_room",
            background=_build_demo_background(1920, 1080),
            bg_width=1920,
            on_enter="sister_room_enter",
            on_enter_limit=1,
            events=[
                Event(
                    id="sister_room.drain",                      # 三間要不一樣
                    condition=Condition(require=["flashlight"]),
                    effect=Effect(actor="player", stats={"battery": -1}),
                    limit=None,                               # 每次進來都扣
                )
            ]
        )

        room.add_hotspot(Hotspot(
            name="back_corridor",
            x=900, y=820,
            label="走廊",
            on_click="sister_room_go_corridor",
        ))

        return room

##################################################
# 這個房間的 label
##################################################

label sister_room_enter:
    "終於爬進來了"
    "這裡只有點燃的蠟燭，怎麼感覺涼涼的"
    return

label sister_room_go_corridor:
    $ change_room("corridor")
    return