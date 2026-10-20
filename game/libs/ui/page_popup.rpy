##################################################
# page_popup.rpy
#
# 通用的翻頁彈出視窗。可以拿來做教學、道具說明、線索筆記、地圖說明…
# 任何「一頁一頁看文字配圖」的東西都能用這一個視窗。
#
# 這個檔案不依賴探索工具包的任何東西 (Room / Camera / Hotspot 都沒用到)，
# 可以單獨複製到別的 Ren'Py 專案使用。
#
# 用法：在任何 label 裡寫
#
#     call show_pages(PAGES_HELP)
#
# 呼叫端會停在這裡，等玩家把視窗關掉才會往下走。
#
# 每一頁是一個 dict，可用欄位 (全部都可省略，但至少要有 text 或 img 其中之一)：
#   title  這一頁的標題，例如 "移動"
#   text   說明文字，可以用 \n 換行
#   img    這一頁要配的圖片路徑，例如 "images/arrow_left.png"
#
# 頁面資料自己命名一個變數放著就好：
#
#     define PAGES_HELP = [
#         {"title": "移動", "text": "把滑鼠移到左右兩側，鏡頭會跟著轉。", "img": "images/arrow.png"},
#         {"title": "互動", "text": "可互動的東西，滑鼠移過去會有提示。"},
#     ]
#
# 只有一頁時，翻頁按鈕會自動隱藏。
##################################################

# 視窗目前翻到第幾頁 (0 = 第一頁)。
# 每次 call show_pages 進來時會歸零，所以同一份資料重看也會從頭開始。
default page_popup_index = 0


screen page_popup(pages):
    # 擋住後方所有東西，視窗開著時點不到底下的按鈕/熱點。
    # 注意 modal 擋的是「點擊」不是「滑鼠移動」，
    # 所以在探索畫面上開這個視窗時，底下的鏡頭仍然會跟著滑鼠移動 (這是刻意允許的)。
    modal True

    zorder 200

    # 保險：頁面資料是空的就直接結束，不要讓下面的 pages[index] 爆掉
    if not pages:
        timer 0.01 action Return()

    else:
        # 翻頁用的頁碼放在 store 變數 page_popup_index (見上面的 default)，
        # 不是 screen 自己的變數。翻頁就是 SetVariable 改它 + 重畫。
        $ index = min(page_popup_index, len(pages) - 1)
        $ page = pages[index]
        $ is_first = (index == 0)
        $ is_last = (index == len(pages) - 1)
        $ has_multiple_pages = (len(pages) > 1)

        # 按 ESC (或滑鼠右鍵) 關閉視窗。
        # 不攔截的話這兩個操作會跳出 Ren'Py 的遊戲選單。
        key "game_menu" action Return()

        # 背景壓暗
        add "#000000cc"

        # 視窗本體：固定尺寸的深色底，內容再往裡面塞
        frame:
            align (0.5, 0.5)
            xysize (1100, 720)
            padding (50, 40)
            background Frame(Solid("#1a1a1acc"), 0, 0)

            vbox:
                align (0.5, 0.5)
                spacing 24
                xfill True

                # 標題
                if page.get("title"):
                    text page["title"]:
                        xalign 0.5
                        color "#e67e22"
                        size 42

                # 圖片：限制最大顯示尺寸，免得圖太大把視窗撐爆
                if page.get("img"):
                    add page["img"]:
                        xalign 0.5
                        fit "contain"
                        xysize (900, 380)

                # 說明文字
                if page.get("text"):
                    text page["text"]:
                        xalign 0.5
                        text_align 0.5
                        color "#ffffff"
                        size 30
                        line_spacing 8

        # 底部操作列
        hbox:
            align (0.5, 0.9)
            spacing 60

            # 只有一頁的話不需要翻頁按鈕，只留一顆關閉
            if has_multiple_pages:

                textbutton "◀ 上一頁":
                    text_size 28
                    text_color "#e67e22"
                    text_hover_color "#ffffff"
                    text_insensitive_color "#666666"
                    sensitive (not is_first)
                    # SetVariable 改完 store 變數會自動重畫畫面，就翻頁了
                    action SetVariable("page_popup_index", index - 1)

                text "%d / %d" % (index + 1, len(pages)):
                    yalign 0.5
                    color "#aaaaaa"
                    size 26

                if is_last:
                    textbutton "關閉":
                        text_size 28
                        text_color "#e67e22"
                        text_hover_color "#ffffff"
                        action Return()
                else:
                    textbutton "下一頁 ▶":
                        text_size 28
                        text_color "#e67e22"
                        text_hover_color "#ffffff"
                        action SetVariable("page_popup_index", index + 1)

            else:
                textbutton "關閉":
                    text_size 28
                    text_color "#e67e22"
                    text_hover_color "#ffffff"
                    action Return()

        # 右上角關閉
        textbutton "✕":
            align (0.97, 0.04)
            text_size 28
            text_color "#888888"
            text_hover_color "#ffffff"
            action Return()


# 顯示視窗並「等玩家關掉才繼續」的入口。
#
#     call show_pages(PAGES_HELP)
#
# call screen 會卡在這裡，直到 screen 裡某顆按鈕執行 Return()，
# 然後才會往下走、回到呼叫的地方。
label show_pages(pages):
    # 視窗期間對話框(黑框)要收起來，不然會疊在視窗上
    window hide

    # 每次打開都從第一頁開始
    $ page_popup_index = 0

    # 倒帶 (quick menu 的「返回」、滾輪、PageUp) 要跳過這個視窗。
    #
    # call screen 本來是倒帶的停靠點，所以玩家看完簡介、關掉之後按返回，
    # 會「倒帶回到視窗裡」。而視窗是 modal，會擋住 quick menu 的返回鈕 ——
    # 玩家在裡面按不到返回，只能關掉，關掉再按返回又回到視窗裡，永遠出不去。
    #
    # suspend_rollback 讓這段期間的停靠點變成 soft，倒帶會直接跳過。
    # 這個旗標是記在每一筆倒帶紀錄上的，倒帶時會一起還原，不會殘留。
    $ renpy.suspend_rollback(True)

    # 翻頁視窗期間世界時鐘暫停 —— 看說明、讀筆記不該被追殺。
    # (解謎視窗刻意相反，那邊不暫停)
    #
    # 這個檔案本來不依賴探索工具包的任何東西，用 getattr 問一下
    # 就是為了維持那件事：單獨複製到沒有 world 的專案也能用。
    $ _page_world = getattr(store, "world", None)

    if _page_world is not None:
        $ _page_world.pause("page_popup")

    call screen page_popup(pages=pages)

    if _page_world is not None:
        $ _page_world.resume("page_popup")

    $ renpy.suspend_rollback(False)

    return
