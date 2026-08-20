##################################################
# event_state.rpy
#
#   事件的執行狀態：每個 Event 觸發過幾次、有沒有死亡。
#
#   為什麼存在這裡而不是存在 Event 物件上：
#   Event 跟 Room 一樣是 build_rooms() 產生的「靜態定義」，
#   按 debug 面板的「重新載入房間資料」時會被整個重建。
#   如果把觸發次數記在 Event 物件上，一重新載入就歸零了
#   (Room.on_enter_count 就踩過這個坑)。
#   觸發次數與死亡狀態是「遊戲進度」，該跟著存檔走，所以放在 GameState 裡。
#
#   這是 GameState 的一個 section，要有 reset()。
##################################################

init python:

    class EventState:
        def __init__(self):
            # event_id -> 已觸發次數
            self.counts = {}

            # 已死亡的 event_id。
            # 死亡代表「這件事結束了，不用再檢查」，
            # 派發時會先跳過死亡的 Event，所以 sequence 的檢查成本會隨遊戲進行遞減。
            self.dead = set()

        def count_of(self, event_id):
            return self.counts.get(event_id, 0)

        def record_trigger(self, event_id, limit):
            """
            記錄一次觸發，並在次數用完時自動轉成死亡。

            limit 是 None 代表無限次，永遠不會因為次數而死。
            """
            self.counts[event_id] = self.count_of(event_id) + 1

            if limit is not None and self.counts[event_id] >= limit:
                self.kill(event_id)

        def kill(self, event_id):
            """讓一個 Event 死亡。可以殺別的房間的 Event。"""
            self.dead.add(event_id)

        def revive(self, event_id):
            """
            讓一個死亡的 Event 復活。

            引擎本身不會呼叫這個，是留給遊戲邏輯用的
            (例如「重置這個房間的謎題」)。
            """
            self.dead.discard(event_id)

        def is_dead(self, event_id):
            return event_id in self.dead

        def reset(self):
            self.counts = {}
            self.dead = set()

        def __repr__(self):
            return f"<EventState triggered={len(self.counts)} dead={len(self.dead)}>"
