##################################################
# trigger.rpy
#
#   事件的觸發時機。
#
#   玩家動作觸發的時機 (已接上派發)：
#     ENTER_ROOM / EXIT_ROOM  由 change_room() 派發
#     CLICK_HOTSPOT           由熱點的點擊派發
#
#   時間觸發的時機 (已接上派發)：
#     TIMER                   進房間幾秒後自動觸發 (Event.delay)。
#                             由 explore_loop 派發，見 room_manager.rpy。
##################################################

init python:

    import enum

    class TriggerType(enum.Enum):
        ENTER_ROOM = "enter_room"
        EXIT_ROOM = "exit_room"
        CLICK_HOTSPOT = "click_hotspot"
        TIMER = "timer"
