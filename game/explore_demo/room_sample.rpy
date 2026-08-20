##################################################
# room_sample.rpy —— 房間樣板
#
#   複製這個檔案改名就能開始寫新房間。
#
#   建立步驟：
#     1. 複製此檔，改名成 你的房間名.rpy
#     2. 全檔搜尋取代 sample -> 你的房間名   (函式名、label 名、事件 id 都會一起改到)
#     3. 到 rooms.rpy 的 build_rooms() 加一行：
#            rooms["你的房間名"] = build_你的房間名()
#     4. 用 $ change_room("你的房間名") 進去
#
#   座標怎麼填：進遊戲按 F9 開標點面板，滑鼠移到想放的位置按 F10 釘住，
#
#   完整說明見 game/libs/explore/DEVELOPER_GUIDE.md
##################################################

init python:

    def build_sample():
        room = Room(
            name="sample",
            background="images/bg_sample.png",
            bg_width=3000,
            on_enter="sample_enter",
        )

        room.add_hotspot(Hotspot(
            name="sign",
            x=800, y=500,
            label="🪧 看板",
            on_click="sample_look_sign",
        ))

        room.add_hotspot(Hotspot(
            name="window",
            x=1500, y=400,
            width=300, height=400,
            debug=True,
            on_click="sample_look_window",
        ))

        room.add_hotspot(Hotspot(
            name="notice",
            x=1000, y=300,
            label="📖 讀說明書",
            on_click="sample_show_pages",
        ))

        room.add_hotspot(Hotspot(
            name="item_pickup",
            x=2200, y=600,
            label="✨ 某個東西",
            condition=Condition(forbid=["sample_item"]),
            events=[
                Event(
                    id="sample.pick_item",
                    effect=Effect(
                        give_items=["sample_item"],
                        label="sample_pick_item",
                    ),
                ),
            ],
        ))

        room.add_hotspot(Hotspot(
            name="door",
            x=2600, y=450,
            label="🚪 門",
            events=[
                Event(
                    id="sample.door_open",
                    condition=Condition(require=["key"]),
                    effect=Effect(
                        set_flags=["sample_door_opened"],
                        label="sample_open_door",
                    ),
                    sequence=10,
                    stop=True,
                ),
                Event(
                    id="sample.door_locked",
                    effect=Effect(label="sample_door_locked"),
                    sequence=20,
                    limit=None,
                ),
            ],
        ))

        room.add_hotspot(Hotspot(
            name="exit",
            x=200, y=700,
            label="↩ 離開",
            on_click="sample_leave",
        ))

        return room


##################################################
# 翻頁視窗的內容
##################################################

define SAMPLE_PAGES = [
    {
        "title": "第一頁的標題",
        "text": "第一頁的內容。\n用 \\n 換行。",
    },
    {
        "title": "第二頁的標題",
        "text": "三個欄位都可以省略。",
        "img": "images/sample_page.png",
    },
]


##################################################
# 這個房間的 label
##################################################

label sample_enter:
    "（進來這個房間時講的話）"
    return

label sample_look_sign:
    "（點看板時講的話）"
    return

label sample_look_window:
    "（點窗戶時講的話）"
    return

label sample_show_pages:
    call show_pages(SAMPLE_PAGES)
    return

label sample_pick_item:
    "（撿到東西時講的話）"
    return

label sample_open_door:
    "鑰匙轉動了。"
    $ change_room("某個房間")
    return

label sample_door_locked:
    "鎖住了。"
    return

label sample_leave:
    $ change_room("某個房間")
    return
