##################################################
# inventory_display.rpy
#
#   物品欄畫面。
#
#   放在探索畫面的右上角 —— 左上角被 debug 標點面板 (F9) 佔走了。
#
#   用法：在探索畫面裡加一行
#       use inventory_display
#
#   物品欄只存 key 與數量，名稱/圖示/描述都是即時查 item_catalog，
#   所以這裡看到的永遠是目前的物品定義，不是撿取當下的快照。
##################################################

screen inventory_display():

    frame:
        xalign 1.0
        xoffset -20
        yalign 0.0
        yoffset 20
        padding (16, 12)
        background "#000000aa"

        vbox:
            spacing 6

            text "【物品】":
                size 20
                color "#aaaaaa"

            $ _inv_keys = game_state.inventory.keys()

            if _inv_keys:
                for _key in _inv_keys:
                    # 查目錄拿定義。查不到的話 (例如目錄裡把這個物品刪掉了)
                    # 就退而顯示 key 本身，不要讓畫面直接當掉。
                    $ _item = item_def(_key)
                    $ _count = game_state.inventory.count_of(_key)
                    $ _name = _item.name if _item else _key

                    # 數量 1 的時候不顯示「×1」，畫面比較乾淨
                    $ _suffix = ("  ×%d" % _count) if _count > 1 else ""

                    hbox:
                        spacing 8

                        if _item and _item.icon:
                            add _item.icon:
                                xysize (28, 28)

                        textbutton "[_name][_suffix]":
                            text_size 22
                            text_color "#2ecc71"
                            text_hover_color "#ffffff"
                            action Call("_show_item_detail", _key)

            else:
                text "(無)":
                    size 22
                    color "#7f8c8d"


# 點物品欄裡的物品時顯示它的描述。
#
# 直接重用翻頁視窗 —— 一個物品就是一頁，
# 標題是名稱、內文是描述、圖是 icon。
label _show_item_detail(item_key):
    python:
        _item = item_def(item_key)

        _detail_pages = [{
            "title": _item.name if _item else item_key,
            "text": (_item.description if _item and _item.description
                     else "（沒有更多資訊）"),
            "img": _item.icon if _item else None,
        }]

    call show_pages(_detail_pages) from _call_show_item_detail

    return
