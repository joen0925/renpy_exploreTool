##################################################
# actor_state.rpy
#
#   角色身上的數值：血量、憤怒值、體力、電池量……
#
#   一張兩層的表：{角色 -> {數值名稱 -> 整數}}
#   不做 hp 專用欄位，因為「綁在某個角色身上的整數計數器」都是同一種東西，
#   新增一種數值不用改引擎，跟 FlagState 一樣。
#
#   引擎只認得一個數值名稱：hp。
#   其他名稱 (battery / stamina / rage) 引擎完全不管，
#   歸零就只是歸零，要有後果請自己用 Condition 接。
#
#   這裡只放「進度」。角色的顯示名稱、立繪、對話用的 Character
#   都是靜態定義，不該存進來 —— 存進去的話改了定義，舊存檔會繼續用舊的
#   (rooms 就是因為把整個物件存進存檔才踩到這個坑)。
#
#   這是 GameState 的一個 section，要有 reset()。
##################################################

init python:

    # 引擎唯一認得的數值名稱：歸零代表死亡。
    ACTOR_HP = "hp"

    # 主角的預設 actor id。Effect 沒指定 actor 時就是改他。
    PLAYER_ACTOR = "player"


    class ActorState:
        def __init__(self):
            # actor_id -> {stat_name: int}
            self.stats = {}

            # 明確死亡的 actor。
            # hp 歸零會自動算死亡 (見 is_dead)，這個 set 是給
            # 「沒有血量概念但還是會消失的角色」用的，例如劇情上離開的 NPC。
            self.dead = set()

        # --- 查詢 ---

        def get(self, actor, stat):
            """
            查一個數值。沒有的話回傳 0，跟 InventoryState.count_of() 同一個約定。
            """
            return self.stats.get(actor, {}).get(stat, 0)

        def has_stat(self, actor, stat):
            """
            這個數值有沒有被「設定過」。

            跟 get() != 0 不一樣：設成 0 也算設定過。
            is_dead() 需要這個來區分「血被扣光」與「根本沒有血量概念」。
            """
            return stat in self.stats.get(actor, {})

        def stats_of(self, actor):
            """這個角色所有的數值 (複本)。debug 面板用。"""
            return dict(self.stats.get(actor, {}))

        def actors(self):
            """所有有數值紀錄的角色。debug 面板用。"""
            return list(self.stats.keys())

        def is_dead(self, actor):
            """
            這個角色死了沒。

            兩種死法：被 kill() 明確標記，或是 hp 歸零。

            第二種刻意要求 hp「被設定過」——
            不然沒有血量概念的角色 get() 回傳 0，會被誤判成一出場就死了。
            換句話說：沒設過 hp 的角色是無敵的。

            這個失敗方向是刻意選的：忘了初始化血量，症狀是「打不死」，
            比「一開場就死」好查得多。
            """
            if actor in self.dead:
                return True

            return self.has_stat(actor, ACTOR_HP) and self.get(actor, ACTOR_HP) <= 0

        def is_alive(self, actor):
            return not self.is_dead(actor)

        # --- 修改 ---

        def set(self, actor, stat, value):
            """
            直接設定一個數值。夾在 0 以上。
            """
            if actor not in self.stats:
                self.stats[actor] = {}

            self.stats[actor][stat] = max(0, int(value))

        def add(self, actor, stat, delta):
            """
            加減一個數值，回傳加減後的結果。夾在 0 以上。

            夾下限是為了避免「hp 扣到 -5，吃了藥加 1 還是死的」這種難查的 bug。
            注意這也代表加減不可逆：扣到 0 之後再加回來，中間溢出的部分不會記得。
            """
            self.set(actor, stat, self.get(actor, stat) + delta)
            return self.get(actor, stat)

        def kill(self, actor):
            """明確讓一個角色死亡，不管他有沒有血量。"""
            self.dead.add(actor)

        def revive(self, actor):
            """
            解除明確死亡的標記。

            注意這「不會」補血 —— 如果對方是因為 hp 歸零而死的，
            解除標記之後 is_dead() 還是會回傳 True。
            要真的救活請一起 set(actor, "hp", n)。
            """
            self.dead.discard(actor)

        def reset(self):
            self.stats = {}
            self.dead = set()

        def __repr__(self):
            return f"<ActorState actors={len(self.stats)} dead={len(self.dead)}>"
