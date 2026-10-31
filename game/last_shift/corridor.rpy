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
                )
            ]
        )

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
    "今天是最後一天上班了，我得把三樓那間一直開著門的那間房間打掃乾淨!"
    return

label admin_note:
    call show_pages(ADMIN_NOTE)
    return

label go_living_room:
    "你推開那扇一直開著的門。"
    $ change_room("living_room")
    return

label go_sister_room:
    "(蹲著爬進去)"
    $ change_room("sister_room")
    return

label cantgo_sister_room_dark:
    me "太黑了，我需要照亮的東西"
    me "裡面好可怕"
    return