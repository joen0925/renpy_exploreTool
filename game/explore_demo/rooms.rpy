##################################################
# rooms.rpy
#
#   房間清單 (遊戲內容，不屬於 game/libs/explore/ 的引擎)
#
#   新增房間的步驟：
#     1. 在 rooms/ 底下寫一個 build_xxx() 回傳 Room 物件
#     2. 在下面 build_rooms() 裡加一行 rooms["xxx"] = build_xxx()
#   之後就可以用 change_room("xxx") 切換過去。
##################################################

init python:

    def build_rooms():
        rooms = {}

        rooms["demo_room"] = build_demo_room()
        rooms["kitchen"] = build_kitchen()
        rooms["bed_room"] = build_bed_room()
        rooms["attic"] = build_attic()
        rooms["playground"] = build_playground()

        return rooms


# change_room() 用字串找房間時就是查這個字典。
#
# 為什麼是 init 而不是 default (曾經是 default，2026-08-25 改掉)：
#
# default 的變數會被寫進存檔，也就是說整棵 Room / Hotspot 物件樹都會被 pickle。
# 但 Hotspot 可以帶 Condition(check=lambda ...)，而那個 lambda 定義在
# build_xxx() 函式內部 —— Python 存不了函式內的區域物件，存檔會直接爆掉：
#     AttributeError: Can't get local object 'build_bed_room.<locals>.<lambda>'
#
# 而且就算不用 lambda，把房間存進存檔還有另一個長期的痛：
# 改了熱點座標、改了文字、加了新熱點，舊存檔統統吃不到 ——
# 因為讀檔時是把當初存的那份舊 Room 物件還原回來。
#
# 房間是「靜態定義」，跟 item_catalog 一樣，本來就不該進存檔。
# 玩家的進度全部在 game_state 裡，熱點顯不顯示請用 condition 推導。
#
# 為什麼是 init 1 而不是 define：
#
# 兩者都不會進存檔，但 define 在優先權 0 執行，跟各房間檔的 init python 同一層，
# 所以會照檔名排序 —— 檔名排在 rooms.rpy 之後的房間 (例如 study.rpy) 會來不及定義：
#     NameError: name 'build_study' is not defined
# init 1 保證在所有優先權 0 的 init 跑完之後才執行，檔名怎麼取都不會踩到。
init 1 python:
    rooms = build_rooms()