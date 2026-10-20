##################################################
# trigger.rpy
#
#   事件的觸發時機。
#
#   三種時機都會被實際派發：
#     ENTER_ROOM / EXIT_ROOM  由 change_room() 派發
#     CLICK_HOTSPOT           由熱點的點擊派發
##################################################

init python:

    import enum

    class TriggerType(enum.Enum):
        ENTER_ROOM = "enter_room"
        EXIT_ROOM = "exit_room"
        CLICK_HOTSPOT = "click_hotspot"
