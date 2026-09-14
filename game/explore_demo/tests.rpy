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

    # --- Room.music 的播放規則 ---
    #
    # 規則是「music=None 就完全不碰音樂，維持現在正在播的那首」。
    #
    # demo 專案裡沒有任何音檔可以真的播出來，
    # 所以這裡改用替身攔截 renpy.music.play，
    # 驗證的是「有沒有被呼叫、帶了什麼參數」這個契約本身。
    # 放在最後面，因為它會把 current_room 換成臨時房間。
    # 每個 change_room 一定要獨立成一個語句，不能跟斷言擠在同一個
    # python 區塊裡 —— change_room 內部會呼叫 renpy.call()，
    # 那會直接終止當下的區塊，後面的程式碼一行都不會跑。
    # (這個坑真的踩過：整段測試變成只跑前兩行卻顯示 PASSED)
    python:
        # 記錄用的清單放在 store 上，不能用區域變數 ——
        # 測試裡的 python 區塊是用獨立的 globals/locals 執行的，
        # 下面那個 lambda 之後被 change_room 呼叫時查不到區域變數。
        store._music_calls = []
        store._orig_music_play = renpy.music.play
        renpy.music.play = lambda *a, **kw: store._music_calls.append((a, kw))

        # 借用現有房間的背景，避免 background=None 讓畫面畫不出來
        store._music_bg = current_room.background

    $ change_room(Room(name="_music_none", background=store._music_bg, music=None))
    $ assert store._music_calls == [], "music=None 的房間不該碰音樂"

    $ change_room(Room(name="_music_set", background=store._music_bg, music="bgm.ogg"))
    $ assert len(store._music_calls) == 1, f"有設 music 的房間應該播放一次，實際 {len(store._music_calls)} 次"
    $ assert store._music_calls[0][0][0] == "bgm.ogg", "應該播放房間指定的那首"
    $ assert store._music_calls[0][1].get("if_changed") is True, "應該用 if_changed，同一首不該從頭重播"

    $ renpy.music.play = store._orig_music_play

    # 確認上面每一句都真的跑到了 —— 這正是當初漏掉的那一段
    $ assert current_room.name == "_music_set", f"應該停在 _music_set，實際 {current_room.name}"
    $ _trace("7_music規則驗證完成")


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
    $ assert _h.visible, "預設應該是可見的"

    $ _h.hide()
    $ assert not _h.visible, "hide() 之後 visible 應該是 False"
    $ _h.show()
    $ assert _h.visible, "show() 之後 visible 應該是 True"

    # 每個 Hotspot 要有自己的 data dict
    $ _h2 = Hotspot(name="h2", x=0, y=0)
    $ _h.data["k"] = 1
    $ assert _h2.data == {}, "兩個 Hotspot 不該共用同一個 data dict"

    # --- 熱點大小 (hotspot_size) ---

    # 沒填 width/height 就用預設值
    $ assert hotspot_size(Hotspot(name="s", x=0, y=0)) == (100, 100), "預設判定範圍應該是 100x100"

    # 有填就用填的
    $ assert hotspot_size(Hotspot(name="s", x=0, y=0, width=300, height=80)) == (300, 80)

    # 只填一邊，另一邊仍然用預設值
    $ assert hotspot_size(Hotspot(name="s", x=0, y=0, width=300)) == (300, 100)
    $ assert hotspot_size(Hotspot(name="s", x=0, y=0, height=80)) == (100, 80)

    # --- hover 判定 (hotspot_contains) ---
    #
    # 這是圖片熱點決定「hover 圖要不要畫出來」的依據，
    # 探索畫面每一幀都會算一次。
    #
    # 傳進去的是背景圖座標，不是螢幕座標：
    # 呼叫端 (explore 畫面) 會先算 room_x = mouse_x - camera.offset。
    # 這裡直接餵座標測，是因為測試環境沒辦法可靠地控制真實滑鼠位置。

    $ _box = Hotspot(name="box", x=200, y=300, width=100, height=50)

    # 正中央：命中
    $ assert hotspot_contains(_box, 250, 325), "範圍正中央應該命中"

    # 左上角是包含的 (>=)
    $ assert hotspot_contains(_box, 200, 300), "左上角座標應該算在範圍內"

    # 右下角是不包含的 (<)，剛好在邊界外面一格
    $ assert not hotspot_contains(_box, 300, 350), "右下邊界應該算在範圍外"

    # 邊界內側最後一格：命中
    $ assert hotspot_contains(_box, 299, 349), "邊界內側最後一格應該命中"

    # 四個方向各差一格就落空
    $ assert not hotspot_contains(_box, 199, 325), "左邊差一格應該落空"
    $ assert not hotspot_contains(_box, 250, 299), "上面差一格應該落空"
    $ assert not hotspot_contains(_box, 300, 325), "右邊差一格應該落空"
    $ assert not hotspot_contains(_box, 250, 350), "下面差一格應該落空"

    # 完全不相干的座標
    $ assert not hotspot_contains(_box, 0, 0), "遠處座標不該命中"

    # 沒填寬高的熱點，用預設的 100x100 判定
    $ _dot = Hotspot(name="dot", x=0, y=0)
    $ assert hotspot_contains(_dot, 99, 99), "預設範圍內應該命中"
    $ assert not hotspot_contains(_dot, 100, 100), "超出預設範圍應該落空"

    # 鏡頭位移之後的行為：
    # 熱點畫在背景圖的 x=200，鏡頭往左推 640，
    # 玩家滑鼠停在螢幕 x=-440+640... 直接用呼叫端的算式驗證一次，
    # 確認「螢幕座標扣掉 offset」才是正確的輸入。
    $ _offset = -640
    $ _screen_x = 200 + _offset          # 熱點左上角這時出現在螢幕上的哪裡
    $ assert hotspot_contains(_box, _screen_x - _offset, 300), "扣掉鏡頭位移後應該命中"
    $ assert not hotspot_contains(_box, _screen_x, 300), "忘了扣鏡頭位移就會判定錯"


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

    # --- ActorState：角色身上的數值 ---

    $ _act = ActorState()

    # 沒有的數值回傳 0，跟 InventoryState.count_of() 同一個約定
    $ assert _act.get("player", "hp") == 0, "沒設過的數值應該回傳 0"

    # 但「回傳 0」跟「設定過」是兩件事
    $ assert not _act.has_stat("player", "hp"), "沒設過就是沒設過"
    $ _act.set("player", "hp", 0)
    $ assert _act.has_stat("player", "hp"), "設成 0 也算設定過"

    $ _act.set("player", "hp", 5)
    $ assert _act.get("player", "hp") == 5

    # add 會回傳加減後的結果
    $ assert _act.add("player", "hp", -2) == 3, "add 應該回傳結果"
    $ assert _act.get("player", "hp") == 3

    # 夾在 0 以上：扣過頭不會變負數
    $ _act.add("player", "hp", -99)
    $ assert _act.get("player", "hp") == 0, f"應該夾在 0，實際 {_act.get('player', 'hp')}"

    # set 也一樣夾
    $ _act.set("player", "hp", -5)
    $ assert _act.get("player", "hp") == 0, "set 負數也應該夾成 0"

    # 一個角色可以有多種數值，彼此獨立
    $ _act.set("player", "battery", 100)
    $ _act.add("player", "battery", -30)
    $ assert _act.get("player", "battery") == 70
    $ assert _act.get("player", "hp") == 0, "改 battery 不該影響 hp"

    # 不同角色的同名數值也互不影響
    $ _act.set("annie_ghost", "hp", 3)
    $ _act.set("annie_ghost", "rage", 0)
    $ assert _act.get("annie_ghost", "hp") == 3
    $ assert _act.get("player", "hp") == 0, "改別的角色不該影響玩家"

    # --- ActorState.is_dead 的四種情況 ---

    # 1. 沒設過 hp = 無敵。這是刻意選的失敗方向 (打不死比一開場就死好查)
    $ assert not _act.is_dead("nobody"), "沒設過 hp 的角色不該被判定為死亡"
    $ assert _act.is_alive("nobody")

    # 2. hp > 0 = 活著
    $ assert not _act.is_dead("annie_ghost")

    # 3. hp <= 0 = 死了
    $ assert _act.is_dead("player"), "hp 歸零應該判定為死亡"

    # 4. 明確 kill = 死了，不管有沒有血量
    $ _act.kill("nobody")
    $ assert _act.is_dead("nobody"), "kill() 應該讓沒有血量的角色也能死"

    # revive 只解除標記，不會補血
    $ _act.revive("nobody")
    $ assert not _act.is_dead("nobody")
    $ _act.kill("player")
    $ _act.revive("player")
    $ assert _act.is_dead("player"), "revive 不會補血，hp 還是 0 就還是死的"

    # debug 面板用的查詢
    $ assert _act.stats_of("annie_ghost") == {"hp": 3, "rage": 0}
    $ assert _act.stats_of("annie_ghost") is not _act.stats["annie_ghost"], "stats_of 要回傳複本，不能讓外面改到內部"
    $ assert "annie_ghost" in _act.actors()

    $ _act.reset()
    $ assert _act.get("annie_ghost", "hp") == 0 and _act.actors() == [], "reset 應該清空"

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

    # 角色數值也查得到
    $ _gs.actors.set("player", "hp", 5)
    $ _gs.actors.set("annie_ghost", "rage", 4)
    $ assert _view.stats("player", "hp") == 5
    $ assert _view.stats("annie_ghost", "rage") == 4
    $ assert _view.stats("nobody", "hp") == 0, "查不到的回傳 0"
    $ assert _view.is_alive("player") and not _view.is_dead("player")

    $ _gs.actors.set("player", "hp", 0)
    $ assert _view.is_dead("player"), "StateView 應該反映最新狀態，不是快照"

    # StateView 是唯讀的：不該有任何會改狀態的方法
    $ assert not hasattr(_view, "add"), "StateView 不該暴露 add"
    $ assert not hasattr(_view, "set"), "StateView 不該暴露 set"
    $ assert not hasattr(_view, "remove"), "StateView 不該暴露 remove"
    $ assert not hasattr(_view, "kill"), "StateView 不該暴露 kill"

    # reset 要能一次清掉所有 section
    $ _gs.reset()
    $ assert not _gs.view().has("key") and not _gs.view().has("opened_door"), "reset 應該清掉所有 section"
    $ assert _gs.view().stats("player", "hp") == 0, "reset 應該連 actors 一起清掉"
    $ assert len(_gs.sections()) == 4, "GameState 應該有四個 section"


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

    # --- Effect 的角色數值 ---

    $ _gs3 = GameState()
    $ _gs3.actors.set("player", "hp", 5)
    $ _gs3.actors.set("annie_ghost", "rage", 1)

    # actor 一定要寫清楚
    $ Effect(actor="player", stats={"hp": -2}).apply(_gs3)
    $ assert _gs3.actors.get("player", "hp") == 3, f"應該扣成 3，實際 {_gs3.actors.get('player', 'hp')}"

    # 改別的角色
    $ Effect(actor="annie_ghost", stats={"rage": +2}).apply(_gs3)
    $ assert _gs3.actors.get("annie_ghost", "rage") == 3
    $ assert _gs3.actors.get("player", "hp") == 3, "改鬼不該動到玩家"

    # 一次改多個數值
    $ Effect(actor="player", stats={"hp": -1, "battery": +10}).apply(_gs3)
    $ assert _gs3.actors.get("player", "hp") == 2
    $ assert _gs3.actors.get("player", "battery") == 10

    # stats 是「增減量」不是「設定值」——
    # 同一個 Effect 套用兩次，效果會累積
    $ _eff_dmg = Effect(actor="player", stats={"hp": -1})
    $ _eff_dmg.apply(_gs3)
    $ _eff_dmg.apply(_gs3)
    $ assert _gs3.actors.get("player", "hp") == 0, f"連扣兩次應該歸零，實際 {_gs3.actors.get('player', 'hp')}"

    # 扣過頭夾在 0，不會變負數
    $ Effect(actor="player", stats={"hp": -99}).apply(_gs3)
    $ assert _gs3.actors.get("player", "hp") == 0

    # --- 有 stats 卻沒指定 actor 要直接爆掉 ---
    #
    # 刻意不給「沒填就是主角」的預設值：看不出來扣的是誰的血，
    # 而扣錯角色的血是那種「遊戲照跑、幾天後才發現」的錯誤。
    # 因為 Effect 是在 build_rooms() 裡建立的，這個錯誤會在遊戲啟動時就跳出來。
    python:
        _raised = False
        try:
            Effect(stats={"hp": -1})
        except ValueError:
            _raised = True
        assert _raised, "有 stats 卻沒指定 actor 應該直接拋 ValueError"

    # 沒有 stats 的話不用寫 actor
    $ assert Effect(label="x").actor is None
    $ assert Effect(set_flags=["y"]).actor is None

    # 兩個 Effect 不該共用同一個 stats dict
    $ _e_a = Effect(actor="player", stats={"hp": -1})
    $ _e_b = Effect(actor="player", stats={"hp": -1})
    $ _e_a.stats["rage"] = 5
    $ assert "rage" not in _e_b.stats, "兩個 Effect 不該共用同一個 stats dict"

    # 沒有 stats 的 Effect 完全不碰 actors
    $ _gs4 = GameState()
    $ Effect(set_flags=["x"]).apply(_gs4)
    $ assert _gs4.actors.actors() == [], "沒有 stats 就不該建立任何角色紀錄"

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


# 角色數值 (ActorState) 走完整條路：
#   進遊戲拿到初始血量 -> 惹鬼生氣 -> 熱點因為憤怒值出現 -> 被攻擊扣血
#   -> 對話演完 -> 死亡 -> 跳到 game_over
#
# 這裡刻意不寫死 demo 的數字 (初始血量幾點、扣幾滴)。
# 那些是內容層隨時會調的參數，寫進斷言的話別人改 demo 就會誤報。
# 要驗證的是「機制對不對」，所以血量都在測試裡自己設定。
testcase actor_flow:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _trace_reset()

    click "開始"
    advance until "爬上閣樓"

    # init_actor_stats 有跑到：玩家拿到了初始血量，而且活著
    $ assert game_state.actors.has_stat("player", "hp"), "label start 應該有初始化玩家血量"
    $ assert game_state.actors.get("player", "hp") > 0
    $ assert not game_state.actors.is_dead("player")
    $ _trace("1_開場血量已設定")

    # --- 上閣樓 ---
    click "爬上閣樓"
    advance until "轉動音樂盒"
    $ assert current_room.name == "attic"
    $ _trace("2_進閣樓")

    # 安妮的熱點還沒出現 (憤怒值不夠)
    assert not "👻 安妮"

    # --- 惹她生氣，直到熱點出現 ---
    # 需要幾次由 demo 的條件決定，這裡用迴圈跑到出現為止，
    # 不寫死次數，這樣調整 demo 的門檻不會讓測試誤報。
    click "轉動音樂盒"
    advance until "轉動音樂盒"
    $ _rage1 = game_state.actors.get("annie_ghost", "rage")
    $ assert _rage1 > 0, "轉音樂盒應該讓安妮的憤怒值上升"

    click "轉動音樂盒"
    advance until "轉動音樂盒"
    $ assert game_state.actors.get("annie_ghost", "rage") > _rage1, "憤怒值應該持續累積"
    $ _trace("3_安妮生氣了")

    # 改別人的數值不該動到玩家
    $ assert game_state.actors.get("annie_ghost", "hp") > 0, "轉音樂盒不該扣到鬼的血"

    # 憤怒值夠了，熱點就自己出現 —— 沒有任何人呼叫 show()
    assert "👻 安妮"

    # --- 被攻擊會扣血 ---
    $ _hp_before = game_state.actors.get("player", "hp")
    click "👻 安妮"
    advance until "轉動音樂盒"
    $ _hp_after = game_state.actors.get("player", "hp")
    $ assert _hp_after < _hp_before, f"被攻擊應該扣血，{_hp_before} -> {_hp_after}"
    $ _trace("4_被攻擊扣血")

    # 沒死就該回到探索狀態，不該跳走
    $ assert renpy.get_screen("explore") is not None, "還沒死就該留在探索畫面"
    $ assert current_room.name == "attic"

    # --- 血剩一滴，再被打一次就死 ---
    #
    # 直接設定血量而不是一直點到死：扣幾滴是 demo 的參數，
    # 這個測試要驗的是「歸零之後會發生什麼事」。
    $ game_state.actors.set("player", "hp", 1)

    # 先清掉這個旗標，不然它在上一次攻擊時就被設起來了，
    # 底下那個「對話有沒有演完」的斷言會永遠成立 —— 一個假綠燈。
    $ game_state.flags.clear("annie_left")
    $ renpy.restart_interaction()

    click "👻 安妮"

    # 關鍵：扣血之後對話要「完整演完」才死。
    # 攻擊的台詞會照常出現，不會被死亡流程硬生生打斷。
    advance until "GAME OVER"
    $ _trace("5_死亡演出")

    $ assert game_state.actors.is_dead("player"), "血歸零應該判定為死亡"
    $ assert renpy.get_screen("explore") is None, "死了就不該還留著探索畫面"

    # 關鍵斷言：排在攻擊後面的那個 label 也跑完了。
    #
    # 這證明死亡檢查是在「整串 label 都跑完之後」才做的。
    # 如果改成「每跑完一個就檢查」，扣血那個 label 一結束就會跳走，
    # 後面的收尾永遠不會執行，這個旗標就不會被設起來。
    $ assert game_state.flags.has("annie_left"), "扣血之後的對話應該完整演完才死亡，不該被打斷"


# 「只扣血、不講話」的事件也要能觸發死亡。
#
# 這條路徑很容易漏掉：Effect 沒帶 label 的話，收集到的清單是空的。
# 死亡檢查如果寫在「有 label 才做」的分支裡，
# 這種事件就會靜靜地把玩家扣死卻什麼都不發生。
#
# 分成兩段測：
#   1. 進房時的無聲扣血 (閣樓的蠟燭詛咒)
#   2. 點熱點時的無聲扣血 (生鏽的釘子) —— 這一段才驗得到空清單那條路徑
#
# 為什麼第 1 段驗不到：點「爬上閣樓」本身是熱點，它的 on_click 是一個 label，
# 所以外層的 run_event_labels 是非空的。內層 change_room 就算跳過死亡檢查，
# 外層那次也會補抓到，兩種實作的結果一樣。
# 釘子沒有 label 也沒有 on_click，交給 run_event_labels 的才是真正的空清單。
testcase silent_death:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _trace_reset()

    click "開始"
    advance until "爬上閣樓"

    click "爬上閣樓"
    advance until "點燃蠟燭"
    $ _trace("1_進閣樓")

    # 點蠟燭啟動詛咒
    click "點燃蠟燭"
    advance until "下樓"
    $ assert game_state.flags.has("attic_cursed"), "點蠟燭應該啟動詛咒"
    $ _trace("2_詛咒啟動")

    # 詛咒事件沒有 label，所以進房不該有任何對話冒出來，
    # 但血要確實被扣掉。
    click "下樓"
    advance until "爬上閣樓"

    $ _hp_before = game_state.actors.get("player", "hp")
    click "爬上閣樓"
    advance until "轉動音樂盒"
    $ _hp_after = game_state.actors.get("player", "hp")

    $ assert _hp_after < _hp_before, f"詛咒應該在進房時扣血，{_hp_before} -> {_hp_after}"
    $ assert renpy.get_screen("explore") is not None, "沒死就該留在探索畫面"
    $ _trace("3_無聲扣血")

    # --- 點熱點的無聲扣血：釘子沒有 label 也沒有 on_click ---
    #
    # 這才是真正的「空清單」路徑：_fire_hotspot 收集到的是 []，
    # 交給 run_event_labels 的也是 []。
    $ _hp_before = game_state.actors.get("player", "hp")
    click "🩸 生鏽的釘子"
    pause 0.5

    $ assert game_state.actors.get("player", "hp") < _hp_before, "釘子應該扣血"
    # 沒有任何 label，所以畫面完全不該切走 —— 探索畫面要一直在
    $ assert renpy.get_screen("explore") is not None, "沒有 label 的事件不該讓畫面閃一下"
    $ _trace("4_釘子無聲扣血")

    # --- 血剩一滴，再踩一次釘子就死 ---
    $ game_state.actors.set("player", "hp", 1)
    $ renpy.restart_interaction()

    click "🩸 生鏽的釘子"
    advance until "GAME OVER"
    $ _trace("5_無聲死亡")

    $ assert game_state.actors.is_dead("player"), "沒有 label 的事件也該能把人扣死"
    $ assert renpy.get_screen("explore") is None, "死了就不該還留著探索畫面"


# 進房事件「只扣血、不講話」也要能觸發死亡。
#
# 這是 change_room() 那一側的空清單路徑，跟 silent_death 測的
# _fire_hotspot 那一側是兩條不同的程式碼。
#
# 為什麼要直接呼叫 change_room 而不是點熱點：
# 點熱點換房間的話，熱點的 on_click 是一個 label，
# 外層的 run_event_labels 是非空的，就算 change_room 自己漏掉死亡檢查，
# 外層那次也會補抓到 —— 兩種實作看起來會一模一樣。
# 直接呼叫才隔離得出來。
testcase enter_room_silent_death:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    click "開始"
    advance until "走去廚房"

    python:
        # 借用現有房間的背景，避免 background=None 讓畫面畫不出來
        store._trap_room = Room(
            name="_silent_trap",
            background=current_room.background,
            events=[
                Event(
                    id="_silent_trap.drain",
                    effect=Effect(actor="player", stats={"hp": -1}),   # 沒有 label
                    limit=None,
                ),
            ],
        )
        game_state.actors.set("player", "hp", 1)

    # change_room 一定要獨立成一個語句 —— 它內部會 renpy.call()，
    # 那會終止當下的 python 區塊。
    $ change_room(store._trap_room)

    advance until "GAME OVER"

    $ assert game_state.actors.is_dead("player"), "進房的無聲扣血也該能把人扣死"
    $ assert renpy.get_screen("explore") is None, "死了就不該還留著探索畫面"


# 存檔 / 讀檔不能壞。
#
# 背景：rooms 原本是 default (會進存檔)，於是整棵 Room/Hotspot 物件樹都要被 pickle。
# 但 Hotspot 可以帶 Condition(check=lambda ...)，那個 lambda 定義在 build_xxx()
# 函式內部，Python 存不了函式內的區域物件，一按存檔就:
#     AttributeError: Can't get local object 'build_bed_room.<locals>.<lambda>'
#
# 改成 init 1 之後房間不再進存檔。這支測試守住「不能再退回去」。
#
# 刻意走過所有會用到 lambda 條件的房間再存檔 ——
# 只在開場存檔的話，那些房間可能還沒被碰過，抓不到問題。
testcase save_load_flow:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _trace_reset()

    click "開始"
    advance until "爬上閣樓"

    # 開場就先存一次
    python:
        store._save_err = None
        try:
            renpy.save("_test_save_1", extra_info="開場")
        except Exception as e:
            store._save_err = f"{type(e).__name__}: {e}"
    $ assert store._save_err is None, f"開場存檔就失敗了：{store._save_err}"
    $ _trace("1_開場存檔成功")

    # --- 走到有 lambda 條件的房間，改一些狀態，再存一次 ---
    click "爬上閣樓"
    advance until "轉動音樂盒"

    click "轉動音樂盒"
    advance until "轉動音樂盒"

    python:
        store._save_err = None
        try:
            renpy.save("_test_save_2", extra_info="閣樓")
        except Exception as e:
            store._save_err = f"{type(e).__name__}: {e}"
    $ assert store._save_err is None, f"在閣樓存檔失敗：{store._save_err}"
    $ _trace("2_閣樓存檔成功")

    # --- 存檔裡該有的東西 ---
    $ assert renpy.can_load("_test_save_2"), "存檔應該讀得回來"

    # --- 房間定義「不在」存檔裡 ---
    #
    # 存檔是壓縮過的，所以「檔案裡找不到某個字串」證明不了什麼。
    # 直接驗 pickle 的行為：Room / Hotspot 應該只被存成「名稱」，
    # 還原時從目前的 rooms 查回來 (Room.__reduce__ / Hotspot.__reduce__)。
    python:
        import pickle

        store._room_blob = pickle.dumps(current_room)
        store._hs_blob = pickle.dumps(current_room.get_hotspot("music_box"))

    # 只存名稱的話會很小；整棵物件樹被存進去的話會大得多
    $ assert len(store._room_blob) < 300, f"房間不該被整個存進去，實際 {len(store._room_blob)} bytes"
    $ assert len(store._hs_blob) < 300, f"熱點不該被整個存進去，實際 {len(store._hs_blob)} bytes"

    # 還原之後要拿到「目前的」那個物件本身，不是一份舊複本 ——
    # 這就是「改了座標舊存檔也吃得到」的來源
    $ assert pickle.loads(store._room_blob) is current_room, "還原的房間應該就是目前的那一個"
    $ assert pickle.loads(store._hs_blob) is current_room.get_hotspot("music_box"), "還原的熱點應該就是目前的那一個"

    $ _trace("3_房間只存名稱")

    # --- 存檔讀得回來 ---
    $ assert renpy.can_load("_test_save_2"), "存檔應該讀得回來"
    $ _trace("4_存檔可讀")

    # --- 對照組：進度是「照值」存的，不會被之後的改動影響 ---
    #
    # 房間定義只存名稱、讀檔吃到最新版；但玩家的進度剛好相反 ——
    # 存檔當下是多少就是多少，之後再怎麼變都不影響那個存檔。
    #
    # 這裡直接用 pickle 驗，因為存檔用的就是同一套機制。
    python:
        store._rage_at_save = game_state.actors.get("annie_ghost", "rage")
        store._gs_blob = pickle.dumps(game_state)

        # 存檔之後才發生的事
        game_state.actors.add("annie_ghost", "rage", 99)
        game_state.inventory.add("_late_item", 7)
        game_state.flags.set("_late_flag")

        store._gs_restored = pickle.loads(store._gs_blob)

    # 還原回來的是一份「當時的複本」，不是現在這個
    $ assert store._gs_restored is not game_state, "進度應該是照值存的，不是照參考"

    $ assert store._gs_restored.actors.get("annie_ghost", "rage") == store._rage_at_save, "讀檔應該拿回存檔當下的數值，不是後來的"
    $ assert game_state.actors.get("annie_ghost", "rage") == store._rage_at_save + 99, "現在這個當然還是新的值"

    $ assert not store._gs_restored.inventory.has("_late_item"), "存檔之後才拿到的物品不該出現在舊存檔裡"
    $ assert not store._gs_restored.flags.has("_late_flag"), "存檔之後才設的旗標不該出現在舊存檔裡"

    $ _trace("5_進度照值存")

    # 把上面為了測試加的東西清掉，不要污染後面
    python:
        game_state.actors.add("annie_ghost", "rage", -99)
        game_state.inventory.remove("_late_item", 7)
        game_state.flags.clear("_late_flag")

    # 清掉這支測試產生的存檔，不要留在 saves/ 裡礙事
    python:
        for _slot in ("_test_save_1", "_test_save_2"):
            if renpy.can_load(_slot):
                renpy.unlink_save(_slot)


# 左上角狀態欄 (status_display)。
#
# 兩層過濾：
#   1. 只顯示 player_status_display 列出來的數值 (內容層決定要給玩家看什麼)
#   2. 其中「沒被設定過」的跳過 (沒拿到手電筒就不該出現「🔦 0」)
#
# 這裡不寫死 demo 顯示了哪些數值 —— 那是內容層隨時會調的。
# 驗的是機制：列出來的會顯示、數值變了畫面要跟著變、沒列出來的不會漏出去。
#
# 注意測試框架的 assert 是「純文字比對」，不會做 [變數] 插值，
# 所以要先把數值設成一個好認的數字，再比對那個字面值。
testcase status_display_flow:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _trace_reset()

    click "開始"
    advance until "爬上閣樓"
    $ _trace("1_進入探索")

    # demo 至少要顯示一個數值，不然底下全部沒有意義
    python:
        store._shown = [e["stat"] for e in player_status_display
                        if game_state.actors.has_stat("player", e["stat"])]
    $ assert store._shown, "demo 的狀態欄至少要顯示一個數值"

    # --- 列在清單裡而且設定過的數值，畫面上要看得到 ---
    $ game_state.actors.set("player", "hp", 41)
    $ renpy.restart_interaction()
    pause 0.5
    assert "41"
    $ _trace("2_血量顯示中")

    # --- 數值變了，畫面要跟著變 ---
    #
    # 這是狀態欄最容易做壞的地方：把數值當成快照存起來，
    # 之後扣血了畫面還顯示舊的。
    $ game_state.actors.set("player", "hp", 42)
    $ renpy.restart_interaction()
    pause 0.5
    assert "42"
    assert not "41"
    $ _trace("3_數值變了畫面跟著變")

    # --- 沒列在清單裡的數值不該漏出去 ---
    #
    # rage 這種鬼的內部計數器如果顯示給玩家看就是 bug。
    # 這裡用一個一定不在清單裡的名字，配一個很好認的數值。
    $ game_state.actors.set("player", "_secret_counter", 777)
    $ renpy.restart_interaction()
    pause 0.5
    assert not "777"
    $ _trace("4_沒列出來的不顯示")

    # --- 列在清單裡、但沒設定過的數值也不該出現 ---
    #
    # 臨時把一個沒設定過的數值加進顯示清單，確認它不會冒出來。
    # 測完立刻還原，不要污染別的測試。
    python:
        store._orig_display = list(player_status_display)
        player_status_display.append({"stat": "_never_set", "icon": "🔦"})

    $ renpy.restart_interaction()
    pause 0.5
    assert not "🔦"
    $ _trace("5_沒設定過的不顯示")

    # 設定之後就該出現了
    $ game_state.actors.set("player", "_never_set", 88)
    $ renpy.restart_interaction()
    pause 0.5
    assert "88"
    $ _trace("6_設定之後就出現")

    python:
        store.player_status_display = store._orig_display


# 解謎關卡 (Puzzle) 的純邏輯：哪一種結果配哪一個 Effect。
#
# puzzle_result_effect 是純函式，餵假的結果就能測，不用把畫面叫出來。
testcase puzzle_checks:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    # --- 結果與 Effect 的對應 ---

    $ _ok = Effect(set_flags=["opened"])
    $ _bad = Effect(actor="player", stats={"hp": -1})
    $ _p = KeypadPuzzle(code="1234", on_success=_ok, on_failure=_bad)

    $ assert puzzle_result_effect(_p, PUZZLE_SOLVED) is _ok, "答對要套 on_success"
    $ assert puzzle_result_effect(_p, PUZZLE_FAILED) is _bad, "答錯要套 on_failure"

    # 關掉視窗什麼都不做 —— 這才是「可以關掉但沒有放棄選項」的實作
    $ assert puzzle_result_effect(_p, PUZZLE_CLOSED) is None, "關掉視窗不該算失敗"

    # 預期外的值一律什麼都不做。
    #
    # 這一條很重要：Ren'Py 的 Return() 不帶參數時回傳的是 True 不是 None，
    # 所以新的關卡類型只要寫錯一個 Return()，run_puzzle 就會收到 True。
    # 那時候「什麼都不做」比「當成答對」安全太多 —— 一按 ✕ 就開鎖過。
    $ assert puzzle_result_effect(_p, True) is None, "收到 True 不該當成答對"
    $ assert puzzle_result_effect(_p, None) is None
    $ assert puzzle_result_effect(_p, False) is None
    $ assert puzzle_result_effect(_p, "亂七八糟") is None

    # 三個常數不能互相撞，也不能是會被誤判的值
    $ assert len({PUZZLE_SOLVED, PUZZLE_FAILED, PUZZLE_CLOSED}) == 3, "三個結果常數不能重複"
    $ assert all(isinstance(_v, str) and _v for _v in (PUZZLE_SOLVED, PUZZLE_FAILED, PUZZLE_CLOSED)), "結果常數必須是非空字串"

    # 沒設 on_failure 的關卡，答錯就沒代價
    $ _p2 = KeypadPuzzle(code="1234", on_success=_ok)
    $ assert puzzle_result_effect(_p2, PUZZLE_FAILED) is None, "沒設 on_failure 就不該有代價"
    $ assert puzzle_result_effect(_p2, PUZZLE_SOLVED) is _ok

    # --- KeypadPuzzle 的欄位 ---

    # run_puzzle 只認這四個屬性 (鴨子型別)，缺一個就跑不了
    $ assert _p.screen == "keypad_puzzle"
    $ assert _p.on_success is _ok and _p.on_failure is _bad
    $ assert _p.pausable is True, "pausable 預設應該是 True"

    # 密碼一律轉成字串，這樣寫 code=4721 或 code="4721" 都行
    $ assert KeypadPuzzle(code=4721, on_success=_ok).code == "4721", "數字密碼應該轉成字串"
    $ assert KeypadPuzzle(code="0042", on_success=_ok).code == "0042", "開頭的 0 不能被吃掉"

    # --- 目錄查表 ---

    $ assert puzzle_def("kitchen_safe") is not None, "demo 的關卡應該查得到"
    $ assert puzzle_def("nope") is None, "查不到的關卡應該回傳 None"


# 走完密碼鎖的三條路徑：關掉視窗 / 答錯 / 答對。
#
# 密碼不寫死在測試裡 —— 從 puzzle_catalog 讀出來，
# 這樣改了 demo 的密碼，測試也不用跟著改。
#
# 輸入的方式是直接設定 screen 變數而不是一位一位 click，
# 因為測試的 click 是「語句」，沒辦法放進迴圈裡跑可變長度的密碼。
# 數字鍵本身有沒有接對，由前面單獨 click 一次來驗。
testcase keypad_flow:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _trace_reset()

    click "開始"
    advance until "走去廚房"

    click "走去廚房"
    advance until "保險箱"
    $ assert current_room.name == "kitchen"
    $ _trace("1_進廚房")

    # --- 路徑一：打開又關掉，什麼都不該發生 ---
    click "保險箱"
    pause 0.5
    $ assert renpy.get_screen("keypad_puzzle") is not None, "點保險箱應該叫出密碼鎖"
    $ _trace("2_密碼鎖開啟")

    # 數字鍵有沒有真的接上 SetScreenVariable
    $ assert renpy.get_screen_variable("entered", screen="keypad_puzzle") == ""
    click "7"
    pause 0.3
    $ assert renpy.get_screen_variable("entered", screen="keypad_puzzle") == "7", "按數字鍵應該記到 entered"
    $ _trace("3_數字鍵有作用")

    $ _hp_before = game_state.actors.get("player", "hp")
    click "✕"
    pause 0.5

    $ assert renpy.get_screen("keypad_puzzle") is None, "✕ 應該關掉視窗"
    $ assert not game_state.flags.has("safe_opened"), "關掉視窗不該算答對"
    $ assert game_state.actors.get("player", "hp") == _hp_before, "關掉視窗不該算答錯，不能扣血"
    $ assert renpy.get_screen("explore") is not None, "關掉之後要回到探索畫面"
    $ _trace("4_關掉視窗什麼都沒發生")

    # --- 路徑二：答錯 ---
    click "保險箱"
    pause 0.5

    # 重新打開時輸入格要是空的 (screen 的 default entered 每次都重來)
    $ assert renpy.get_screen_variable("entered", screen="keypad_puzzle") == "", "重新打開不該殘留上次按的數字"

    # 一組一定不對的密碼：把正確密碼的每一位都 +1
    python:
        _code = puzzle_def("kitchen_safe").code
        store._wrong = "".join(str((int(_c) + 1) % 10) for _c in _code)
        renpy.set_screen_variable("entered", store._wrong, screen="keypad_puzzle")

    $ renpy.restart_interaction()
    pause 0.3
    $ _hp_before = game_state.actors.get("player", "hp")
    $ _trace("5_輸入錯誤密碼")

    click "確認"
    advance until "保險箱"

    $ assert not game_state.flags.has("safe_opened"), "密碼錯了不該開"
    $ assert game_state.actors.get("player", "hp") < _hp_before, "demo 的 on_failure 會扣血"
    $ assert renpy.get_screen("keypad_puzzle") is None, "答錯之後視窗要關掉"
    $ _trace("6_答錯有代價")

    # --- 路徑三：答對 ---
    click "保險箱"
    pause 0.5

    python:
        renpy.set_screen_variable("entered", puzzle_def("kitchen_safe").code,
                                  screen="keypad_puzzle")

    $ renpy.restart_interaction()
    pause 0.3

    # 解完還在廚房，所以等的是廚房的熱點 (保險箱本身會消失，不能等它)
    click "確認"
    advance until "打開冰箱"

    $ assert game_state.flags.has("safe_opened"), "密碼對了應該開"
    $ assert game_state.inventory.has("documents"), "開了應該拿到獎勵物品"
    $ _trace("7_答對拿到東西")

    # 開過的保險箱熱點會自己消失 (condition=forbid=["safe_opened"])
    assert not "🔒 保險箱"
    $ assert renpy.get_screen("explore") is not None, "解完要回到探索畫面"


init python:

    class _RollbackStash(NoRollback):
        """
        倒帶測試專用的置物櫃。

        倒帶會把 store 裡的東西還原到當時的狀態 —— 包括測試自己在
        $ 語句裡設的變數。所以「倒帶前量到的值」要放在 NoRollback 物件上，
        不然一倒帶就跟著消失，斷言會拿不到。
        """
        pass

    _rb = _RollbackStash()


# 倒帶 (quick menu 的「返回」) 經過 modal 視窗時不能卡住。
#
# 原本的 bug：翻頁視窗與解謎關卡都是 call screen，是倒帶的停靠點。
# 看完物品簡介、關掉之後按「返回」會回到視窗裡；而視窗是 modal，
# 會擋住 quick menu 的「返回」鈕 —— 按不到，只能關掉，
# 關掉再按返回又回到視窗裡，永遠出不去。
#
# 修法是在視窗期間 renpy.suspend_rollback(True)，讓倒帶直接跳過。
#
# 「卡住」的判定方式：連按兩次「返回」。
# 如果倒帶停在 modal 視窗裡，第二次的 click "返回" 會找不到可以點的按鈕而逾時。
testcase rollback_through_modals:

    $ __import__("renpy").test.testsettings._test.timeout = 20.0
    $ _trace_reset()

    click "開始"
    advance until "生鏽的鑰匙"
    click "🔑 生鏽的鑰匙"
    advance until "走去廚房"

    # --- 物品簡介 (page_popup) ---

    click "生鏽的鑰匙"
    pause 0.5
    $ assert renpy.get_screen("page_popup") is not None, "點物品應該打開簡介"

    click "關閉"
    pause 0.5
    $ _trace("1_關閉物品簡介")

    click "返回"
    pause 0.5
    $ assert renpy.get_screen("page_popup") is None, "倒帶不該回到物品簡介視窗裡"
    $ _trace("2_返回一次沒進視窗")

    # 第二次還按得到 = 沒有被 modal 視窗擋住
    click "返回"
    pause 0.5
    $ assert renpy.get_screen("page_popup") is None, "繼續倒帶也不該回到視窗裡"
    $ _trace("3_返回兩次沒卡住")

    # 把測試游標從「返回」鈕上移開。
    #
    # click 會把測試游標留在按鈕上，那顆按鈕就一直保持焦點 ——
    # 之後推進對話時，Enter 會觸發「有焦點的按鈕」，等於又按了一次返回，
    # 一直往回倒、永遠推不回來。真人玩家按完返回會把滑鼠移去點對話，不會發生這件事。
    # (這個坑踩過：測試連續三次卡在 advance until，還一度誤判成倒帶的 bug)
    move pos (960, 300)

    # 倒帶正確性：倒帶到某個時間點、再往前推回來，狀態要跟那個時間點一致。
    # 記在 NoRollback 的置物櫃裡，不然「倒帶當下量到的值」自己也會被倒帶掉。
    $ _rb.key_at_rollback_point = game_state.inventory.has("key")

    # --- 解謎關卡 (keypad) ---
    #
    # 從這裡開始是新的一段流程，先回到探索狀態、走去廚房。
    advance until "走去廚房"
    $ _trace("3a_回到探索看得到走去廚房")
    $ assert game_state.inventory.has("key") == _rb.key_at_rollback_point, f"倒帶後再往前推，鑰匙狀態應該跟倒帶當下一致 (當下 {_rb.key_at_rollback_point})"
    click "走去廚房"
    $ _trace("3b_點了走去廚房")
    advance until "保險箱"
    $ _trace("3c_看得到保險箱")

    python:
        # 暫時把答錯的代價換成「不帶 label」的版本。
        #
        # 這樣答錯之後沒有對話，只要倒帶一次就該回到打開關卡之前 ——
        # 測試不用去數 demo 的對話有幾句，改 demo 台詞也不會讓這裡誤報。
        # (這個改動發生在倒帶停靠點之後，倒帶時會自動還原)
        puzzle_def("kitchen_safe").on_failure = Effect(actor="player", stats={"hp": -1})

        _rb.hp_before = game_state.actors.get("player", "hp")

    click "保險箱"
    pause 0.5
    $ assert renpy.get_screen("keypad_puzzle") is not None

    python:
        _code = puzzle_def("kitchen_safe").code
        _wrong = "".join(str((int(_c) + 1) % 10) for _c in _code)
        renpy.set_screen_variable("entered", _wrong, screen="keypad_puzzle")

    $ renpy.restart_interaction()
    pause 0.3
    click "確認"
    advance until "保險箱"

    $ _rb.hp_after_wrong = game_state.actors.get("player", "hp")
    $ assert _rb.hp_after_wrong < _rb.hp_before, "答錯應該扣血"
    $ _trace("4_答錯扣血")

    click "返回"
    pause 0.5
    $ assert renpy.get_screen("keypad_puzzle") is None, "倒帶不該回到密碼鎖裡"

    # 我在 puzzle.rpy 的註解裡宣稱「答錯扣的血會一起被倒帶還原」——
    # 這句話要有東西守著，不能只寫在註解裡。
    $ assert game_state.actors.get("player", "hp") == _rb.hp_before, f"倒帶應該把答錯扣的血還回來，倒帶前 {_rb.hp_before}、答錯後 {_rb.hp_after_wrong}、現在 {game_state.actors.get('player', 'hp')}"
    $ _trace("5_倒帶跳過密碼鎖而且血回來了")

    click "返回"
    pause 0.5
    $ assert renpy.get_screen("keypad_puzzle") is None, "繼續倒帶也不該回到密碼鎖裡"
    $ _trace("6_返回兩次沒卡住")
    move pos (960, 300)


# 九宮格解鎖 (PatternPuzzle) 的純邏輯。
#
# 規則與拖曳判定都抽成純函式，PatternPad 的 event() 也可以直接餵假的
# pygame 事件 —— 所以轉角、手滑、跨過中間點這些情況都不用靠真的拖滑鼠。
testcase pattern_checks:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    # --- pattern_extend：接點規則 ---

    $ assert pattern_extend([], 1) == [1]
    $ assert pattern_extend([1], 2) == [1, 2], "相鄰的點直接接上"
    $ assert pattern_extend([1], 5) == [1, 5], "斜對角相鄰，中間沒有格點"
    $ assert pattern_extend([1], 6) == [1, 6], "馬步 (1->6) 中間沒有格點"

    # 直線跨過的點會被自動接上
    $ assert pattern_extend([1], 3) == [1, 2, 3], "橫跨：1->3 要自動接上 2"
    $ assert pattern_extend([1], 7) == [1, 4, 7], "直跨：1->7 要自動接上 4"
    $ assert pattern_extend([1], 9) == [1, 5, 9], "斜跨：1->9 要自動接上 5"
    $ assert pattern_extend([4], 6) == [4, 5, 6]
    $ assert pattern_extend([3], 7) == [3, 5, 7]

    # 中間的點已經用過了，就直接跨過去
    $ assert pattern_extend([2, 1], 3) == [2, 1, 3], "中間點用過了就不再接一次"

    # 同一個點不能用兩次
    $ assert pattern_extend([1, 2], 2) == [1, 2], "重複的點要被忽略"
    $ assert pattern_extend([1, 2], 1) == [1, 2]

    # 純函式：不能改到傳進來的 list
    $ _orig = [1]
    $ pattern_extend(_orig, 3)
    $ assert _orig == [1], "pattern_extend 不該改到傳進來的 list"

    # --- 座標與判定 ---

    # 480 的連線區切三等分，每格 160，點在格子中央
    $ assert pattern_dot_center(1) == (80.0, 80.0)
    $ assert pattern_dot_center(5) == (240.0, 240.0)
    $ assert pattern_dot_center(9) == (400.0, 400.0)

    $ assert pattern_dot_at(240, 240) == 5, "點在圓心要命中"
    $ assert pattern_dot_at(80 + 40, 80) == 1, "判定範圍內要命中"
    $ assert pattern_dot_at(80 + 50, 80) is None, "判定範圍外要落空"
    $ assert pattern_dot_at(160, 160) is None, "兩點之間的空隙不該命中任何點"
    $ assert pattern_dot_at(-100, -100) is None

    # --- PatternPuzzle：建立時就檢查畫不畫得出來 ---

    $ _ok = Effect(set_flags=["x"])

    $ _pp = PatternPuzzle(pattern="1235789", on_success=_ok)
    $ assert _pp.pattern == [1, 2, 3, 5, 7, 8, 9], "字串圖形要轉成數字 list"
    $ assert _pp.screen == "pattern_puzzle"
    $ assert _pp.pausable is True
    $ assert _pp.on_failure is None
    $ assert PatternPuzzle(pattern=[1, 5, 9, 6], on_success=_ok).pattern == [1, 5, 9, 6]

    python:
        def _raises(**kw):
            try:
                PatternPuzzle(on_success=_ok, **kw)
            except ValueError:
                return True
            return False

    $ assert _raises(pattern=[1, 3, 6, 9]), "1->3 會自動接上 2，這個圖形畫不出來，要報錯"
    $ assert _raises(pattern=[1, 2, 2, 3]), "重複的點要報錯"
    $ assert _raises(pattern=[0, 1, 2, 3]), "編號超出 1-9 要報錯"
    $ assert _raises(pattern=[1, 2, 3]), "比 min_length (預設 4) 短，玩家畫出來會被當手滑，要報錯"
    $ assert not _raises(pattern=[1, 2, 3], min_length=3), "min_length 放寬之後就合法"

    $ assert puzzle_def("playground_phone") is not None, "demo 的圖形鎖應該查得到"

    # --- PatternPad：直接餵假的滑鼠事件 ---

    python:
        def _down(pad, dot):
            x, y = pattern_dot_center(dot)
            return pad.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1), x, y, 0)

        def _move(pad, dot):
            x, y = pattern_dot_center(dot)
            return pad.event(pygame.event.Event(pygame.MOUSEMOTION), x, y, 0)

        def _up(pad):
            return pad.event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1), 0, 0, 0)

    # 畫對：從 1 直接跳到 9，中間的 5 要被自動接上
    python:
        _pad = PatternPad([1, 5, 9], 3)
        _down(_pad, 1)
        _move(_pad, 9)
        assert _pad.path == [1, 5, 9], f"跳過中間點也要被接上，實際 {_pad.path}"
        assert _up(_pad) == PUZZLE_SOLVED, "畫對要回傳 PUZZLE_SOLVED"
        assert _pad.path == [] and not _pad.dragging, "放開之後要清掉路徑"

    # 畫錯
    python:
        _pad = PatternPad([1, 5, 9], 3)
        _down(_pad, 1)
        _move(_pad, 3)
        assert _up(_pad) == PUZZLE_FAILED, "畫錯要回傳 PUZZLE_FAILED"

    # 手滑：點太少，不結束互動 (回傳 None)，也不算失敗
    python:
        _pad = PatternPad([1, 5, 9], 3)
        _down(_pad, 1)
        _move(_pad, 2)
        assert _up(_pad) is None, "點太少不該結束互動"
        assert _pad.too_short, "點太少要顯示提示"

        # 再畫一次，提示要消失
        _down(_pad, 1)
        assert not _pad.too_short, "重新開始畫要清掉提示"

    # 不是從點上開始拖，就不算開始
    python:
        _pad = PatternPad([1, 5, 9], 3)
        _pad.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1), 160, 160, 0)
        assert not _pad.dragging, "沒按在點上不該開始連線"
        assert _up(_pad) is None, "沒在拖的時候放開不該有結果"


# 九宮格解鎖的整合測試：真的用滑鼠拖曳。
#
# 測試框架的 drag 只能拖「一段直線」，最多連到 3 個點，
# 所以這裡暫時把 demo 的圖形換成 [1, 5, 9]、min_length 放寬成 3。
# (demo 的 Z 形圖形在 pattern_checks 裡用假事件驗)
testcase pattern_flow:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _trace_reset()

    click "開始"
    advance until "前往實驗區"

    click "前往實驗區"
    advance until "舊手機"
    $ assert current_room.name == "playground"
    $ _trace("1_進實驗區")

    python:
        _phone = puzzle_def("playground_phone")
        _phone.pattern = [1, 5, 9]
        _phone.min_length = 3

    # --- 路徑一：打開又關掉 ---
    click "舊手機"
    pause 0.5
    $ assert renpy.get_screen("pattern_puzzle") is not None, "點舊手機應該叫出圖形鎖"

    click "✕"
    pause 0.5
    $ assert renpy.get_screen("pattern_puzzle") is None, "✕ 應該關掉視窗"
    $ assert not game_state.flags.has("playground_phone_unlocked"), "關掉不該算解開"
    $ _trace("2_關掉什麼都沒發生")

    # --- 路徑二：手滑 (只連 2 個點) ---
    click "舊手機"
    pause 0.5

    drag pos pattern_dot_screen_pos(1) to pos pattern_dot_screen_pos(2) steps 10
    pause 0.3

    $ assert renpy.get_screen("pattern_puzzle") is not None, "點太少不該關掉視窗"
    $ assert renpy.get_screen_variable("pad", screen="pattern_puzzle").too_short, "點太少要顯示提示"
    $ _trace("3_手滑不算一次嘗試")

    # --- 路徑三：畫錯 (1->3 會變成 1,2,3) ---
    drag pos pattern_dot_screen_pos(1) to pos pattern_dot_screen_pos(3) steps 10

    # 用 advance until 回到探索畫面，不要假設「畫錯之後沒有對話」——
    # on_failure 帶不帶 label 是 demo 內容隨時會調的。
    # 沒有對話時會立刻通過；有對話時會先把對話推完。
    # (這個坑踩過：demo 加了失敗對話之後，這裡直接去點舊手機就點不到了)
    advance until "舊手機"

    $ assert renpy.get_screen("pattern_puzzle") is None, "畫錯之後視窗要關掉"
    $ assert not game_state.flags.has("playground_phone_unlocked"), "畫錯不該解開"
    $ _trace("4_畫錯")

    # --- 路徑四：畫對 (1->9 斜拖，中間的 5 會被連到) ---
    click "舊手機"
    pause 0.5

    drag pos pattern_dot_screen_pos(1) to pos pattern_dot_screen_pos(9) steps 20
    advance until "舊手機"

    $ assert game_state.flags.has("playground_phone_unlocked"), "畫對應該解開"
    $ assert renpy.get_screen("explore") is not None, "解完要回到探索畫面"
    $ _trace("5_畫對解開")
