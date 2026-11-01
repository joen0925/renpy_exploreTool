##################################################
# corridor.rpy
#
# 管理員走廊
# 
#
##################################################

init python:
    
    def build_corridor():
        room = Room(
            name="corridor",
            background="images/bg_corridor.png",
            bg_width=3200,
            on_enter="corridor_enter",
            events=[
                Event(
                    id="corridor.drain",                      # 三間要不一樣
                    condition=Condition(require=["flashlight"]),
                    effect=Effect(actor="player", stats={"battery": -1}),
                    limit=None,                               # 每次進來都扣
                ),
                Event(
                    id="corridor.hear_something",
                    condition=Condition(require=["sister_phone_unlocked"]),
                    trigger=TriggerType.ENTER_ROOM,
                    effect=Effect(label="sister_phone_unlocked_hear_something"),
                ),
            ]
        )
        room.add_event(Event(
            id="corridor.chase",
            condition=Condition(require=["sister_warned"]),
            trigger=TriggerType.TIMER,
            delay=2,
            effect=Effect(
                label="demage_by_father",
                actor="player",
                stats={"hp": -3},
            ),
        ))

        room.add_hotspot(Hotspot(
            name="sign",
            x=580, y=320,
            width=440,height=300,
            on_click="admin_note",
        ))

        room.add_hotspot(Hotspot(
            name="door_living",
            x=1370, y=205,
            width=460,height=745,
            on_click="go_living_room",
        ))

        room.add_hotspot(Hotspot(
            name="hole_sister",
            x=2750, y=835,
            width=150,height=120,
            events=[
                Event(
                    id="corridor.hole_lit",
                    condition=Condition(check=lambda s: s.stats("player", "battery") > 0),
                    effect=Effect(label="go_sister_room"),
                    sequence=10,
                    stop=True,
                    limit=None,
                ),
                Event(
                    id="corridor.hole_dark",
                    effect=Effect(label="cantgo_sister_room_dark"),
                    sequence=20,
                    limit=None,
                )
            ]
            
        ))
    
        return room
##################################################
# 翻頁視窗的內容
##################################################

define ADMIN_NOTE = [
    {
        "title": "管理員須知",
        "text": "1.每日定時巡視各樓層與公設。\n2.保持大廳整潔並禮貌接待訪客。\n3.3樓某房間曾有異樣，勿多問。",
    }
]

##################################################
# 這個房間的 label
##################################################

label corridor_enter:
    "最後一班了。"
    "只要把三樓那戶清空——就是門從上個月起一直開著的那間——這棟樓就跟我沒關係了。"
    return

label admin_note:
    call show_pages(ADMIN_NOTE)
    return

label go_living_room:
    "你推開那扇一直開著的門。"
    $ change_room("living_room")
    return

label go_sister_room:
    "（你蹲下身，從洞口爬了進去。）"
    $ change_room("sister_room")
    return

label cantgo_sister_room_dark:
    me "裡面一片漆黑，什麼都看不見。"
    me "沒有光的話……我可不想把頭伸進去。"
    return


label sister_phone_unlocked_hear_something:
    "（嘶……嘶嘶……）"
    me "客廳那邊有聲音……"
    me "好像是從那個籠子傳出來的。"
    return