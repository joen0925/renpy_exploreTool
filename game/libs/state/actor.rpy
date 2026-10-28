##################################################
# actor.rpy
#
#   角色目錄：引擎需要知道的那一小部分「這個角色是誰」。
#
#   刻意只有四個欄位。不在這裡的東西與它們的去處：
#
#     立繪    Ren'Py 的 image 命名空間 (image annie calm = "...")
#             不自己做一套 —— Ren'Py 的 show 已經會：照屬性挑圖、
#             只換表情時保留位置、把「現在顯示什麼」存進存檔與倒帶紀錄。
#             自己存一份「現在的表情」就要自己重新解決存檔與倒帶，
#             而那是這個專案已經踩過兩次的坑。
#
#     台詞    Ren'Py 的 Character (define annie = Character("安妮"))
#
#     位置    演出自己的 show ... at ...。「現在站在哪」是演出的狀態，
#             記在角色定義上會被 reload 重建、不會進存檔、還會漏到下一場戲。
#
#   所以一個角色的檔案長這樣 (game/explore_demo/characters/annie.rpy)：
#
#       image annie calm = "characters/annie/calm.png"
#       define annie = Character("安妮")
#
#       init python:
#           def build_annie():
#               return Actor(key="annie_ghost", name="安妮", stats={"hp": 3, "rage": 0})
#
#   關於這個角色的一切 (立繪、名字、數值、他自己的演出 label) 都在那一個檔案裡，
#   跟「一個檔案一個房間」是同一個原則。
#
#   ---
#
#   這裡放「定義」，ActorState 放「進度」。
#
#   目錄用 define 宣告 (不進存檔)，所以改了名字、改了初始血量，
#   連舊存檔都會馬上吃到新的。玩家現在幾滴血在 ActorState 裡，跟著存檔走。
#   這跟 item_catalog / Item 是同一套切法。
##################################################

init python:

    class Actor:
        def __init__(
            self,
            key,                  # 唯一識別字串。Effect(actor=...) 與 s.stats(...) 用的就是這個
            name,                 # 顯示名稱，例如 "安妮"

            # 初始數值 {"hp": 3, "rage": 0}。開新遊戲時寫進 ActorState。
            #
            # 沒有 hp 的角色在引擎眼中是「無敵」的 —— 這是刻意的失敗方向，
            # 忘了給血的症狀是「打不死」，比「一開場就死」好查得多
            # (見 ActorState.is_dead)。路人就該沒有 hp。
            stats=None,

            # 狀態欄要顯示這個角色的哪些數值，由上往下依順序排。
            #     [{"stat": "hp", "icon": "❤️"}, {"stat": "battery", "icon": "🔦", "name": "電量"}]
            #
            # 只有要顯示給玩家看的角色需要填 —— 所以鬼的 rage 不會漏給玩家看到。
            status_display=None,
        ):
            self.key = key
            self.name = name
            self.stats = dict(stats) if stats else {}
            self.status_display = list(status_display) if status_display else []

        def __reduce__(self):
            """
            存檔時只存 key，讀檔時再從目前的目錄查回來。

            正常情況下 Actor 不會進存檔 (actor_catalog 是 define)。
            但只要有人寫了一行
                $ current_ghost = actor_def("annie_ghost")
            那個 store 變數就會被 pickle，而 Actor 身上可能掛著
            Condition(check=lambda ...) 之類定義在函式內部的東西，
            Python 存不了，存檔會直接爆掉。

            跟 Room / Hotspot 用同一個解法，理由也一樣：
            角色是靜態定義，改了定義舊存檔也要吃得到。
            """
            return (actor_def_required, (self.key,))

        def __repr__(self):
            return f"<Actor {self.key}>"


    def add_actor(actors, actor):
        """
        把一個 Actor 加進目錄，回傳那個目錄。key 重複就直接報錯。

        用法 (在 build_actors() 裡)：
            add_actor(actors, build_annie())

        為什麼不直接寫 actors["annie_ghost"] = Actor(...)：
        那樣重複定義會安靜地蓋掉前面那個，Python 不會抗議。
        症狀是「我明明設了 3 滴血怎麼變成 5」，而兩筆定義可能隔了幾百行。
        (物品目錄目前還有這個漏洞，它只檢查 dict key 與 Item.key 一致)

        順便也不可能發生「dict key 跟 Actor.key 不一致」—— key 是推出來的，
        所以 item_catalog 那種事後驗證在這裡不需要。
        """
        if actor.key in actors:
            raise ValueError(
                f"角色目錄裡已經有 \"{actor.key}\" 了，不能重複定義。\n"
                f"是不是複製貼上之後忘了改 key？"
            )

        actors[actor.key] = actor
        return actors


    def actor_def(key):
        """
        查一個角色的定義，查不到回傳 None。

        用 getattr 而不是直接寫 store.actor_catalog，是因為角色清單
        由遊戲內容那邊宣告，引擎不能假設它一定存在。
        """
        return getattr(store, "actor_catalog", {}).get(key)


    def actor_def_required(key):
        """
        查一個角色的定義，查不到直接報錯。讀檔還原 (見 Actor.__reduce__) 用。
        """
        actor = actor_def(key)

        if actor is None:
            raise ValueError(
                f"找不到角色 \"{key}\"。\n"
                f"是不是把它從 build_actors() 裡刪掉或改名了？"
            )

        return actor


    def actor_name(key):
        """
        角色的顯示名稱。查不到就回傳 key 本身 ——
        debug 面板用，那裡寧可顯示 raw id 也不要整個當掉。
        """
        actor = actor_def(key)
        return actor.name if actor is not None else key


    def known_actor_ids():
        """
        目錄裡所有的角色 id。角色目錄不存在時回傳 None
        (而不是空集合) —— 「沒有目錄」與「目錄是空的」要分得出來，
        前者代表這個專案沒在用角色目錄，所有檢查都該跳過。
        """
        catalog = getattr(store, "actor_catalog", None)

        if catalog is None:
            return None

        return set(catalog)


    def init_actor_stats_from_catalog():
        """
        把目錄裡每個角色的初始數值寫進 GameState。

        開新遊戲時呼叫一次，而且一定要排在第一次 change_room 之前 ——
        進房事件本身就可能扣血。
        """
        for key, actor in getattr(store, "actor_catalog", {}).items():
            for stat, value in actor.stats.items():
                store.game_state.actors.set(key, stat, value)


    def find_unknown_actor_ids(rooms, puzzles=None):
        """
        掃過所有 Effect，找出 actor= 指到目錄裡沒有的角色。
        回傳 [(是誰寫的, 打錯的 id), ...]，沒問題就是空清單。

        為什麼一定要這個檢查 —— 打錯字的症狀非常難查：

            Effect(actor="playr", stats={"hp": -1})

        ActorState.add 查不到 "playr" 就當它是 0，存回 max(0, -1) = 0，
        於是憑空多出一個 hp=0 的幽靈角色 (引擎還會認為它死了)，
        而**真正的玩家一滴血都沒掉**。遊戲照跑，只是主角變成無敵。

        ⚠️ 這個檢查抓不到 lambda 裡面的字串：
            Condition(check=lambda s: s.stats("anie_ghost", "rage") >= 2)
        那種靜態掃不到，所以 StateView.stats() 另外做了執行期檢查。

        純函式，餵假的 rooms 就能測。
        """
        known = known_actor_ids()

        if known is None:
            return []

        bad = []

        def check(owner, effect):
            if effect is None or effect.actor is None:
                return
            if effect.actor not in known:
                bad.append((owner, effect.actor))

        for room in rooms.values():
            for event in getattr(room, "events", None) or []:
                check(event.id, event.effect)

            for hotspot in room.hotspots:
                for event in getattr(hotspot, "events", None) or []:
                    check(event.id, event.effect)

        for name, puzzle in (puzzles or {}).items():
            check(f"puzzle:{name}", getattr(puzzle, "on_success", None))
            check(f"puzzle:{name}", getattr(puzzle, "on_failure", None))

        return bad


    def check_actor_catalog(rooms, puzzles=None):
        """
        啟動時的檢查。有問題直接拋例外，讓遊戲一開就爆掉。

        用法 (在內容層，要排在 rooms 與 puzzle_catalog 都建好之後)：
            init 2 python:
                check_actor_catalog(rooms, puzzle_catalog)
        """
        bad = find_unknown_actor_ids(rooms, puzzles)

        if not bad:
            return

        raise ValueError(
            "有 Effect 指到不存在的角色：\n"
            + "\n".join(f"  {owner} -> actor=\"{a}\"" for owner, a in bad)
            + "\n\n請在 build_actors() 裡把它加進去，或是修正拼字。"
        )
