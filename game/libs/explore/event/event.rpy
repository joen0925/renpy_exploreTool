##################################################
# event.rpy
#
#   事件本體，以及派發時傳進去的執行環境。
#
#   一個 Event 就是一句「在什麼時機、滿足什麼條件、就做什麼事」。
#
#     Event(
#         id="hall.door_open",
#         condition=Condition(require=["key"]),
#         effect=Effect(set_flags=["door_opened"], label="open_the_door"),
#         sequence=10,
#         limit=1,
#         stop=True,
#     )
#
#   Event 是靜態定義，跟 Room / Hotspot 一樣由 build_rooms() 產生，
#   所以「觸發過幾次」「死了沒」不存在這裡，存在 GameState.events。
##################################################

init python:

    class Event:
        def __init__(
            self,
            id,               # 全域唯一字串。慣例用 "房間名.事件名"，例如 "hall.ghost_warn" 一定要唯一：EventState 用它當 key，撞名會讓兩個事件共用狀態

            condition=None,   # Condition。None = 無條件，一定通過
            effect=None,      # Effect。None = 什麼都不做 (只用來記錄「來過了」時有意義)

            sequence=0,       # 同一個掛載點內的執行順序，小的先跑。每個房間各自獨立計算
            limit=1,          # 最多觸發幾次，用完自動死亡。None = 無限次
            stop=False,       # 這個 Event 觸發之後，就不再檢查後面的

            # 觸發時機。None 代表「由掛載的位置決定」——
            # 掛在 Room.events 就是 ENTER_ROOM，掛在 Hotspot.events 就是 CLICK_HOTSPOT。
            # 之後 EXIT_ROOM 接上時，同一個 list 裡混兩種時機也能正確派發。
            trigger=None,
        ):
            self.id = id
            self.condition = condition
            self.effect = effect
            self.sequence = sequence
            self.limit = limit
            self.stop = stop
            self.trigger = trigger

        def trigger_type(self, default_trigger):
            """實際的觸發時機。沒指定就用掛載位置的預設值。"""
            return self.trigger if self.trigger is not None else default_trigger

        def can_fire(self, context, default_trigger, trigger):
            """
            這次派發要不要執行這個 Event。

            這裡「只讀不寫」，可以安全地重複呼叫。
            實際的狀態改動在 Effect.apply()。
            """
            if self.trigger_type(default_trigger) != trigger:
                return False

            # 死掉的事件直接跳過，連條件都不用算。
            # 這也是為什麼 sequence 的檢查成本會隨遊戲進行而遞減。
            if context.view.is_event_dead(self.id):
                return False

            if self.condition is not None and not self.condition.test(context.view):
                return False

            return True

        def __repr__(self):
            return f"<Event {self.id} seq={self.sequence}>"


    class EventContext:
        """
        派發事件時傳進去的執行環境。

        刻意不放 player —— 目前這個專案沒有任何角色屬性，
        玩家的一切就是 game_state 加上所在的房間。
        之後真的需要時再加。
        """

        def __init__(self, game_state, current_room=None):
            self.game_state = game_state
            self.current_room = current_room

            # 唯讀視圖，給 Condition 用。
            # 它持有 game_state 的引用，所以查詢永遠是即時的 ——
            # 前面的 Effect 改了狀態，後面的 Condition 馬上看得到。
            self.view = game_state.view()

        def __repr__(self):
            room = self.current_room.name if self.current_room else None
            return f"<EventContext room={room}>"
