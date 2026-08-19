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

        return rooms


# change_room() 用字串找房間時就是查這個字典。
# 放 default 而不是 init，是為了讓房間狀態 (例如 hotspot.visible 被改過)
# 能跟著存檔一起被保存下來。
default rooms = build_rooms()