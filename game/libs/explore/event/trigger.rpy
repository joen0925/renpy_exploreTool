##################################################
# trigger.rpy
#
#   事件的觸發時機。
#
#   玩家動作觸發的時機 (已接上派發)：
#     ENTER_ROOM / EXIT_ROOM  由 change_room() 派發
#     CLICK_HOTSPOT           由熱點的點擊派發
#
#   時間觸發的時機：
#     TIMER                   由世界時鐘派發。**派發還沒接上** ——
#                             目前只有 Event 的 delay 驗證在用這個名字。
#                             正在實作中，見 pending_imp.md 的動工順序。
##################################################

init python:

    import enum

    class TriggerType(enum.Enum):
        ENTER_ROOM = "enter_room"
        EXIT_ROOM = "exit_room"
        CLICK_HOTSPOT = "click_hotspot"
        TIMER = "timer"
