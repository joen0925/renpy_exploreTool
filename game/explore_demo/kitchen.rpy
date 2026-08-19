##################################################
# kitchen.rpy
#
#   第二個示範房間：用來驗證房間之間的切換。
#   這個檔案是照著 game/libs/explore/README.md 的「建立一個新房間」寫出來的。
##################################################

init python:

    def build_kitchen():
        room = Room(
            name="kitchen",
            # 沒有美術素材，借用 demo_room.rpy 的測試背景產生器，
            # 換一個寬度來驗證 bg_width 不同時鏡頭範圍會跟著變
            background=_build_demo_background(2400, 1080),
            bg_width=2400,
            on_enter="kitchen_enter",
        )

        # 文字熱點
        room.add_hotspot(Hotspot(
            name="fridge",
            x=1000,
            y=500,
            label="🧊 打開冰箱",
            action=Call("say_in_room", "kitchen_look_fridge"),
        ))

        # 方框熱點，開 debug 看得到判定範圍
        room.add_hotspot(Hotspot(
            name="stove",
            x=1700,
            y=620,
            width=220,
            height=180,
            debug=True,
            action=Call("say_in_room", "kitchen_look_stove"),
        ))

        # 回到測試房間
        room.add_hotspot(Hotspot(
            name="back",
            x=200,
            y=460,
            label="↩ 回到測試房間",
            action=Call("say_in_room", "kitchen_go_back"),
        ))

        return room


##################################################
# 這個房間的 label
##################################################

label kitchen_enter:
    "廚房裡有股燒焦味。"
    return

label kitchen_look_fridge:
    "冰箱門上貼滿了便條紙，沒有一張寫著字。"
    return

label kitchen_look_stove:
    "爐子還是溫的。"
    return

label kitchen_go_back:
    $ change_room("demo_room")
    return
