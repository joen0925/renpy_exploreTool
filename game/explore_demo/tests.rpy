##################################################
# tests.rpy
#
#   探索工具包的自動化測試。
#
#   執行方式（在 SDK 目錄下）：
#       renpy.exe <專案路徑> test explore_smoke
#
#   testcase 只在 test 模式下執行，正常玩遊戲不受影響。
##################################################

init python:

    # 測試過程的軌跡記錄，用來確認每個步驟真的有跑到
    # （光看 PASSED 不夠，要能證明流程確實走完）
    # 產生在專案根目錄的 test_trace.txt
    _TRACE_PATH = __import__("os").path.join(renpy.config.basedir, "test_trace.txt")

    def _trace_reset():
        with open(_TRACE_PATH, "w", encoding="utf-8") as f:
            f.write("=== trace start ===\n")

    def _trace(step):
        room = current_room.name if current_room else None
        exploring = renpy.get_screen("explore") is not None

        # on_enter 的觸發次數存在 GameState.events，不在 Room 物件上。
        # Room 是靜態定義會被 reload 重建，次數是遊戲進度要跟著存檔走。
        cnt = game_state.events.count_of(f"{room}.on_enter") if room else None

        with open(_TRACE_PATH, "a", encoding="utf-8") as f:
            f.write(
                f"{step} | room={room} | explore={exploring}"
                f" | offset={camera.offset:.1f} | on_enter_count={cnt}\n"
            )


# 走一遍完整的探索流程：
#   開場白 -> 點熱點講話 -> 換房間 -> 在新房間點熱點 -> 換回原房間
#
# 重點是驗證「連續多次互動之後，探索狀態還在」，
# 也就是 explore_loop 有沒有確實接住 say_in_room 的返回點。
#
# 對話一律用「advance until 某個熱點出現」來推進，而不是數 advance 的次數。
# 因為對話講完 explore 畫面才會被放回來，熱點出現就代表已經回到可互動狀態，
# 這樣即使之後改了對話長度，測試也不用跟著改。
testcase explore_smoke:

    # 每個語句的等待上限，預設 5 秒對含轉場的流程來說偏短
    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _trace_reset()

    # 測試是從主選單開始跑的，先點「開始」進遊戲。
    # 注意這個專案的介面是繁體中文，按鈕文字不是 "Start"。
    click "開始"

    # --- 開場：推完 demo_room 的 on_enter，直到探索畫面回來 ---
    advance until "走去廚房"
    $ _trace("1_開場結束")
    $ assert current_room.name == "demo_room", f"開場應該在 demo_room，實際在 {current_room.name}"
    # 有設 on_enter 的房間，第一次進來一定會觸發一次
    $ _enter_id = current_room.name + ".on_enter"
    $ assert game_state.events.count_of(_enter_id) == 1, f"第一次進房後計數應該是 1，實際 {game_state.events.count_of(_enter_id)}"

    # --- 第 1 次互動：點熱點講話，並切換到另一個房間 ---
    click "走去廚房"
    advance until "打開冰箱"
    $ _trace("2_切換到kitchen")
    $ assert current_room.name == "kitchen", f"應該已經切換到 kitchen，實際在 {current_room.name}"

    # --- 第 2 次互動：驗證換房間之後熱點仍然可以點 ---
    click "打開冰箱"
    advance until "打開冰箱"
    $ _trace("3_在kitchen點熱點")
    $ assert current_room.name == "kitchen", "點熱點講完話不該換房間"

    # --- 第 3 次互動：需要先移動鏡頭才點得到的熱點 ---
    # back 在背景圖 x=200，kitchen 初始 offset=-240，螢幕位置 -40 在畫面外。
    # 把滑鼠移到螢幕左側，鏡頭會掃過去，熱點才會進入畫面。
    #
    # 一定要用 renpy.set_mouse_pos() 而不是測試框架的 move：
    # camera.update() 讀的是 renpy.get_mouse_pos()，那個函式不經過測試框架的滑鼠覆寫，
    # 拿到的永遠是「真實游標位置」。用 move 的話鏡頭不會動，
    # 測試會變成靠執行當下游標剛好在哪裡來決定成敗。
    # (副作用：這會實際移動你的滑鼠游標)
    $ renpy.set_mouse_pos(60, 540)
    pause 2.0
    $ assert camera.offset > -100, f"鏡頭應該已經掃到左側，實際 offset={camera.offset}"
    $ _trace("4_鏡頭掃到左邊")

    click "回到測試房間"
    advance until "走去廚房"
    $ _trace("5_切換回demo_room")
    $ assert current_room.name == "demo_room", f"應該切換回 demo_room，實際在 {current_room.name}"

    # on_enter 的觸發次數不該超過房間自己設定的上限。
    #
    # 這裡刻意不寫死成某個數字 —— demo 房間的 on_enter_limit 是可以隨時被調整的，
    # 寫死的話別人改 demo 就會讓這個測試誤報。
    # limit 本身的精確邏輯 (1 / 2 / None / 沒設 on_enter) 由 unit_checks 負責，
    # 那裡是自己建 Room 來測，不受 demo 內容影響。
    $ _limit = current_room.on_enter_limit
    $ _cnt = game_state.events.count_of(current_room.name + ".on_enter")
    $ assert _limit is None or _cnt <= _limit, f"on_enter 觸發 {_cnt} 次，超過上限 {_limit}"

    # --- 第 4 次互動：確認繞了一圈之後探索狀態還在 ---
    # 走到這裡代表 explore_loop 一直有接住返回點，沒有漏出去回主選單
    click "走去廚房"
    advance until "打開冰箱"
    $ _trace("6_第四次互動完成")
    $ assert current_room.name == "kitchen", "第四次互動仍應正常運作"


# 翻頁視窗 (page_popup) 與 debug 標點面板 (explore_debug) 的測試。
testcase popup_and_debug:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _trace_reset()

    click "開始"
    advance until "看說明"
    $ _trace("1_進入探索")

    # --- 翻頁視窗 ---
    click "看說明"
    pause 0.5
    $ _trace("2_開啟視窗")
    $ assert renpy.get_screen("page_popup") is not None, "視窗應該要出現"
    $ assert page_popup_index == 0, "每次打開都要從第一頁開始"

    click "下一頁"
    pause 0.3
    $ _trace("3_翻到第二頁")
    $ assert page_popup_index == 1, f"應該翻到第二頁，實際 index={page_popup_index}"

    # 最後一頁的按鈕會變成「關閉」
    click "關閉"
    pause 0.5
    $ _trace("4_關閉視窗")
    $ assert renpy.get_screen("page_popup") is None, "視窗應該要關掉"

    # --- debug 標點面板 ---
    keysym "K_F9"
    pause 0.3
    $ _trace("5_F9開啟面板")
    $ assert renpy.get_screen("explore_debug") is not None, "F9 應該要叫出 debug 面板"

    # 移到畫面中央再釘座標。
    # 用 renpy.set_mouse_pos 而不是 move —— F10 記錄的是 renpy.get_mouse_pos()，
    # 也就是真實游標位置，測試框架的 move 影響不到它。
    $ renpy.set_mouse_pos(960, 400)
    pause 1.0
    keysym "K_F10"
    pause 0.3
    $ _trace("6_F10釘住座標")
    $ assert debug_pinned_pos is not None, "F10 應該要釘住座標"

    # 面板開著時，底下的熱點仍然要能點 (驗證 overlay 沒有擋住探索畫面)
    click "走去廚房"
    advance until "打開冰箱"
    $ _trace("7_面板開著仍可點熱點")
    $ assert current_room.name == "kitchen", "debug 面板不該擋住熱點"
    $ assert renpy.get_screen("explore_debug") is not None, "換房間後面板應該還在"

    # --- 重新載入房間資料 ---
    # 先記住目前房間物件的身分，重新載入後應該換成一個全新的物件
    $ _old_room_id = id(current_room)

    click "重新載入房間資料"
    pause 0.3
    $ assert explore_debug_confirm_reload, "重新載入應該要先跳確認，不能直接執行"

    click "確定重新載入"
    pause 0.5
    $ _trace("8_重新載入房間資料")
    $ assert not explore_debug_confirm_reload, "確認狀態應該要收掉"
    $ assert id(current_room) != _old_room_id, "房間物件應該被重建成新的"
    $ assert current_room.name == "kitchen", "重新載入後應該留在同一個房間"

    keysym "K_F9"
    pause 0.3
    $ _trace("9_F9關閉面板")
    $ assert renpy.get_screen("explore_debug") is None, "F9 應該要收起 debug 面板"


# 純邏輯測試：不需要畫面，直接建物件驗證方法的行為。
# 這些跑起來很快也很穩定，適合放邊界條件。
testcase unit_checks:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    # --- Camera.enter_room 的置中計算 ---

    # 背景比螢幕寬 (3200 > 1920)：置中，offset = -(3200-1920)/2 = -640
    $ _cam = Camera()
    $ _cam.enter_room(Room(name="wide", background=None, bg_width=3200))
    $ assert _cam.offset == -640, f"寬背景應該置中在 -640，實際 {_cam.offset}"

    # 背景等於螢幕寬：不需要偏移
    $ _cam.enter_room(Room(name="exact", background=None, bg_width=1920))
    $ assert _cam.offset == 0, f"等寬背景 offset 應該是 0，實際 {_cam.offset}"

    # 背景比螢幕窄 (1200 < 1920)：min(0, 正數) 要夾成 0，維持貼左，不能變成正的往右推
    $ _cam.enter_room(Room(name="narrow", background=None, bg_width=1200))
    $ assert _cam.offset == 0, f"窄背景 offset 應該夾成 0，實際 {_cam.offset}"

    # --- Room 的熱點增刪查 ---

    $ _room = Room(name="t", background=None)
    $ _hs = Hotspot(name="a", x=10, y=20)

    $ _room.add_hotspot(_hs)
    $ assert _room.get_hotspot("a") is _hs, "get_hotspot 應該找得到剛加進去的熱點"
    $ assert _room.get_hotspot("nope") is None, "找不到的名稱應該回傳 None"

    $ _room.remove_hotspot(_hs)
    $ assert _room.get_hotspot("a") is None, "remove_hotspot 之後應該找不到了"

    # 移除不存在的熱點不該爆掉
    $ _room.remove_hotspot(_hs)

    # 每個 Room 要有自己的 hotspots list，不能共用同一個
    $ _room2 = Room(name="t2", background=None)
    $ _room2.add_hotspot(Hotspot(name="b", x=0, y=0))
    $ assert len(_room.hotspots) == 0, "兩個 Room 不該共用同一個 hotspots list"

    # --- on_enter 簡寫會轉成一個 Event ---
    # 進房行為只有一套機制 (Event)，on_enter 只是它的簡寫入口。

    $ _r1 = Room(name="r1", background=None, on_enter="hello")
    $ assert len(_r1.events) == 1, "on_enter 應該轉成一個 Event"

    $ _e1 = _r1.events[0]
    $ assert _e1.id == "r1.on_enter", f"id 應該是「房間名.on_enter」，實際 {_e1.id}"
    $ assert _e1.effect.label == "hello", "Event 的 Effect 應該帶著那個 label"
    $ assert _e1.limit == 1, "on_enter_limit 預設是 1"
    $ assert _e1.sequence == -1000, "on_enter 應該排在所有事件最前面"
    $ assert _e1.condition is None, "on_enter 是無條件的"

    # limit=None：無限次
    $ _r2 = Room(name="r2", background=None, on_enter="x", on_enter_limit=None)
    $ assert _r2.events[0].limit is None

    # limit=2
    $ _r3 = Room(name="r3", background=None, on_enter="x", on_enter_limit=2)
    $ assert _r3.events[0].limit == 2

    # 沒設 on_enter 就不該產生 Event
    $ _r4 = Room(name="r4", background=None, on_enter_limit=None)
    $ assert _r4.events == [], "沒有 on_enter 就不該產生 Event"

    # 自己掛的 events 與 on_enter 產生的會並存
    $ _r5 = Room(name="r5", background=None, on_enter="x", events=[Event(id="r5.extra")])
    $ assert len(_r5.events) == 2, "自訂 events 與 on_enter 應該並存"

    # --- Hotspot 的狀態方法 ---

    $ _h = Hotspot(name="h", x=0, y=0)
    $ assert _h.visible and _h.enabled, "預設應該是可見且可用"

    $ _h.hide()
    $ assert not _h.visible, "hide() 之後 visible 應該是 False"
    $ _h.show()
    $ assert _h.visible, "show() 之後 visible 應該是 True"

    $ _h.disable()
    $ assert not _h.enabled, "disable() 之後 enabled 應該是 False"
    $ _h.enable()
    $ assert _h.enabled, "enable() 之後 enabled 應該是 True"

    # 每個 Hotspot 要有自己的 data dict
    $ _h2 = Hotspot(name="h2", x=0, y=0)
    $ _h.data["k"] = 1
    $ assert _h2.data == {}, "兩個 Hotspot 不該共用同一個 data dict"


# GameState 三個 section 的純邏輯測試。
# 這些都是自己建物件來測，不碰全域的 game_state，也不需要畫面。
testcase state_checks:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    # --- InventoryState：只存 key -> 數量 ---

    $ _inv = InventoryState()
    $ assert not _inv.has("key"), "一開始不該有東西"
    $ assert _inv.count_of("key") == 0, "沒有的物品數量應該是 0"

    $ _inv.add("key")
    $ assert _inv.has("key") and _inv.count_of("key") == 1

    # 同一個 key 再加會累加，不是覆蓋
    $ _inv.add("key", 2)
    $ assert _inv.count_of("key") == 3, f"應該累加成 3，實際 {_inv.count_of('key')}"

    # 移除一部分
    $ _inv.remove("key", 1)
    $ assert _inv.count_of("key") == 2

    # 移到 0 就整個消失，不留空殼
    $ _inv.remove("key", 99)
    $ assert not _inv.has("key"), "數量歸零後應該整個移除"
    $ assert "key" not in _inv.items, "不該留下數量為 0 的空殼"

    # 移除不存在的東西不該出錯
    $ _inv.remove("nothing")

    # 加 0 個或負數不該有作用
    $ _inv.add("ghost", 0)
    $ assert not _inv.has("ghost"), "加 0 個不該產生物品"

    $ _inv.add("a")
    $ _inv.reset()
    $ assert _inv.keys() == [], "reset 之後應該清空"

    # --- 物品目錄的一致性檢查 ---

    # dict key 與 Item.key 一致 -> 原樣回傳
    python:
        _good = {"key": Item(key="key", name="鑰匙")}
        assert validate_item_catalog(_good) is _good, "一致的目錄應該原樣回傳"

    # 不一致 -> 直接報錯。
    # 實際被使用的是 dict key，Item.key 只是給人看的，
    # 兩邊不一樣的話遊戲照跑但條件會查不到，所以寧可啟動時就爆掉。
    python:
        _bad = {"coin10": Item(key="coin", name="10元")}

        try:
            validate_item_catalog(_bad)
            assert False, "dict key 與 Item.key 不一致時應該要報錯"
        except ValueError as e:
            # 錯誤訊息要把兩個 key 都講出來，不然還是不知道哪裡錯
            assert "coin10" in str(e) and "coin" in str(e)

    # 空目錄不該出錯
    $ assert validate_item_catalog({}) == {}

    # --- FlagState ---

    $ _flags = FlagState()
    $ assert not _flags.has("cut_wire")

    $ _flags.set("cut_wire")
    $ assert _flags.has("cut_wire")

    # 重複 set 不該出錯，也不會變成兩個
    $ _flags.set("cut_wire")
    $ assert _flags.all_flags() == ["cut_wire"]

    $ _flags.clear("cut_wire")
    $ assert not _flags.has("cut_wire")

    # 清除不存在的旗標不該出錯
    $ _flags.clear("never_set")

    $ _flags.set("a")
    $ _flags.reset()
    $ assert _flags.all_flags() == []

    # --- EventState：觸發次數與死亡 ---

    $ _ev = EventState()
    $ assert _ev.count_of("e1") == 0
    $ assert not _ev.is_dead("e1")

    # limit=2：觸發一次還活著，第二次就死
    $ _ev.record_trigger("e1", 2)
    $ assert _ev.count_of("e1") == 1
    $ assert not _ev.is_dead("e1"), "limit=2 觸發一次還不該死"

    $ _ev.record_trigger("e1", 2)
    $ assert _ev.count_of("e1") == 2
    $ assert _ev.is_dead("e1"), "次數用完應該自動死亡"

    # limit=None：無限次，永遠不會因為次數而死
    $ _ev.record_trigger("e2", None)
    $ _ev.record_trigger("e2", None)
    $ _ev.record_trigger("e2", None)
    $ assert _ev.count_of("e2") == 3
    $ assert not _ev.is_dead("e2"), "limit=None 不該因為次數而死"

    # 可以被別人提前殺死
    $ _ev.kill("e2")
    $ assert _ev.is_dead("e2")

    # 也可以復活
    $ _ev.revive("e2")
    $ assert not _ev.is_dead("e2")

    $ _ev.reset()
    $ assert _ev.count_of("e1") == 0 and not _ev.is_dead("e1")

    # --- GameState 與 StateView ---

    $ _gs = GameState()
    $ _gs.inventory.add("key")
    $ _gs.flags.set("opened_door")

    $ _view = _gs.view()

    $ assert _view.has_item("key")
    $ assert _view.has_flag("opened_door")
    $ assert _view.item_count("key") == 1

    # 物品與旗標共用命名空間：has() 兩邊都查
    $ assert _view.has("key"), "has() 應該查得到物品"
    $ assert _view.has("opened_door"), "has() 應該查得到旗標"
    $ assert not _view.has("nothing")

    # StateView 是唯讀的：不該有任何會改狀態的方法
    $ assert not hasattr(_view, "add"), "StateView 不該暴露 add"
    $ assert not hasattr(_view, "set"), "StateView 不該暴露 set"
    $ assert not hasattr(_view, "remove"), "StateView 不該暴露 remove"

    # reset 要能一次清掉所有 section
    $ _gs.reset()
    $ assert not _gs.view().has("key") and not _gs.view().has("opened_door"), "reset 應該清掉所有 section"


# 事件系統的純邏輯測試：Condition / Effect / collect_events。
# collect_events 是純函式，餵假的 GameState 就能測，不需要畫面。
testcase event_checks:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    # --- Condition ---

    $ _gs = GameState()
    $ _gs.inventory.add("key")
    $ _gs.flags.set("saw_ghost")
    $ _v = _gs.view()

    # 沒設任何欄位 = 無條件通過
    $ assert Condition().test(_v), "空條件應該永遠通過"

    # require：全部都要有
    $ assert Condition(require=["key"]).test(_v)
    $ assert not Condition(require=["key", "map"]).test(_v), "缺一個就不該通過"

    # 可以直接傳字串，不用包 list
    $ assert Condition(require="key").test(_v), "require 應該接受字串"

    # 物品與旗標共用命名空間
    $ assert Condition(require=["saw_ghost"]).test(_v), "require 應該也查得到旗標"

    # require_any：至少要有一個
    $ assert Condition(require_any=["axe", "key"]).test(_v)
    $ assert not Condition(require_any=["axe", "crowbar"]).test(_v)

    # forbid：都不能有
    $ assert Condition(forbid=["ghost"]).test(_v)
    $ assert not Condition(forbid=["key"]).test(_v), "有被禁止的東西就不該通過"

    # 三者是 AND 關係
    $ assert not Condition(require=["key"], forbid=["saw_ghost"]).test(_v)

    # check 逃生艙
    $ _gs.inventory.add("coin", 3)
    $ assert Condition(check=lambda v: v.item_count("coin") >= 3).test(_gs.view())
    $ assert not Condition(check=lambda v: v.item_count("coin") >= 4).test(_gs.view())

    # --- Effect ---

    $ _gs2 = GameState()
    $ _eff = Effect(give_items=["key", ("coin", 5)], set_flags=["opened"], label="say_hi")
    $ _label = _eff.apply(_gs2)

    $ assert _label == "say_hi", "apply 應該回傳 label"
    $ assert _gs2.inventory.count_of("key") == 1
    $ assert _gs2.inventory.count_of("coin") == 5, "應該支援 (key, 數量) 寫法"
    $ assert _gs2.flags.has("opened")

    # 移除與清除
    $ Effect(remove_items=[("coin", 2)], clear_flags=["opened"]).apply(_gs2)
    $ assert _gs2.inventory.count_of("coin") == 3
    $ assert not _gs2.flags.has("opened")

    # kill_events
    $ Effect(kill_events=["some.event"]).apply(_gs2)
    $ assert _gs2.events.is_dead("some.event")

    # 沒有 label 的 Effect 回傳 None
    $ assert Effect(set_flags=["x"]).apply(_gs2) is None

    # --- collect_events：排序 ---

    $ _gs3 = GameState()
    $ _ctx = EventContext(_gs3)
    python:
        _events = [
            Event(id="t.c", sequence=30, effect=Effect(label="third"), limit=None),
            Event(id="t.a", sequence=10, effect=Effect(label="first"), limit=None),
            Event(id="t.b", sequence=20, effect=Effect(label="second"), limit=None),
        ]
    $ _labels = collect_events(_events, TriggerType.ENTER_ROOM, _ctx, TriggerType.ENTER_ROOM)
    $ assert _labels == ["first", "second", "third"], f"應該依 sequence 排序，實際 {_labels}"

    # --- collect_events：stop 中斷後續 ---

    $ _gs4 = GameState()
    $ _ctx4 = EventContext(_gs4)
    python:
        _events4 = [
            Event(id="s.a", sequence=10, effect=Effect(label="a"), stop=True, limit=None),
            Event(id="s.b", sequence=20, effect=Effect(label="b"), limit=None),
        ]
    $ _labels4 = collect_events(_events4, TriggerType.ENTER_ROOM, _ctx4, TriggerType.ENTER_ROOM)
    $ assert _labels4 == ["a"], f"stop 之後不該再檢查，實際 {_labels4}"
    $ assert _gs4.events.count_of("s.b") == 0, "被 stop 擋掉的事件不該記錄觸發"

    # --- collect_events：次數用完自動死亡，之後直接跳過 ---

    $ _gs5 = GameState()
    $ _ctx5 = EventContext(_gs5)
    $ _events5 = [Event(id="l.a", effect=Effect(label="once"), limit=1)]

    $ assert collect_events(_events5, TriggerType.ENTER_ROOM, _ctx5, TriggerType.ENTER_ROOM) == ["once"]
    $ assert _gs5.events.is_dead("l.a"), "limit=1 觸發後應該死亡"
    $ assert collect_events(_events5, TriggerType.ENTER_ROOM, _ctx5, TriggerType.ENTER_ROOM) == [], "死掉之後不該再觸發"

    # --- collect_events：條件不符就跳過，而且不該記錄觸發次數 ---

    $ _gs6 = GameState()
    $ _ctx6 = EventContext(_gs6)
    $ _events6 = [Event(id="c.a", condition=Condition(require=["key"]), effect=Effect(label="x"), limit=None)]

    $ assert collect_events(_events6, TriggerType.ENTER_ROOM, _ctx6, TriggerType.ENTER_ROOM) == []
    $ assert _gs6.events.count_of("c.a") == 0, "條件不符不該算觸發過"

    $ _gs6.inventory.add("key")
    $ assert collect_events(_events6, TriggerType.ENTER_ROOM, _ctx6, TriggerType.ENTER_ROOM) == ["x"]

    # --- collect_events：前面的 Effect 要能影響後面的 Condition ---
    # 這是刻意的設計：同一次派發裡，撿到鑰匙的下一個事件就該看得到鑰匙

    $ _gs7 = GameState()
    $ _ctx7 = EventContext(_gs7)
    python:
        _events7 = [
            Event(id="chain.give", sequence=10, effect=Effect(give_items=["key"]), limit=None),
            Event(id="chain.use", sequence=20, condition=Condition(require=["key"]), effect=Effect(label="used"), limit=None),
        ]
    $ _labels7 = collect_events(_events7, TriggerType.ENTER_ROOM, _ctx7, TriggerType.ENTER_ROOM)
    $ assert _labels7 == ["used"], f"後面的條件應該看得到前面 Effect 的改動，實際 {_labels7}"

    # --- collect_events：trigger 過濾 ---

    $ _gs8 = GameState()
    $ _ctx8 = EventContext(_gs8)
    python:
        _events8 = [
            Event(id="tr.enter", effect=Effect(label="on_enter"), limit=None),
            Event(id="tr.click", trigger=TriggerType.CLICK_HOTSPOT, effect=Effect(label="on_click"), limit=None),
        ]

    # 沒指定 trigger 的用掛載位置的預設值
    $ _r8 = collect_events(_events8, TriggerType.ENTER_ROOM, _ctx8, TriggerType.ENTER_ROOM)
    $ assert _r8 == ["on_enter"], f"只該跑符合時機的，實際 {_r8}"

    $ _r8b = collect_events(_events8, TriggerType.CLICK_HOTSPOT, _ctx8, TriggerType.ENTER_ROOM)
    $ assert _r8b == ["on_click"], f"明確指定 trigger 的應該只在該時機跑，實際 {_r8b}"

    # --- 空清單不該出錯 ---

    $ assert collect_events(None, TriggerType.ENTER_ROOM, _ctx8) == []
    $ assert collect_events([], TriggerType.ENTER_ROOM, _ctx8) == []


# 物品欄與條件事件的完整流程：
#   撿鑰匙 -> 熱點自動消失 -> 物品欄出現 -> 用鑰匙開櫃子 -> 拿到紙條 -> 再點變成空的
testcase inventory_flow:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _trace_reset()

    click "開始"
    advance until "走去廚房"

    # 一開始物品欄是空的，鑰匙熱點看得到
    $ assert not game_state.inventory.keys(), "開場物品欄應該是空的"
    assert "生鏽的鑰匙"
    assert "(無)"

    # --- 撿鑰匙 ---
    click "生鏽的鑰匙"
    advance until "走去廚房"
    $ _trace("1_撿到鑰匙")

    $ assert game_state.inventory.has("key"), "撿完應該有 key"
    $ assert game_state.inventory.count_of("key") == 1

    # 熱點的 condition 是 forbid=["key"]，撿走之後應該自動消失。
    # 用完整的 label 文字 (含 emoji) 來比對，才不會跟物品欄裡的名稱搞混。
    assert not "🔑 生鏽的鑰匙"

    # 物品欄現在該顯示它了 (名稱是即時查 item_catalog 得到的)
    assert "生鏽的鑰匙"
    assert not "(無)"

    # --- 去廚房用鑰匙開櫃子 ---
    click "走去廚房"
    advance until "上鎖的櫃子"
    $ _trace("2_進廚房")

    click "上鎖的櫃子"
    advance until "上鎖的櫃子"
    $ _trace("3_開櫃子")

    $ assert game_state.flags.has("locker_opened"), "有鑰匙就該開得了櫃子"
    $ assert game_state.inventory.has("note"), "開櫃子應該拿到紙條"

    # --- 再點一次，這次該講「空了」 ---
    # locker_open 已死、locker_locked 因為 locker_opened 而不成立，
    # 只剩 locker_empty 會觸發
    click "上鎖的櫃子"
    advance until "上鎖的櫃子"
    $ _trace("4_再點一次櫃子")

    # 紙條只該拿到一張 —— 這是玩家看得到的不變量。
    #
    # 這裡刻意不去斷言「哪個 event 死了」：event id 與 limit 設定是 demo 的內容，
    # 隨時可能被調整 (實際上就被改過一次，害這個測試誤報)。
    # limit 用完會死亡這個「機制」由 event_checks 用自建的 Event 驗證，
    # 不受 demo 怎麼寫影響。
    $ assert game_state.inventory.count_of("note") == 1, "紙條不該拿到第二張"

    # --- 點物品欄的物品會顯示描述 ---
    click "潮濕的紙條"
    pause 0.5
    $ assert renpy.get_screen("page_popup") is not None, "點物品應該跳出說明視窗"

    click "關閉"
    pause 0.5
    $ assert renpy.get_screen("page_popup") is None
    $ _trace("5_看完物品說明")


# 沒有鑰匙的時候，同一個熱點要講不一樣的話。
testcase locked_without_key:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    click "開始"
    advance until "走去廚房"

    # 這次刻意不撿鑰匙，直接去廚房
    click "走去廚房"
    advance until "上鎖的櫃子"

    $ assert not game_state.inventory.has("key"), "這個測試不該有鑰匙"

    click "上鎖的櫃子"
    advance until "上鎖的櫃子"

    # 條件不成立，所以櫃子沒開、也沒拿到紙條
    $ assert not game_state.flags.has("locker_opened"), "沒鑰匙不該開得了櫃子"
    $ assert not game_state.inventory.has("note")

    # 重複點也一樣 —— 沒鑰匙就是打不開，而且不會因為點過就失去機會。
    #
    # 這裡同樣不斷言具體的 event id 或觸發次數：那些是 demo 的內容。
    # 「條件不符不算觸發過、也不會死亡」這個機制由 event_checks 驗證。
    click "上鎖的櫃子"
    advance until "上鎖的櫃子"

    $ assert not game_state.flags.has("locker_opened"), "重複點還是不該開得了"
    $ assert not game_state.inventory.has("note")

    # 熱點還在，玩家之後拿到鑰匙還能回來開
    assert "上鎖的櫃子"


# 已經修好的 bug 的回歸測試。
# 這兩個問題都是實際發生過、使用者回報的，所以留下測試防止再犯。
testcase regression_fixes:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _trace_reset()

    click "開始"
    advance until "走去廚房"

    ##############################################
    # bug 1: 進房間的開場白講完後，對話框沒有收起來
    #        (say_in_room 少了 window hide)
    ##############################################
    $ _trace("1_開場白結束")
    $ assert renpy.get_screen("say") is None, "開場白講完後對話框應該要收起來"

    # 點熱點講話，講完之後也一樣要收
    click "走去廚房"
    advance until "打開冰箱"
    $ _trace("2_熱點對話結束")
    $ assert renpy.get_screen("say") is None, "熱點對話講完後對話框應該要收起來"

    ##############################################
    # bug 2: F10 釘住的房間座標會隨著滑鼠移動而改變
    #        (原本只存螢幕座標，事後才用當下的 offset 換算)
    ##############################################
    keysym "K_F9"
    pause 0.3
    $ assert renpy.get_screen("explore_debug") is not None

    # 先確認 F10 這個按鍵真的有綁到 pin 函式
    keysym "K_F10"
    pause 0.3
    $ _trace("3_按F10釘住座標")
    $ assert debug_pinned_pos is not None, "F10 應該要釘住座標"

    # 舊版只存 (螢幕x, 螢幕y) 兩個值，房間座標是顯示時才用當下的 offset 算的，
    # 所以鏡頭一動數字就跟著跑。現在要存三個值，房間座標在釘住當下就算好。
    $ assert len(debug_pinned_pos) == 3, "釘住的資料應該是 (螢幕x, 螢幕y, 房間x) 三個值"

    # 換算的正確性直接呼叫函式來驗，不透過按鍵。
    #
    # 用按鍵的話，「按下的那一刻」跟「事後讀 camera.offset」之間隔了好幾幀，
    # 鏡頭還在收斂中，兩個值不一樣，算出來的期望值就對不上。
    # 包在同一個 python 區塊裡就沒有這個問題 —— 區塊內不會有畫面更新。
    python:
        pin_debug_pos()

        _offset_at_pin = int(camera.offset)
        _pinned = debug_pinned_pos
        _sx, _sy, _rx = _pinned

        assert _rx == _sx - _offset_at_pin, \
            f"房間座標應該是釘住當下換算的，期望 {_sx - _offset_at_pin}，實際 {_rx}"

    # 直接改 camera.offset 來模擬鏡頭移動。
    #
    # 這裡刻意「不」用滑鼠去推鏡頭：camera.update() 讀的是真實游標位置，
    # 而測試框架的 move 影響不到它，renpy.set_mouse_pos() 又會受視窗焦點影響
    # (實測過會時靈時不靈)，把測試建立在那上面等於在賭執行環境。
    #
    # 整段包在同一個 python 區塊裡是必要的：區塊內不會有畫面更新，
    # camera.update() 沒機會把 offset 拉回去，斷言才有意義。
    python:
        _offset_before = camera.offset
        camera.offset = _offset_before - 400.0

        assert abs(camera.offset - _offset_before) > 100, \
            f"鏡頭應該要明顯移動過，實際只從 {_offset_before} 變到 {camera.offset}"

        # 這就是 bug 的核心：釘住的值不該因為鏡頭移動而改變
        assert debug_pinned_pos == _pinned, \
            f"釘住的座標不該改變，原本 {_pinned} 變成 {debug_pinned_pos}"

    $ _trace("4_鏡頭移到別的位置")

    keysym "K_F9"
    pause 0.3
    $ _trace("5_收起面板")


# 翻頁視窗的邊界情況。
testcase popup_edge_cases:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    click "開始"
    advance until "看說明"

    # --- ESC 要能關掉視窗 ---
    # page_popup 裡有 key "game_menu" action Return()，
    # 沒攔截的話按 ESC 會跳出 Ren'Py 的遊戲選單而不是關閉視窗。
    click "看說明"
    pause 0.5
    $ assert renpy.get_screen("page_popup") is not None, "視窗應該要打開"

    keysym "K_ESCAPE"
    pause 0.8
    $ assert renpy.get_screen("page_popup") is None, "ESC 應該要關掉視窗"
    $ assert renpy.get_screen("save") is None, "ESC 不該跳出遊戲選單"
    $ assert renpy.get_screen("explore") is not None, "關掉視窗後應該回到探索畫面"

    # --- 只有一頁時，不該出現翻頁按鈕 ---
    $ renpy.show_screen("page_popup", pages=[{"title": "單頁", "text": "只有一頁的內容"}])
    pause 0.5
    $ assert renpy.get_screen("page_popup") is not None

    # 注意：測試框架的文字選擇器走的是 find_focus，只找得到「可聚焦的元件」(按鈕)。
    # 標題、說明文字這種純 text 永遠找不到，不能拿來當斷言對象。
    # 所以這裡只檢查按鈕：單頁時翻頁鈕要消失、關閉鈕要在。
    assert not "下一頁"
    assert not "上一頁"
    assert "關閉"

    $ renpy.hide_screen("page_popup")
    pause 0.3

    # --- 空的 pages 不該讓遊戲爆掉 ---
    # screen 裡有 if not pages: timer 0.01 action Return() 這道保險
    $ renpy.show_screen("page_popup", pages=[])
    pause 0.5
    $ renpy.hide_screen("page_popup")
    pause 0.3
    $ assert renpy.get_screen("explore") is not None, "空頁面不該影響探索畫面"


# hotspot.visible 對畫面的實際影響。
# unit_checks 只驗證了屬性值有沒有被改到，
# 這裡驗證改了之後畫面上是不是真的看不到、點不到。
testcase hotspot_visibility:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    click "開始"
    advance until "看說明"

    # 一開始看得到
    assert "看說明"

    # 隱藏之後就不該出現在畫面上
    $ current_room.get_hotspot("help").hide()
    $ renpy.restart_interaction()
    pause 0.5
    assert not "看說明"

    # 其他熱點不受影響
    assert "走去廚房"

    # 放回來又看得到
    $ current_room.get_hotspot("help").show()
    $ renpy.restart_interaction()
    pause 0.5
    assert "看說明"
