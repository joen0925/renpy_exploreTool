init python:

    def build_bed_room():
        room = Room(
            name="bed_room",
            background=_build_demo_background(2400, 1080),
            bg_width=2400,
        )

        room.add_hotspot(Hotspot(
            name="bed",
            x=800,
            y=265,
            width=200,
            height=200,
            label="bed",            
            events=[
                Event(
                    id="bed_room.take_coin10",
                    condition=Condition(forbid=["coin10"]),
                    sequence=10,
                    effect=Effect(
                        set_flags=["had_coin10"],
                        give_items=[("coin10", 10)],
                        label="found_coin10",
                    ),
                    stop=True,
                ),

                Event(
                    id="bed_room.sleep",
                    condition=Condition(require=["had_coin10"]),
                    sequence=20,
                    effect=Effect(                        
                        label="sleep",
                    ),
                    limit=None,
                ),
            ]
        ))

        room.add_hotspot(Hotspot(
            name="drink_box",
            x=2000,
            y=265,
            width=200,
            height=200,
            label="drink_box",
            events=[
                Event(
                    id="use_drink_box",
                    condition=Condition(check=lambda v: v.item_count("coin10") > 5),
                    effect=Effect(
                        remove_items=[("coin10", 5)],
                        label="drink_box_cost",
                    ),
                    limit=None,
                    stop=True,
                ),
                Event(
                    id="dont_had_coin10",
                    sequence=10,
                    effect=Effect(
                        label="no_money",
                    ),
                    limit=None,
                ),
            ]
        ))
       


        room.add_hotspot(Hotspot(
            name="to_demo_room",
            x=1500,
            y=880,
            label="返回demo room",
            on_click="bed_room_to_demo_room",
        ))

        return room


##################################################
# 這個房間的 label
##################################################

label bed_room_to_demo_room:
    "你返回了demo room"
    $ change_room("demo_room")
    return

label goto_bed:
    "這床真舒服"
    "?"
    "好像有東西"
    return

label found_coin10:
    "喔幹是10元硬幣，竟然還有10個"
    "撿起來"
    return

label sleep:
    "來睡個覺"
    return

label drink_box_cost:
    "好貴喔50元"
    return

label no_money:
    "要50元，我的錢不夠"
    return