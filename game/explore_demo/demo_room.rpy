##################################################
# demo_room.rpy
#
#   示範房間：房間定義 + 這個房間會用到的 label 都放在同一個檔案，
#   要知道這個房間點下去會發生什麼事，看這一個檔案就夠了。
#
#   這整個 game/explore_demo/ 目錄都是示範用的，可以直接刪掉。
##################################################

init python:

    def _build_demo_background(width=3200, height=1080):
        """
        用 Ren'Py 內建的 Solid / Text 拼出一張測試背景，不需要任何美術檔案。

        每 400px 畫一條深色直帶並標上該處的 X 座標，
        這樣鏡頭有沒有在動一眼就看得出來，
        也方便你直接讀出想放 hotspot 的位置該填多少 x。
        """
        # Composite 的參數格式：(整張圖的尺寸), (位置), 圖層, (位置), 圖層, ...
        parts = [(width, height)]

        # 底色
        parts += [(0, 0), Transform(Solid("#2c3e50"), xysize=(width, height))]

        # 每 400px 一條色帶 + 座標數字
        for x in range(0, width, 400):
            parts += [(x, 0), Transform(Solid("#34495e"), xysize=(200, height))]
            parts += [(x + 16, 24), Text(str(x), size=40, color="#7f8c8d")]

        return Composite(*parts)

    def build_demo_room():
        room = Room(
            name="demo_room",
            background=_build_demo_background(),
            bg_width=3200,
            on_enter="demo_room_enter",
            on_enter_limit=2
        )

        # 文字熱點：不需要圖片素材，直接畫成一顆 textbutton
        room.add_hotspot(Hotspot(
            name="sign",
            x=520,
            y=500,
            label="🪧 讀看板",
            action=Call("say_in_room", "demo_look_sign"),
        ))

        # 方框熱點：沒有 idle/hover 圖，開 debug=True 用紅框標出判定範圍
        room.add_hotspot(Hotspot(
            name="box",
            x=1600,
            y=620,
            width=240,
            height=200,
            debug=True,
            action=Call("say_in_room", "demo_look_box"),
        ))

        # 靠右邊的熱點：要把鏡頭往右掃才看得到，用來驗證鏡頭與熱點座標有沒有對齊
        room.add_hotspot(Hotspot(
            name="far_door",
            x=2900,
            y=460,
            label="🚪 遠處的門",
            action=Call("say_in_room", "demo_look_door"),
        ))

        # 開啟翻頁視窗的熱點。
        # 這個不用走 say_in_room —— page_popup 是 modal，本身就會擋住底下的熱點，
        # 不需要先把探索畫面收起來。
        room.add_hotspot(Hotspot(
            name="help",
            x=1500,
            y=880,
            label="📖 看說明",
            action=Call("demo_show_help"),
        ))

        # 切換到另一個房間的熱點：切房間要包成 label 再用 Call，
        # 不能直接把 change_room 塞進 action
        room.add_hotspot(Hotspot(
            name="to_kitchen",
            x=1100,
            y=760,
            label="🍳 走去廚房",
            action=Call("say_in_room", "demo_go_kitchen"),
        ))

        room.add_hotspot(Hotspot(
            name="for_test",
            x=1204,
            y=537,
            width=240,
            height=200,
            debug=True,
            action=Call("say_in_room", "test"),
        ))

        room.add_hotspot(Hotspot(
            name="for_test_pop",
            x=2000,
            y=540,
            width=240,
            height=200,
            debug=True,
            action=Call("demo_show_test"),
        ))

        return room


##################################################
# 這個房間的 label
##################################################

label demo_room_enter:
    "你走進了一個測試房間。"
    "把滑鼠往左右移動，鏡頭會跟著掃過整個空間。"
    return

label demo_look_sign:
    "看板上寫著：熱點的座標是背景圖座標，不是螢幕座標。"
    return

label demo_look_box:
    "一個紅框標出來的箱子。這個紅框是 debug=True 畫出來的，正式素材上線後改成 False 就會隱形。"
    return

label demo_look_door:
    "門把是冷的。這扇門在背景圖的 x=2900，要把鏡頭掃到最右邊才看得到。"
    return

label demo_go_kitchen:
    "你推開門走進廚房。"
    $ change_room("kitchen")
    return

label test:
    "測試說話"
    return

##################################################
# 翻頁視窗的示範內容
##################################################

define PAGES_DEMO = [
    {
        "title": "移動",
        "text": "把滑鼠移到畫面左右兩側，鏡頭會跟著轉過去。\n看到門或通道的熱點，點下去就能前往別的房間。",
    },
    {
        "title": "觀察與互動",
        "text": "畫面上可以互動的東西，點下去會有反應。\n這個視窗可以翻頁，也可以放圖片。",
    },
]

define TEST_DEMO = [
    {
        "title": "屁眼",
        "text": "我知道",
    },
    {
        "title": "觀察與互動",
        "text": "A片。",
    },
]

label demo_show_help:
    call show_pages(PAGES_DEMO)
    return

label demo_show_test:
    call show_pages(TEST_DEMO)
    return