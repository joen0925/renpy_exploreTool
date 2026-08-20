##################################################
# trigger.rpy
#
#   事件的觸發時機。
#
#   七種全部定義好，但目前只有 ENTER_ROOM 與 CLICK_HOTSPOT 真的會被派發。
#   其他四種是預留的名字，接上時不用改介面：
#
#     EXIT_ROOM        離開房間。需要先在 change_room() 加「離開舊房間」的鉤子。
#     INTERACT         語意還沒定義 (跟 CLICK_HOTSPOT 的差別未釐清)。
#     QUEST_COMPLETED  ┐ 這三個是「衍生事件」：Effect 改了狀態之後
#     EVENT_COMPLETED  │ 反過來觸發新的 Event，需要一整套 event bus
#     ITEM_OBTAINED    ┘ 與防無限迴圈的機制，目前沒有使用案例。
#
#   詳見專案根目錄的 pending_imp.md。
##################################################

init python:

    import enum

    class TriggerType(enum.Enum):
        # --- 目前有實際派發的 ---
        ENTER_ROOM = "enter_room"
        CLICK_HOTSPOT = "click_hotspot"

        # --- 預留，尚未接上 ---
        EXIT_ROOM = "exit_room"
        INTERACT = "interact"
        QUEST_COMPLETED = "quest_completed"
        EVENT_COMPLETED = "event_completed"
        ITEM_OBTAINED = "item_obtained"
