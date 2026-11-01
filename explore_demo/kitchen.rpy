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
            on_click="kitchen_look_fridge",
        ))

        # 方框熱點，開 debug 看得到判定範圍
        room.add_hotspot(Hotspot(
            name="stove",
            x=1700,
            y=620,
            width=220,
            height=180,
            debug=True,
            on_click="kitchen_look_stove",
        ))

        # 回到測試房間
        room.add_hotspot(Hotspot(
            name="back",
            x=200,
            y=460,
            label="↩ 回到測試房間",
            on_click="kitchen_go_back",
        ))

        # 條件分支的示範：同一個熱點，三種狀態各講不同的話。
        #
        # 沒鑰匙        -> 「鎖住了」        (locker_locked)
        # 有鑰匙        -> 開鎖並拿到紙條    (locker_open，開完就死亡)
        # 已經開過      -> 「空了」          (locker_empty)
        room.add_hotspot(Hotspot(
            name="locker",
            x=500,
            y=520,
            label="🚪 上鎖的櫃子",
            events=[
                # 第一次打開：開櫃子 + 拿紙條。
                # limit=1 所以觸發一次就死亡，之後不管開關幾次都不會再拿到。
                Event(
                    id="kitchen.locker_first_open",
                    condition=Condition(require=["key"], forbid=["locker_opened"]),
                    effect=Effect(
                        set_flags=["locker_opened"],
                        give_items=["note"],
                        label="kitchen_open_locker_first",
                    ),
                    sequence=10, stop=True, limit=1,
                ),

                # 之後再打開：只開櫃子，不給東西。
                # 上面那個死了之後才會輪到這個。
                Event(
                    id="kitchen.locker_open_again",
                    condition=Condition(require=["key"], forbid=["locker_opened"]),
                    effect=Effect(
                        set_flags=["locker_opened"],
                        label="kitchen_open_locker_again",
                    ),
                    sequence=20, stop=True, limit=None,
                ),

                # 沒鑰匙而且櫃子關著
                Event(
                    id="kitchen.locker_locked",
                    condition=Condition(forbid=["key", "locker_opened"]),
                    effect=Effect(label="kitchen_locker_locked"),
                    sequence=30, limit=None,
                ),

                # 櫃子開著
                Event(
                    id="kitchen.locker_empty",
                    condition=Condition(require=["locker_opened"]),
                    effect=Effect(label="kitchen_locker_empty"),
                    sequence=40, limit=None,
                ),
            ]
        ))

        # 測試關箱子
        room.add_hotspot(Hotspot(
            name="close_box",
            label="關櫃子",
            x=510,
            y=380,
            width=100,
            height=100,
            condition=Condition(require=["locker_opened"]),
            events=[
                Event(
                    id="kitchen.close_box",
                    effect=Effect(
                            remove_items=["key"],
                            clear_flags=["locker_opened"],
                            label="close_locker",
                    ),
                    limit=None,
                ),
            ]
        ))

        # 保險箱：解謎關卡 (KeypadPuzzle) 的示範。
        #
        # 熱點本身什麼都不做，只負責把關卡叫出來 ——
        # 不給 Hotspot 加 puzzle 欄位，一律走 label，
        # 跟換房間、講話同一條規則。
        #
        # 開過就不用再開了，所以用 condition 讓它自己消失。
        room.add_hotspot(Hotspot(
            name="safe",
            x=1400,
            y=300,
            label="🔒 保險箱",
            condition=Condition(forbid=["safe_opened"]),
            on_click="kitchen_open_safe",
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

label kitchen_open_locker_first:
    "鑰匙轉了半圈，鎖開了。"
    "櫃子裡有一張潮濕的紙條。"
    return

label kitchen_open_locker_again:
    "你又把櫃子打開了。裡面空空如也。"
    return

label kitchen_locker_locked:
    "鎖住了。得先找到鑰匙。"
    return

label kitchen_locker_empty:
    "櫃子已經空了。"
    return

label close_locker:
    "櫃子關起來了。"
    return

label kitchen_open_safe:
    call run_puzzle("kitchen_safe") from _call_kitchen_open_safe
    return

label kitchen_safe_opens:
    "四聲喀答之後，鎖舌彈開了。"
    "裡面躺著一個牛皮紙袋。"
    return

label kitchen_safe_shock:
    "鍵盤發出一聲短促的蜂鳴。"
    "指尖竄過一陣刺痛 —— 這東西會咬人。"
    return
