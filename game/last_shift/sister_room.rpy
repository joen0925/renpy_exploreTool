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
                ),
                Event(
                    id="sister_room.ending",
                    condition=Condition(require=["sister_warned"]),
                    effect=Effect(kill_events=["living_room.chase", "corridor.chase"],
                    label="true_ending")
                ),                
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
    me "終於爬進來了……"
    me "好臭。又悶又濕。"
    me "刺鼻的味道黏在皮膚上，汗一直流，怎麼擦都擦不乾。"
    return

label sister_room_go_corridor:
    $ change_room("corridor")
    return

label sister_phone_unlocked:
    me "一通未接來電……？"
    me "回撥看看好了。這家人到底怎麼回事……"
    "（嘟——嘟——）"
    me "……響了兩聲，被掛斷了。"
    me "還是報警吧。可是這裡收不到訊號，得先出去。"
    return

label sister_phone_wrong:
    me "不對……圖形到底是什麼？"
    me "螢幕上的油漬，像是有人往誰的臉上狠狠劃了一刀。"
    return

label sister_room_old_phone:
    call run_puzzle("sister_phone")
    return

## 真結局
label true_ending:
    show father_stand at stand(0.5, 0.3)      # 遠、小
    with dissolve

    # 配音檔放 game/audio/，一句一個檔，照 father_01、father_02… 編號。
    voice "audio/father_01.m4a"
    father "喔……妹……妹妹！妳回來啦，寶貝～"

    show father_stand at step(0.5, 0.6, 1.2)  # 走近
    voice "audio/father_02.m4a"
    father "回來就好……回來就好……"           # (哭泣)

    show father_stand at step(0.5, 0.9, 1.6)  # 走近
    voice "audio/father_03.m4a"
    father "過來給爸爸抱抱，快來，寶貝……"

    me "不要！不要啊啊啊啊啊——"

    hide father_stand                          # ⚠️ 一定要 hide
    "他抓住了你。在他眼裡，回來的是他的女兒。"
    "從那天起，你成了妹妹的替代品——被關進客廳角落的寵物籠裡。"
    "直到……警察到來的那一天。"
    "謝謝遊玩！"
    $ renpy.full_restart()

