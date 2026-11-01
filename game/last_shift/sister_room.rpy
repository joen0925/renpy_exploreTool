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
            background="images/bg_sister_room.png",
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
            x=840, y=870,
            width=130,height=87,
            on_click="sister_room_go_corridor",
        ))

        room.add_hotspot(Hotspot(
            name="sister_phone",
            x=1210, y=410,
            width=80,height=175,
            condition=Condition(forbid=["sister_phone_unlocked"]),
            on_click="sister_room_old_phone",
        ))

        return room

##################################################
# 這個房間的 label
##################################################

label sister_room_enter:
    me "終於爬進來了"
    me "好臭，好悶，好潮濕"
    me "這裡的味道好刺鼻，我已經流汗了，身體比平常黏"
    return

label sister_room_go_corridor:
    $ change_room("corridor")
    return

label sister_phone_unlocked:
    me "未接來電?"
    me "來試著回電好了，這家住戶是怎樣..."
    me "打不通，還是打給警察好了，可是這邊沒信號，得趕快出去"
    return

label sister_phone_wrong:
    me "密碼到底多少啊?"
    me "看這油漬，似乎對家人是有怨恨的"
    return

label sister_room_old_phone:
    call run_puzzle("sister_phone")
    return