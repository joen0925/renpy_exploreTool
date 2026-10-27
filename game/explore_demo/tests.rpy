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

    # pausable 的「會暫停」那一半。
    #
    # 保險箱是預設的 pausable=True，所以解的時候世界應該停下來等玩家 ——
    # 單純的謎題，想多久都沒關係。
    #
    # 這條跟 interrupt_flow 裡「pausable=False 不該暫停」是一對。
    # 只有那一條的話，run_puzzle 完全無視 pausable、永遠讓時鐘跑，
    # 也不會有任何測試叫 —— 鬼就會在玩家慢慢解謎時默默逼近。
    $ assert world.paused, "pausable=True 的關卡開著時世界應該暫停 (想解多久都沒關係)"
    $ assert "dialogue" in world.pause_reasons, f"暫停理由應該是外層對話那一層，實際 {world.pause_reasons}"

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
        renpy.set_screen_variable(
            "entered", puzzle_def("kitchen_safe").code, screen="keypad_puzzle")

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
#
# 第三個 modal 視窗 (近景視窗) 的同一組檢查在 closeup_flow 裡 ——
# 從廚房走到實驗區要多繞五六步，而 closeup_flow 本來就站在那裡。
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


# 舊存檔的相容性。
#
# 問題：存檔是把 GameState 的 __dict__ 原樣存起來，讀檔時不會呼叫 __init__。
# 所以工具包多一個 section 之後，舊存檔讀回來身上就是沒有那個屬性，
# 下一次碰到 game_state.actors 就 AttributeError —— 玩家的舊進度全毀。
#
# 這裡用 pickle 直接做出一個「舊版存檔」的形狀來驗，
# 因為存檔用的就是同一套機制，而且真的去讀一個舊版存檔需要留一份二進位檔在 repo 裡。
testcase save_compat:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    # Ren'Py 讀檔後會自動跑這個 label。沒有它的話下面補的洞永遠不會被補。
    $ assert renpy.has_label("after_load"), "少了 label after_load，舊存檔不會被補齊"

    # --- 模擬舊版存檔：某個 section 還不存在的年代 ---
    python:
        import pickle

        store._old = GameState()
        store._old.inventory.add("rusty_key")
        store._old.flags.set("did_something")

        # 「那個年代還沒有 actors」
        del store._old.actors
        store._old_blob = pickle.dumps(store._old)

        store._loaded = pickle.loads(store._old_blob)

    # 前提要成立：還原回來的確實是缺了一塊的狀態
    $ assert not hasattr(store._loaded, "actors"), "這個測試的前提是存檔裡沒有 actors"

    # --- 補洞 ---
    $ _added = store._loaded.ensure_sections()
    $ assert "actors" in _added, f"缺少的 section 應該被補上，實際補了 {_added}"
    $ assert store._loaded.actors.get("player", "hp") == 0, "補上的 section 應該是乾淨的預設值"

    # 關鍵：舊進度一個都不能掉。
    # 寫成「缺就整個重建 GameState」的話這兩條會死，而那正是最容易的寫法。
    $ assert store._loaded.inventory.has("rusty_key"), "補 section 不該弄丟物品"
    $ assert store._loaded.flags.has("did_something"), "補 section 不該弄丟旗標"

    # 補過的東西不該再被動到 (讀檔會跑 after_load，每次讀都會呼叫一次)
    python:
        store._loaded.actors.set("player", "hp", 3)
        store._again = store._loaded.ensure_sections()

    $ assert store._again == [], f"沒有缺東西就不該補，實際補了 {store._again}"
    $ assert store._loaded.actors.get("player", "hp") == 3, "再呼叫一次不該把數值洗掉"

    # --- 一張表，不是兩張 ---
    #
    # sections() 與 ensure_sections() 都從 _section_specs() 讀。
    # 如果有人又把清單抄成兩份，新增 section 時就會只改一邊 ——
    # 補洞補不到那個 section，舊存檔照樣爆。
    $ assert len(game_state.sections()) == len(game_state._section_specs())
    $ assert game_state.ensure_sections() == [], "正在玩的狀態不該缺任何 section"


# 次數累積觸發：「第 N 次進來才發生」。
#
# 這是「不靠計時器也能突然嚇人」的第一種做法。
# collect_events 是純函式，所以餵一個乾淨的 GameState 連續派發幾次就能測完，
# 完全不用啟動畫面。
#
# 最重要的一條是「第 3 次就是第 3 次」—— 差一次的話玩家會在第 4 次才被嚇到，
# 而這種錯誤在遊戲裡幾乎看不出來，只會覺得「怪怪的」。
testcase count_trigger_checks:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    python:
        store._gs = GameState()
        store._ctx = EventContext(store._gs)

        store._events = [
            visit_counter("t.visits"),
            Event(
                id="t.scare",
                condition=Condition(check=count_at_least("t.visits", 3)),
                effect=Effect(label="t_scare"),
                limit=1,
            ),
        ]

        # 連續進房 5 次，記下每一次收集到的 label
        store._fired = []
        for _i in range(5):
            store._fired.append(collect_events(
                store._events,
                TriggerType.ENTER_ROOM,
                store._ctx,
                TriggerType.ENTER_ROOM,
            ))

    # --- 前兩次什麼都不該發生 ---
    $ assert store._fired[0] == [], f"第 1 次就觸發了：{store._fired[0]}"
    $ assert store._fired[1] == [], f"第 2 次就觸發了：{store._fired[1]}"

    # --- 關鍵：第 3 次剛好觸發，不是第 4 次 ---
    #
    # 這一條在守 visit_counter 的 sequence。
    # 計數器如果排在條件事件後面，條件求值時這次的次數還沒被記進去，
    # 第 3 次會讀到 2 而不觸發，變成第 4 次才嚇人。
    $ assert store._fired[2] == ["t_scare"], f"第 3 次應該要觸發，實際 {store._fired[2]}"

    # --- limit=1，之後不再觸發 ---
    $ assert store._fired[3] == [], "已經嚇過一次就不該再嚇"
    $ assert store._fired[4] == []

    # --- 計數器本身永遠不死，會一直數下去 ---
    #
    # 這是 visit_counter 存在的理由：on_enter 那種會死的事件數不到第 3 次。
    $ assert store._gs.events.count_of("t.visits") == 5, f"計數器應該數到 5，實際 {store._gs.events.count_of('t.visits')}"
    $ assert not store._gs.events.is_dead("t.visits"), "計數器不該死亡"

    # --- 對照組：會死的計數器就是數不下去 ---
    #
    # 直接示範 on_enter 那個坑：limit=1 的事件死掉之後次數就停住了。
    python:
        store._gs2 = GameState()
        store._ctx2 = EventContext(store._gs2)
        store._mortal = [Event(id="t.mortal", limit=1)]

        for _i in range(5):
            collect_events(
                store._mortal,
                TriggerType.ENTER_ROOM,
                store._ctx2,
                TriggerType.ENTER_ROOM,
            )

    $ assert store._gs2.events.count_of("t.mortal") == 1, "limit=1 的事件死掉之後次數就不該再增加"

    # --- helper 的順序保證 ---
    #
    # 寫死這個關係，免得有人之後把 VISIT_COUNTER_SEQUENCE 調到 0 以上，
    # 上面那條「第 3 次」的斷言就會變成隨機通過。
    $ assert visit_counter("t.x").sequence < Event(id="t.y").sequence, "計數器一定要排在一般事件前面"
    $ assert visit_counter("t.x").limit is None, "計數器不能有次數上限"
    $ assert visit_counter("t.x").effect is None, "計數器不該有 Effect"

    # 次數判斷式是純讀取的，可以安全地重複呼叫 (熱點顯示條件每幀都會叫它)
    python:
        store._check = count_at_least("t.visits", 3)
        store._v = store._gs.view()
        store._before = store._gs.events.count_of("t.visits")

        for _i in range(10):
            store._check(store._v)

    $ assert store._gs.events.count_of("t.visits") == store._before, "判斷式不該改到任何狀態"


# 機率觸發 (Event.chance)。
#
# 這是「不靠計時器也能突然嚇人」的第二種做法。
#
# 機率怎麼測得準：renpy.random 是 Ren'Py 自己的 RNG (DetRandom)，
# 它的 pushback() 會讓接下來幾次照指定順序發數字 ——
# 倒帶就是靠這個機制重現骰值的，所以測試也能拿來注入固定的骰點。
# 因此這支測試完全沒有隨機性，不會偶爾紅一次。
testcase chance_checks:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    # --- 欄位驗證：寧可建房間時就爆掉 ---
    $ assert Event(id="c.a").chance is None, "沒填 chance 就該是 None (一定觸發)"
    $ assert Event(id="c.b", chance=0.25).chance == 0.25

    # 把百分比直接填進去是最容易犯的錯，一定要擋
    python:
        store._err = None
        try:
            Event(id="c.bad", chance=25)
        except ValueError as e:
            store._err = str(e)
    $ assert store._err is not None, "chance=25 (當成百分比) 應該要報錯"
    $ assert "0.25" in store._err, "錯誤訊息應該告訴作者 25% 要寫 0.25"

    python:
        store._err2 = None
        try:
            Event(id="c.bad2", chance=-0.1)
        except ValueError as e:
            store._err2 = str(e)
    $ assert store._err2 is not None, "負數機率應該要報錯"

    # bool 是 int 的子類別，chance=True 幾乎一定是手滑
    python:
        store._err3 = None
        try:
            Event(id="c.bad3", chance=True)
        except ValueError as e:
            store._err3 = str(e)
    $ assert store._err3 is not None, "chance=True 應該要報錯"

    # --- 邊界值不該消耗亂數 ---
    #
    # 每骰一次都會強制產生一個倒帶檢查點，所以 None/0/1 要直接短路。
    # 驗法：注入一顆骰值，呼叫邊界值幾次，那顆應該還沒被拿走。
    python:
        renpy.random.reset()
        renpy.random.pushback([0.01])

        store._edges = [chance_passes(None), chance_passes(1.0), chance_passes(0.0)]

        # 注入的那顆還在不在，直接看 stack 的長度。
        #
        # 刻意不用「下一次骰到什麼」來判斷：如果邊界值真的偷骰了一顆，
        # 下一次就會抽到一個全新的亂數，而那個數字有一半的機率
        # 剛好也讓斷言通過 —— 那就變成偶爾才紅的測試，等於沒有偵錯能力。
        store._stack_after_edges = len(renpy.random.stack)

    $ assert store._edges == [True, True, False], f"邊界值的結果不對：{store._edges}"
    $ assert store._stack_after_edges == 1, f"邊界值 (None/1.0/0.0) 不該消耗亂數，注入的骰值應該還在，實際剩 {store._stack_after_edges}"

    # --- 骰值決定結果 ---
    python:
        renpy.random.reset()
        renpy.random.pushback([0.10, 0.90])

        store._rolls = [chance_passes(0.25), chance_passes(0.25)]

    $ assert store._rolls == [True, False], f"0.10 該中、0.90 該不中，實際 {store._rolls}"

    # --- 最重要的一條：骰輸不算觸發過，不消耗 limit ---
    #
    # 骰輸如果被記成一次觸發，limit=1 的機率事件第一次骰輸就死亡，
    # 玩家永遠遇不到它。而這種 bug 只會偶爾發生，手動試玩幾乎抓不到。
    python:
        store._gs = GameState()
        store._ctx = EventContext(store._gs)
        store._ev = [
            Event(id="c.rare", chance=0.5,
                effect=Effect(label="c_rare"), limit=1),
        ]

        renpy.random.reset()
        renpy.random.pushback([0.99, 0.99, 0.01])   # 輸、輸、中

        # 每派發一次就立刻把狀態拍下來。
        #
        # 這裡踩過一次坑：本來是三次跑完才去查 count_of()，
        # 但第 3 次骰中會把次數加成 1，所以「骰輸不該記次數」那條斷言
        # 查到的其實是第 3 次之後的狀態，必定失敗。
        # 要驗中途的狀態，就得在中途拍照。
        store._out = []
        store._counts = []
        store._deads = []

        for _i in range(3):
            store._out.append(collect_events(
                store._ev,
                TriggerType.ENTER_ROOM,
                store._ctx,
                TriggerType.ENTER_ROOM,
            ))
            store._counts.append(store._gs.events.count_of("c.rare"))
            store._deads.append(store._gs.events.is_dead("c.rare"))

    # --- 骰輸的那兩次：什麼都沒發生，次數也沒動 ---
    $ assert store._out[0] == [], f"第 1 次骰輸不該觸發，實際 {store._out[0]}"
    $ assert store._counts[0] == 0, f"骰輸不該被記成觸發過，實際 {store._counts[0]}"
    $ assert not store._deads[0], "骰輸不該讓事件死亡"

    $ assert store._out[1] == [], f"第 2 次骰輸不該觸發，實際 {store._out[1]}"
    $ assert store._counts[1] == 0, f"骰輸兩次還是不該記成觸發過，實際 {store._counts[1]}"
    $ assert not store._deads[1], "骰輸兩次還是不該死亡 —— 這就是 limit 沒被消耗的證據"

    # --- 第 3 次骰中：這一次才算 ---
    $ assert store._out[2] == ["c_rare"], f"第 3 次骰中應該要觸發，實際 {store._out[2]}"
    $ assert store._counts[2] == 1, f"骰中才算一次觸發，實際 {store._counts[2]}"
    $ assert store._deads[2], "骰中且 limit=1，之後就該死亡"

    # --- 條件不符的事件不該先骰 ---
    #
    # 骰點一定要排在 can_fire 之後：條件都不符的事件白骰一顆，
    # 就白白多一個倒帶檢查點。
    # 驗法一樣 —— 注入的那顆骰值應該還在。
    python:
        store._gs3 = GameState()
        store._ctx3 = EventContext(store._gs3)
        store._blocked = [Event(id="c.blocked", chance=0.5,
                                condition=Condition(require=["nope"]),
                                effect=Effect(label="c_blocked"), limit=None)]

        renpy.random.reset()
        renpy.random.pushback([0.01])

        store._blocked_out = collect_events(
            store._blocked,
            TriggerType.ENTER_ROOM,
            store._ctx3,
            TriggerType.ENTER_ROOM,
        )

        # 一樣看 stack 的長度，理由同上 —— 這條如果用「下一次骰到什麼」來判斷，
        # 破壞驗證會有一半的機率抓不到。
        store._stack_after_blocked = len(renpy.random.stack)

    $ assert store._blocked_out == [], "條件不符當然不該觸發"
    $ assert store._stack_after_blocked == 1, f"條件不符時不該先骰機率，注入的骰值應該還在，實際剩 {store._stack_after_blocked}"

    # --- demo 的衣櫃：機率事件要配一個保底 ---
    #
    # 骰不中時完全沒反應的話，玩家會以為熱點壞了。
    python:
        store._wardrobe = rooms["attic"].get_hotspot("wardrobe")
        store._chances = [e.chance for e in store._wardrobe.events]

    $ assert store._wardrobe is not None, "demo 應該有衣櫃熱點"
    $ assert any(c is not None for c in store._chances), "衣櫃應該有一個機率事件"
    $ assert any(c is None for c in store._chances), "衣櫃應該有一個保底事件 (骰不中時講話)"


# 世界時鐘 (world / WorldClock)。
#
# 純邏輯測試，不啟動畫面 —— tick(dt) 本來就是設計成「餵秒數就能推進」，
# 不用真的等時間過去。
#
# 大部分斷言是在守 2026-10-12 手動測試抓到的兩個 bug：
#   1. 解謎途中時鐘被外層的對話暫停壓住 (suspend_pauses 要能讓開)
#   2. elapsed 放進被倒帶追蹤的 GameState，讀檔後時鐘看起來凍住
#
# 刻意用自己 new 一個 WorldClock 來驗邏輯，不去動 store.world ——
# 動到正在跑的那個時鐘會污染其他測試。
testcase world_clock_checks:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    # --- tick 會推進，而且夾上限 ---
    python:
        store._wc = WorldClock()

        store._adv_small = store._wc.tick(0.05)
        store._elapsed_small = store._wc.elapsed

        # 夾上限：失焦或卡頓隔了 5 秒，不該讓鬼瞬間往前跳 5 秒
        store._adv_big = store._wc.tick(5.0)

    $ assert abs(store._adv_small - 0.05) < 1e-9, f"tick 應該回傳實際推進的秒數，實際 {store._adv_small}"
    $ assert abs(store._elapsed_small - 0.05) < 1e-9, f"elapsed 應該累加，實際 {store._elapsed_small}"
    $ assert abs(store._adv_big - WORLD_MAX_DT) < 1e-9, f"單次 tick 最多只能推進 WORLD_MAX_DT={WORLD_MAX_DT}，實際 {store._adv_big}"

    # 時間不倒流
    python:
        store._before_neg = store._wc.elapsed
        store._adv_neg = store._wc.tick(-3.0)

    $ assert store._adv_neg == 0.0, f"負的 dt 不該推進，實際 {store._adv_neg}"
    $ assert store._wc.elapsed == store._before_neg, "負的 dt 不該讓 elapsed 變小"

    # --- 暫停 ---
    #
    # 暫停計數「不在」時鐘物件身上，而是放在被倒帶追蹤的 store 變數
    # (world_pause_counts)，所以下面用全域的 world 來驗，
    # 每一段開頭先 resume_all() 清乾淨。
    #
    # 為什麼不放在物件上：倒帶會重播 `$ world.pause("dialogue")` 那一行，
    # 計數器如果不跟著倒回去，+1 重播了、-1 沒補回來，就永久多一層。
    # (這個 bug 真的發生過，2026-10-25 用滑鼠滾輪倒帶測出來的)
    #
    # elapsed 仍然是物件自己的狀態，所以這裡還是 new 一個乾淨的時鐘來驗推進。
    python:
        world.resume_all()

        store._wc2 = WorldClock()
        world.pause("dialogue")
        store._adv_paused = store._wc2.tick(1.0)

    $ assert world.paused, "pause 之後應該是暫停狀態"
    $ assert store._adv_paused == 0.0, f"暫停時 tick 應該回傳 0，實際 {store._adv_paused}"
    $ assert store._wc2.elapsed == 0.0, "暫停時不該累加"

    # 暫停會疊：翻頁視窗開著時又跑了一段對話，
    # 對話結束只解除對話那個理由，視窗那個還在 —— 時鐘不該偷跑。
    # 寫成 bool 的話這一條會死，而那正是最容易的寫法。
    python:
        world.pause("page_popup")
        world.resume("dialogue")

    $ assert world.paused, "還有別的暫停理由在，就該繼續暫停"
    $ assert store._wc2.tick(1.0) == 0.0, "還在暫停就不該推進"

    $ world.resume("page_popup")
    $ assert not world.paused, "所有理由都解除後才該繼續走"
    $ assert store._wc2.tick(0.05) > 0.0, "解除暫停後應該推得動"

    # 解除一個不存在的理由不該爆掉 (對話被 jump 打斷時會發生)
    $ world.resume("never_paused_with_this")

    # --- 同一個理由疊兩層：內層解除不該讓外層失效 ---
    #
    # 這是真實會發生的情況：run_event_labels 會嵌套 (事件的 label 裡
    # 呼叫 change_room() 就會在裡面再跑一次)，兩層用的理由都是 "dialogue"。
    # 寫成 set 的話內層的 resume 會把理由整個拿掉，
    # 外層的對話還在演、時鐘就已經偷跑了。
    # (我一開始就是寫成 set，這條就是為了守這個 bug)
    python:
        world.resume_all()
        store._wc_nest = WorldClock()

        world.pause("dialogue")               # 外層
        world.pause("dialogue")               # 內層 (同一個理由)
        world.resume("dialogue")              # 內層結束
        store._nest_still_paused = world.paused
        store._nest_adv = store._wc_nest.tick(0.05)
        world.resume("dialogue")              # 外層結束
        store._nest_done = world.paused

    $ assert store._nest_still_paused, "同一個理由疊兩層，內層解除後外層還在，應該繼續暫停"
    $ assert store._nest_adv == 0.0, f"外層還在暫停就不該推進，實際推進了 {store._nest_adv}"
    $ assert not store._nest_done, "兩層都解除後才該繼續走"

    # 多解除幾次不該讓計數變成負數 (否則之後 pause 一次會解不掉)
    python:
        world.resume_all()
        world.pause("dialogue")
        world.resume("dialogue")
        world.resume("dialogue")
        world.resume("dialogue")
        world.pause("dialogue")

    $ assert world.paused, "多解除幾次之後，pause 一次就該暫停得了"

    # --- suspend_pauses：解謎途中要讓世界繼續走 ---
    #
    # 這是 bug 1 的回歸測試。解謎是從熱點的 label 叫出來的，
    # 而那些 label 由 run_event_labels 執行 —— 那裡已經為了對話暫停了。
    # run_puzzle 不把外層暫停讓開的話，解謎全程時鐘都是停的。
    python:
        world.resume_all()
        store._wc3 = WorldClock()

        world.pause("dialogue")

        world.suspend_pauses()
        store._susp_paused = world.paused
        store._susp_adv = store._wc3.tick(0.05)

        world.restore_pauses()

    $ assert not store._susp_paused, "suspend_pauses 之後世界應該要在走 (解謎時鬼要繼續逼近)"
    $ assert store._susp_adv > 0.0, f"suspend_pauses 期間 tick 應該推得動，實際 {store._susp_adv}"
    $ assert world.paused, "restore_pauses 之後外層的暫停要回來"
    $ assert "dialogue" in world.pause_reasons, f"還原的應該是原本那個理由，實際 {world.pause_reasons}"

    # 嵌套：用堆疊而不是單一欄位，內層還原後外層那一份還要在
    python:
        world.resume_all()
        world.pause("outer")
        world.suspend_pauses()
        world.pause("inner")
        world.suspend_pauses()
        world.restore_pauses()
        store._nested_mid = set(world.pause_reasons)
        world.restore_pauses()
        store._nested_end = set(world.pause_reasons)

    $ assert store._nested_mid == {"inner"}, f"內層還原應該拿回 inner，實際 {store._nested_mid}"
    $ assert store._nested_end == {"outer"}, f"外層還原應該拿回 outer，實際 {store._nested_end}"

    # 沒有對應的 suspend 時 restore 不該爆掉
    $ world.restore_pauses()
    $ world.resume_all()

    # --- 驅動端的回傳值一定要是 None ---
    #
    # 這是整個時鐘最隱晦的地雷：Ren'Py 的畫面動作只要回傳非 None，
    # 就等於「結束當前互動」。時鐘的 timer 接到會回傳 dt 的函式上的話，
    # 每 0.05 秒就會把玩家正在進行的互動砍掉一次 ——
    # 症狀是翻頁視窗/解謎視窗一打開就自己關掉。
    # (這個 bug 真的發生過，popup 三支測試一起掛掉)
    $ assert world_clock_tick() is None, "world_clock_tick 必須不回傳任何東西，不然 timer 會把互動吃掉"

    # --- 時間不能放進被倒帶追蹤的地方 ---
    #
    # 這是 bug 2 的回歸測試。elapsed 每秒被改 20 次，
    # 放進 GameState (刻意被倒帶追蹤) 的話會被倒帶反覆抹掉，
    # 症狀是「讀檔之後時鐘凍住不動」。
    $ assert isinstance(world, NoRollback), "world 必須是 NoRollback，不然每秒 20 次的改動會灌爆倒帶紀錄"
    $ assert hasattr(world, "elapsed"), "elapsed 應該在 world 身上"
    $ assert not any(_n == "world" for _n, _f in game_state._section_specs()), "世界時鐘不該是 GameState 的 section (會被倒帶抹掉)"

    # 但「不被倒帶」不等於「不存檔」—— default 變數照樣會進存檔。
    # 存檔用的就是 pickle，所以直接驗 pickle。
    python:
        import pickle

        store._wc5 = WorldClock()
        store._wc5.tick(0.1)
        store._wc5_restored = pickle.loads(pickle.dumps(store._wc5))

    $ assert store._wc5_restored.elapsed == store._wc5.elapsed, "存檔要留得住累積的時間"

    # 光是「物件 pickle 得起來」不夠 —— 還要確認 world 這個變數真的會被存檔收進去。
    #
    # Ren'Py 只存「init 之後被改過」的變數 (renpy.game.log.get_roots 的註解)。
    # 而 world 是 NoRollback，改 world.elapsed 動的是物件內部，
    # 完全沒碰到 world 這個變數本身 —— 所以這件事值得一條斷言守著。
    # 沒進 roots 的話，讀檔會拿到一個全新的時鐘 (時間歸零)。
    python:
        store._roots = renpy.game.log.get_roots()
        store._world_in_roots = "store.world" in store._roots

    $ assert store._world_in_roots, "world 必須在存檔的 roots 裡，不然讀檔會拿到一個全新的時鐘"

    # --- 讀檔之後時鐘不能卡在暫停 ---
    #
    # 暫停理由會被存進存檔，在對話中途存檔的話讀回來就還是暫停的，
    # 時鐘從此不動。所以要有一個讀檔後清理的鉤子。
    #
    # 用 config.after_load_callbacks 而不是再寫一個 label after_load ——
    # game_state.rpy 已經有一個了，同名 label 會撞車。
    $ assert world_clock_after_load in config.after_load_callbacks, "少了讀檔清理，對話中途存檔讀回來時鐘會卡在暫停"

    # 清理做的事：解除所有暫停、清掉中斷旗標、丟掉 dt 的基準點
    python:
        store._wc6 = WorldClock()

        world.pause("dialogue")
        world.pause("page_popup")
        world.interrupt = True
        world.last_real_time = 12345.0

        world.resume_all()

    $ assert not world.paused, "resume_all 應該解除所有暫停"
    $ assert store._wc6.tick(0.05) > 0.0, "resume_all 之後時鐘要推得動"

    # --- 這些狀態必須被倒帶追蹤 ---
    #
    # 倒帶會重播 `$ world.pause(...)` 這種語句。計數器如果放在
    # NoRollback 的時鐘物件上，+1 會被重播、-1 不會補回來，
    # 每倒帶一次就永久多一層 —— 時鐘從此不動。
    # 所以它們必須是普通的 store 變數 (會被倒帶還原)，
    # 而 elapsed 相反，必須留在 NoRollback 上 (每秒改 20 次)。
    python:
        store._rb_roots = renpy.game.log.get_roots()
        store._tracked = (
            "store.world_pause_counts" in store._rb_roots
            and "store.world_dispatch_depth" in store._rb_roots
            and "store.world_pause_stack" in store._rb_roots
        )

    $ assert store._tracked, "暫停計數與派發層數必須是被倒帶追蹤的 store 變數，不能放在 NoRollback 的時鐘上"
    $ assert not hasattr(world, "pause_counts"), "計數不該又在時鐘物件上留一份 (兩份會不同步)"
    $ assert not hasattr(world, "dispatch_depth"), "派發層數不該又在時鐘物件上留一份"

    # 收尾：不要把全域時鐘留在暫停狀態，不然後面的測試與遊戲本體會被影響
    python:
        world.resume_all()
        world.reset_dispatch()
        world.interrupt = False
        world.last_real_time = None


# TIMER trigger：時間驅動的事件。
#
# 這個 testcase 會隨著 TIMER 的實作一步一步長大。
# 目前到第 2 步：
#   第 1 步 (純資料) TriggerType.TIMER 與 Event.delay 的驗證
#   第 2 步 (純邏輯) 房間內的計時與「哪些到點了」
# 派發還沒接上。
testcase timer_event_checks:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    # --- 正常情況 ---
    python:
        store._tev = Event(
            id="t.ghost",
            trigger=TriggerType.TIMER,
            delay=20,
            effect=Effect(label="t_ghost"),
        )

    $ assert store._tev.delay == 20, f"delay 應該存起來，實際 {store._tev.delay}"
    $ assert Event(id="t.f", trigger=TriggerType.TIMER, delay=2.5).delay == 2.5, "小數秒數也要能填"

    # 沒填 delay 的一般事件，delay 是 None
    $ assert Event(id="t.plain").delay is None, "沒填 delay 就該是 None"

    # --- delay 與 TIMER 必須成對 ---
    python:
        def _delay_raises(**kw):
            try:
                Event(id="t.bad", **kw)
            except ValueError:
                return True
            return False

    # 最容易犯的錯：填了 delay 卻忘了寫 trigger。
    # 不擋的話它會變成「一進房間就觸發」—— 看起來有在動，但時間完全沒生效。
    $ assert _delay_raises(delay=5), "填了 delay 卻沒寫 trigger=TIMER 要報錯"
    $ assert _delay_raises(trigger=TriggerType.ENTER_ROOM, delay=5), "trigger 不是 TIMER 卻填 delay 要報錯"
    $ assert _delay_raises(trigger=TriggerType.TIMER), "trigger=TIMER 卻沒填 delay 要報錯"

    # --- delay 的值域 ---
    $ assert _delay_raises(trigger=TriggerType.TIMER, delay=0), "delay=0 要報錯 (那是 ENTER_ROOM 的事)"
    $ assert _delay_raises(trigger=TriggerType.TIMER, delay=-3), "負的 delay 要報錯"
    $ assert _delay_raises(trigger=TriggerType.TIMER, delay=True), "bool 是 int 的子類別，delay=True 幾乎一定是手滑"
    $ assert _delay_raises(trigger=TriggerType.TIMER, delay="5"), "字串要報錯"

    # --- 掛在 Room.events 上不會被進房事件誤觸發 ---
    #
    # 這是第 1 步最重要的安全性質：TIMER 事件跟進房事件混在同一個
    # Room.events 清單裡，進房間時絕對不能跟著一起跑
    # (不然 delay 等於沒意義，鬼一進門就出現)。
    python:
        store._t_gs = GameState()
        store._t_ctx = EventContext(store._t_gs)

        store._t_mixed = [
            Event(id="t.on_enter", effect=Effect(label="t_enter")),
            Event(id="t.timed", trigger=TriggerType.TIMER, delay=10,
                effect=Effect(label="t_timed")),
        ]

        # 模擬進房間的派發：Room.events 的預設時機是 ENTER_ROOM
        store._t_enter_labels = collect_events(
            store._t_mixed,
            TriggerType.ENTER_ROOM,
            store._t_ctx,
            TriggerType.ENTER_ROOM,
        )

    $ assert store._t_enter_labels == ["t_enter"], f"進房間只該跑進房事件，實際 {store._t_enter_labels}"

    # 明寫的 trigger 要蓋過掛載位置的預設值
    $ assert store._t_mixed[1].trigger_type(TriggerType.ENTER_ROOM) == TriggerType.TIMER, "明寫 TIMER 應該蓋過 Room.events 的預設 ENTER_ROOM"
    $ assert not store._t_mixed[1].can_fire(store._t_ctx, TriggerType.ENTER_ROOM, TriggerType.ENTER_ROOM), "TIMER 事件不該在進房派發時通過"

    # ------------------------------------------------------------------
    # 第 2 步：房間內的計時與「哪些到點了」
    # ------------------------------------------------------------------

    # --- time_in_room / mark_room_entered ---
    #
    # 直接設定 elapsed 來製造時間，不用真的 tick 幾百次 ——
    # 要驗的是「到點的判斷」，時間怎麼累加起來的在 world_clock_checks 驗過了。
    # (跟 camera 的回歸測試直接設 camera.offset 是同一個理由)
    python:
        store._t_wc = WorldClock()
        store._t_wc.elapsed = 30.0
        store._t_wc.mark_room_entered()

        store._t_in_room_fresh = store._t_wc.time_in_room

        store._t_wc.elapsed = 48.5
        store._t_in_room_later = store._t_wc.time_in_room

    $ assert store._t_in_room_fresh == 0.0, f"剛進房間應該是 0 秒，實際 {store._t_in_room_fresh}"
    $ assert store._t_in_room_later == 18.5, f"待了 18.5 秒，實際 {store._t_in_room_later}"

    # 換房間重置：這是使用者 2026-10-20 選的 (a) 純重置
    $ store._t_wc.mark_room_entered()
    $ assert store._t_wc.time_in_room == 0.0, "換房間應該把房間內的計時歸零"
    $ assert store._t_wc.elapsed == 48.5, "換房間不該動到世界時鐘的總秒數"

    # --- due_timer_events ---
    python:
        store._t_events = [
            # 一般的進房事件：不管待多久都不該被挑出來
            Event(id="t2.enter", effect=Effect(label="t2_enter")),

            # 點熱點的事件：同理
            Event(id="t2.click", trigger=TriggerType.CLICK_HOTSPOT,
                effect=Effect(label="t2_click")),

            # 三個 TIMER，delay 與 sequence 刻意「不同序」——
            # 這樣才驗得出排序是照 sequence 而不是照 delay 或清單順序
            Event(id="t2.late_but_important", trigger=TriggerType.TIMER, delay=10,
                sequence=-5, effect=Effect(label="t2_important")),
            Event(id="t2.early", trigger=TriggerType.TIMER, delay=5,
                sequence=10, effect=Effect(label="t2_early")),
            Event(id="t2.very_late", trigger=TriggerType.TIMER, delay=60,
                sequence=0, effect=Effect(label="t2_very_late")),
        ]

        def _due_ids(seconds):
            return [e.id for e in due_timer_events(store._t_events, seconds)]

    $ assert _due_ids(0) == [], f"剛進房間不該有任何事件到點，實際 {_due_ids(0)}"
    $ assert _due_ids(4.9) == [], f"還沒到 delay 就不該到點，實際 {_due_ids(4.9)}"

    # 邊界：剛好等於 delay 要算到點 (用 >= 不是 >)
    $ assert _due_ids(5) == ["t2.early"], f"剛好等於 delay 就該到點，實際 {_due_ids(5)}"

    # 兩個都到點時，依 sequence 排序 —— sequence 小的在前面 (比較重要)。
    # 注意 late_but_important 的 delay 比較晚、在清單裡也比較前面，
    # 所以這一條如果排序寫錯 (照 delay 或照清單順序)，結果會不一樣。
    $ assert _due_ids(10) == ["t2.late_but_important", "t2.early"], f"應該照 sequence 排序，實際 {_due_ids(10)}"
    $ assert _due_ids(999) == ["t2.late_but_important", "t2.very_late", "t2.early"], f"全部到點也要照 sequence 排序，實際 {_due_ids(999)}"

    # 非 TIMER 的事件永遠不會被挑出來，待多久都一樣
    $ assert "t2.enter" not in _due_ids(999), "進房事件不該被當成到點的計時事件"
    $ assert "t2.click" not in _due_ids(999), "點擊事件不該被當成到點的計時事件"

    # 空清單不該出錯
    $ assert due_timer_events([], 999) == []
    $ assert due_timer_events(None, 999) == []

    # --- 只管時間，不管能不能觸發 ---
    #
    # 條件不符的事件照樣會被挑出來 —— 「時間到了」跟「能不能發生」
    # 是兩個問題，後者由 collect_events 回答。
    # 混在一起的話，第 4 步「最重要的那個條件不符就往下找」會無從實作。
    python:
        store._t_blocked = [
            Event(id="t2.blocked", trigger=TriggerType.TIMER, delay=5,
                condition=Condition(require=["something_we_dont_have"]),
                effect=Effect(label="t2_blocked")),
        ]
        store._t_blocked_due = [e.id for e in due_timer_events(store._t_blocked, 10)]

    $ assert store._t_blocked_due == ["t2.blocked"], "due_timer_events 不該過濾條件，那是 collect_events 的事"

    # ------------------------------------------------------------------
    # 第 3 步：重入保護 (正在演事件時，計時器只排隊不插隊)
    # ------------------------------------------------------------------

    # 派發層數放在被倒帶追蹤的 store 變數 (world_dispatch_depth)，
    # 不在時鐘物件上，所以這裡用全域的 world 驗，開頭先歸零。
    python:
        world.reset_dispatch()

        store._wd_idle = world.dispatching

        world.begin_dispatch()
        store._wd_in = world.dispatching

        # 嵌套：事件的 label 裡呼叫 change_room()，裡面又跑一次 run_event_labels
        world.begin_dispatch()
        world.end_dispatch()
        store._wd_inner_done = world.dispatching

        world.end_dispatch()
        store._wd_all_done = world.dispatching

    $ assert not store._wd_idle, "一開始不該是派發中"
    $ assert store._wd_in, "begin_dispatch 之後應該是派發中"
    $ assert store._wd_inner_done, "內層結束時外層還在演，應該仍是派發中 (寫成 bool 的話這條會死)"
    $ assert not store._wd_all_done, "兩層都結束才該離開派發中"

    # 多結算幾次不該變成負數。
    #
    # 死亡流程是 jump 走不回來的，所以 end_dispatch 有可能少呼叫 ——
    # 反過來若讓層數變成負數，之後就再也進不了「派發中」狀態，
    # 計時器會在對話中途插隊。
    python:
        world.end_dispatch()
        world.end_dispatch()
        world.begin_dispatch()
        store._wd_after_underflow = world.dispatching

    $ assert store._wd_after_underflow, "多結算幾次之後，begin_dispatch 一次就該進得了派發中"

    # 讀檔要能把層數清掉。
    #
    # 玩家在對話中途存檔，存檔裡的層數是 1，但讀回來那段對話不會繼續演，
    # 永遠不會有對應的 end_dispatch —— 不清的話計時器從此不發動。
    # 跟暫停理由是完全同一類的坑。
    python:
        world.reset_dispatch()
        world.begin_dispatch()
        world.begin_dispatch()
        world.reset_dispatch()

    $ assert not world.dispatching, "reset_dispatch 應該把層數歸零"
    $ assert world_clock_after_load in config.after_load_callbacks, "讀檔清理必須掛著，不然對話中途存檔會讓計時器永遠不發動"

    # ------------------------------------------------------------------
    # 第 4 步：max_fires（同時到點時只放最重要的那一個）
    # ------------------------------------------------------------------

    # --- 只放一個，而且是 sequence 最小的那個 ---
    python:
        store._mf_gs = GameState()
        store._mf_ctx = EventContext(store._mf_gs)

        store._mf_events = [
            Event(
                id="mf.important",
                trigger=TriggerType.TIMER,
                delay=5,
                sequence=-5,
                effect=Effect(label="mf_important"),
            ),
            Event(
                id="mf.also_due",
                trigger=TriggerType.TIMER,
                delay=5,
                sequence=0,
                effect=Effect(label="mf_also_due"),
            ),
        ]

        store._mf_due = due_timer_events(store._mf_events, 10)
        store._mf_labels = collect_events(
            store._mf_due,
            TriggerType.TIMER,
            store._mf_ctx,
            TriggerType.TIMER,
            max_fires=1,
        )

    $ assert store._mf_labels == ["mf_important"], f"只該放最重要的那一個，實際 {store._mf_labels}"

    # 沒被放的那個不能被消耗掉 —— 次數不加、也不該死亡，
    # 不然它下次就永遠不會發生了
    $ assert store._mf_gs.events.count_of("mf.also_due") == 0, "沒被放的事件不該被記成觸發過"
    $ assert not store._mf_gs.events.is_dead("mf.also_due"), "沒被放的事件不該死亡"
    $ assert store._mf_gs.events.count_of("mf.important") == 1, "被放的那個要記一次"

    # --- 最重要的那個條件不成立時要往下找 (使用者 2026-10-21 選的 (ii)) ---
    #
    # 這是 max_fires 不能寫成「外面挑一個送進來」的理由：
    # 那樣做的話，一個條件沒滿足的高優先事件會把整件事吞掉，
    # 玩家什麼都沒發生，而這種 bug 最難查。
    python:
        store._mf_gs2 = GameState()
        store._mf_ctx2 = EventContext(store._mf_gs2)

        store._mf_blocked = [
            Event(
                id="mf.blocked_important",
                trigger=TriggerType.TIMER,
                delay=5,
                sequence=-5,
                condition=Condition(require=["we_dont_have_this"]),
                effect=Effect(label="mf_blocked"),
            ),
            Event(
                id="mf.fallback",
                trigger=TriggerType.TIMER,
                delay=5,
                sequence=0,
                effect=Effect(label="mf_fallback"),
            ),
        ]

        store._mf_labels2 = collect_events(
            due_timer_events(store._mf_blocked, 10),
            TriggerType.TIMER,
            store._mf_ctx2,
            TriggerType.TIMER,
            max_fires=1,
        )

    $ assert store._mf_labels2 == ["mf_fallback"], f"最重要的那個條件不成立時應該往下找，實際 {store._mf_labels2}"
    $ assert store._mf_gs2.events.count_of("mf.blocked_important") == 0, "條件不符的事件不該被記成觸發過"

    # --- max_fires=None 要維持原本的行為 (全部放) ---
    #
    # 這個參數是新加的，既有的呼叫端 (進房、點熱點) 都沒傳，
    # 所以預設一定要跟以前一樣。
    python:
        store._mf_gs3 = GameState()
        store._mf_all = collect_events(
            [
                Event(id="mf.a", sequence=0, effect=Effect(label="mf_a")),
                Event(id="mf.b", sequence=1, effect=Effect(label="mf_b")),
            ],
            TriggerType.ENTER_ROOM,
            EventContext(store._mf_gs3),
            TriggerType.ENTER_ROOM,
        )

    $ assert store._mf_all == ["mf_a", "mf_b"], f"沒傳 max_fires 就該全部放，實際 {store._mf_all}"

    # --- 計時事件的 limit 只能是 1 ---
    #
    # 時間過了之後會「一直」是已經過了，所以 limit 不是 1 的計時事件
    # 會在同一趟進房間裡每 0.2 秒重複觸發。
    # 擋在建立房間的當下，而不是等玩家被無限轟炸才發現。
    $ assert _delay_raises(trigger=TriggerType.TIMER, delay=5, limit=None), "計時事件不准設成無限次"
    $ assert _delay_raises(trigger=TriggerType.TIMER, delay=5, limit=2), "limit=2 也會在 0.2 秒內連放兩次，要擋"
    $ assert Event(id="t.ok", trigger=TriggerType.TIMER, delay=5, limit=1).delay == 5, "明寫 limit=1 要能過"

    # demo 的實驗區應該有一個可以實際玩到的計時事件
    python:
        store._pg_timed = [
            _e for _e in rooms["playground"].events
            if _e.trigger == TriggerType.TIMER
        ]

    $ assert store._pg_timed, "實驗區應該有一個計時事件可以實際測試"
    $ assert store._pg_timed[0].delay > 0

    # ------------------------------------------------------------------
    # next_timer_wait：要不要「設鬧鐘」，以及睡多久
    # ------------------------------------------------------------------
    #
    # 這關係到倒帶檢查點：renpy.pause 沒有時間限制時會留檢查點、
    # 有時間限制時不會。所以回傳 None (不設鬧鐘) 的房間，
    # 檢查點行為要跟沒有計時器的年代完全一樣。

    python:
        store._nw_gs = GameState()

        store._nw_plain = [
            Event(id="nw.enter", effect=Effect(label="nw_enter")),
            Event(id="nw.click", trigger=TriggerType.CLICK_HOTSPOT,
                effect=Effect(label="nw_click")),
        ]

        store._nw_timed = [
            Event(id="nw.t10", trigger=TriggerType.TIMER, delay=10,
                effect=Effect(label="nw_t10")),
            Event(id="nw.t25", trigger=TriggerType.TIMER, delay=25,
                effect=Effect(label="nw_t25")),
        ]

    # 沒有計時事件的房間 -> 不設鬧鐘
    $ assert next_timer_wait([], 0, store._nw_gs) is None, "空清單不該設鬧鐘"
    $ assert next_timer_wait(None, 0, store._nw_gs) is None, "None 不該設鬧鐘"
    $ assert next_timer_wait(store._nw_plain, 999, store._nw_gs) is None, "只有進房/點擊事件的房間不該設鬧鐘 (不然檢查點回不來)"

    # 有計時事件 -> 睡到「最近的那一個」到點
    $ assert next_timer_wait(store._nw_timed, 0, store._nw_gs) == 10, f"剛進房間應該睡 10 秒，實際 {next_timer_wait(store._nw_timed, 0, store._nw_gs)}"
    $ assert abs(next_timer_wait(store._nw_timed, 2.7, store._nw_gs) - 7.3) < 1e-9, "待了 2.7 秒應該睡 7.3 秒"
    # 過期但還活著 = 它現在就該觸發了，所以要立刻醒來 (回傳下限)，
    # 不是跑去等下一個。等下一個是「前一個已經死掉」才會發生的事。
    $ assert next_timer_wait(store._nw_timed, 12, store._nw_gs) == WORLD_WAIT_FLOOR, f"過期但還活著的事件應該讓迴圈立刻醒來，實際 {next_timer_wait(store._nw_timed, 12, store._nw_gs)}"

    # 時間已經過了 -> 夾在下限，不能回傳 0 或負數 (會空轉燒 CPU)
    $ assert next_timer_wait(store._nw_timed, 10, store._nw_gs) == WORLD_WAIT_FLOOR, "剛好到點時要回傳下限"
    $ assert next_timer_wait(store._nw_timed, 999, store._nw_gs) == WORLD_WAIT_FLOOR, "全部過期時要回傳下限，不能是負數"

    # --- 死掉的計時事件不該讓房間一直掛著鬧鐘 ---
    #
    # 這條最容易漏：事件放完就死了，如果還把它算進來，
    # 這個房間會永遠停在「有鬧鐘」的狀態 —— 於是倒帶檢查點永遠回不來，
    # 而畫面上完全看不出有什麼不對。
    python:
        store._nw_gs2 = GameState()
        store._nw_gs2.events.record_trigger("nw.t10", 1)
        store._nw_gs2.events.record_trigger("nw.t25", 1)

        store._nw_all_dead = next_timer_wait(store._nw_timed, 0, store._nw_gs2)

    $ assert store._nw_gs2.events.is_dead("nw.t10"), "這個測試的前提是事件已經死了"
    $ assert store._nw_all_dead is None, "計時事件都死了之後就不該再設鬧鐘 (不然檢查點永遠回不來)"

    # 只死一個 -> 還是要等活著的那個
    python:
        store._nw_gs3 = GameState()
        store._nw_gs3.events.record_trigger("nw.t10", 1)
        store._nw_half = next_timer_wait(store._nw_timed, 0, store._nw_gs3)

    $ assert store._nw_half == 25, f"活著的那個還是要等，應該是 25，實際 {store._nw_half}"

    # 這才是「睡到下一個」真正會發生的情況：第一個已經觸發過而死掉，
    # 時間也已經超過它，所以輪到等第二個 (25-12)。
    $ assert next_timer_wait(store._nw_timed, 12, store._nw_gs3) == 13, f"第一個死掉之後應該睡到第二個，實際 {next_timer_wait(store._nw_timed, 12, store._nw_gs3)}"


# 近景視窗的純邏輯：換圖規則、框的高度、誤用檢查。
#
# 這三樣全部抽成純函式，所以完全不用把視窗叫出來 ——
# 餵假的狀態、假的房間就能驗完。
testcase closeup_checks:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    # --- room_bg_height：沒填就是拉滿螢幕高 ---
    #
    # 這條守著「bg_height 是純加法」這件事：所有既有房間都沒填它，
    # 行為必須跟這個欄位出現之前一模一樣。
    python:
        store._cu_plain = Room(name="cu_plain", background=None, bg_width=1920)
        store._cu_framed = Room(name="cu_framed", background=None, bg_width=1280, bg_height=720)

    $ assert room_bg_height(store._cu_plain) == config.screen_height, f"沒填 bg_height 的房間要拉滿螢幕高 {config.screen_height}，實際 {room_bg_height(store._cu_plain)}"
    $ assert room_bg_height(store._cu_framed) == 720, f"填了就用填的值，實際 {room_bg_height(store._cu_framed)}"

    # --- pick_state_image：由上往下試，第一個成立的就贏 ---
    python:
        store._cu_gs = GameState()

        store._cu_cases = [
            (Condition(require=["lamp_on", "fuse"]), "both.png"),
            (Condition(require=["lamp_on"]), "lamp.png"),
        ]

    # 什麼都沒有 -> default
    $ assert pick_state_image(store._cu_cases, "dark.png", store._cu_gs.view()) == "dark.png", "全都不成立時要用 default"

    # 只有燈 -> 第二條 (第一條還不成立)
    $ store._cu_gs.flags.set("lamp_on")
    $ assert pick_state_image(store._cu_cases, "dark.png", store._cu_gs.view()) == "lamp.png", "只有燈時應該挑第二條"

    # 燈加保險絲 -> 第一條，不是第二條。
    # 這條守著「順序有意義」：兩條都成立時，寫在前面的贏。
    $ store._cu_gs.inventory.add("fuse")
    $ assert pick_state_image(store._cu_cases, "dark.png", store._cu_gs.view()) == "both.png", "兩條都成立時要挑寫在前面的那一條"

    # 沒有任何 case 時就是 default
    $ assert pick_state_image([], "dark.png", store._cu_gs.view()) == "dark.png", "沒有 case 就該是 default"

    # 不給 view 的話會去問目前的遊戲狀態，不該爆掉
    $ assert pick_state_image([], "dark.png") == "dark.png", "不給 view 時要能自己去問遊戲狀態"

    # --- state_image 的寫法驗證 ---
    #
    # 這些錯誤的症狀都是「圖就是沒換」，靠試玩很難確定問題在哪，
    # 所以寧可在 build_rooms() 當下就爆掉 (= 遊戲一啟動就看得到)。
    python:
        def _si_raises(*cases, **kwargs):
            try:
                state_image(*cases, **kwargs)
            except (ValueError, TypeError):
                return True
            return False

    $ assert _si_raises((Condition(require=["a"]), "a.png")), "沒填 default 要報錯 (不然某些狀態下會變全黑)"
    $ assert _si_raises(default="d.png"), "一組 case 都沒有要報錯 (那直接寫 background= 就好)"
    $ assert _si_raises(Condition(require=["a"]), "a.png", default="d.png"), "漏了括號、把 tuple 寫成散的參數要報錯"
    $ assert _si_raises(("a.png",), default="d.png"), "tuple 長度不是 2 要報錯"
    $ assert _si_raises(("not_a_condition", "a.png"), default="d.png"), "第一個不是 Condition 要報錯"
    $ assert _si_raises((None, "a.png"), default="d.png"), "None 不是 Condition，要報錯 (想要一定成立請用 default)"
    $ assert _si_raises((Condition(require=["a"]), "a.png"), default="d.png", wat=1), "不認得的參數要報錯"

    # 寫對的話要能建起來，而且挑圖的結果跟 pick_state_image 一致
    python:
        store._cu_img = state_image(
            (Condition(require=["lamp_on"]), "lamp.png"),
            default="dark.png",
        )
        # DynamicDisplayable 把 (cases, default) 原樣收在 args 裡，
        # 所以可以直接拿出來驗「建出來的東西挑圖是對的」。
        store._cu_picked = pick_state_image(*store._cu_img.args, view=store._cu_gs.view())

    $ assert store._cu_picked == "lamp.png", f"燈開著應該挑 lamp.png，實際 {store._cu_picked}"

    # --- closeup_misuse：近景只處理點擊，其他時機要主動擋 ---
    #
    # 為什麼要擋：近景房間寫了 on_enter 的話那句開場白永遠不會播，
    # 而畫面上完全看不出有什麼不對 —— 遊戲照跑、框照開，台詞人間蒸發。
    python:
        store._cu_ok = Room(
            name="cu_ok", background=None, bg_width=1280, bg_height=720,
            hotspots=[Hotspot(name="h", x=0, y=0, on_click="whatever")],
        )

        store._cu_no_height = Room(name="cu_nh", background=None, bg_width=1280)

        store._cu_enter = Room(
            name="cu_enter", background=None, bg_width=1280, bg_height=720,
            on_enter="never_runs",
        )

        store._cu_music = Room(
            name="cu_music", background=None, bg_width=1280, bg_height=720,
            music="audio/never.ogg",
        )

        store._cu_room_event = Room(
            name="cu_re", background=None, bg_width=1280, bg_height=720,
            events=[Event(id="cu_re.never")],
        )

        store._cu_bad_trigger = Room(
            name="cu_bt", background=None, bg_width=1280, bg_height=720,
            hotspots=[Hotspot(name="h", x=0, y=0, events=[
                Event(id="cu_bt.timed", trigger=TriggerType.TIMER, delay=5),
            ])],
        )

    $ assert closeup_misuse(store._cu_ok) == [], f"寫對的近景房間不該有任何問題，實際 {closeup_misuse(store._cu_ok)}"
    $ assert closeup_misuse(store._cu_no_height), "沒填 bg_height 要被抓到 (不然框會拉滿螢幕高)"
    $ assert closeup_misuse(store._cu_enter), "on_enter 不會被執行，要被抓到"
    $ assert closeup_misuse(store._cu_music), "music 不會被播放，要被抓到"
    $ assert closeup_misuse(store._cu_room_event), "掛在房間上的 events 不會被執行，要被抓到"
    $ assert closeup_misuse(store._cu_bad_trigger), "熱點事件寫了非點擊的 trigger 要被抓到"

    # 熱點事件沒寫 trigger (預設就是點擊) 不該被誤報
    python:
        store._cu_default_trigger = Room(
            name="cu_dt", background=None, bg_width=1280, bg_height=720,
            hotspots=[Hotspot(name="h", x=0, y=0, events=[Event(id="cu_dt.click")])],
        )

    $ assert closeup_misuse(store._cu_default_trigger) == [], "沒寫 trigger 的熱點事件就是點擊，不該被誤報"

    # 明確寫 CLICK_HOTSPOT 也不該被誤報
    python:
        store._cu_explicit = Room(
            name="cu_ex", background=None, bg_width=1280, bg_height=720,
            hotspots=[Hotspot(name="h", x=0, y=0, events=[
                Event(id="cu_ex.click", trigger=TriggerType.CLICK_HOTSPOT),
            ])],
        )

    $ assert closeup_misuse(store._cu_explicit) == [], "明確寫 CLICK_HOTSPOT 不該被誤報"


# 近景視窗走一遍完整流程：
#   開框 -> 點裡面的照片 -> 框消失、講話 -> 框回來 (照片不見了、底圖變空)
#   -> 按 ✕ 關掉 -> 回到探索
#
# 另外守住四件近景的設計承諾：
#   1. 近景期間世界時鐘照跑 (不暫停)
#   2. 近景房間「不會」變成 current_room —— 不然開抽屜就能無限躲鬼
#   3. 房間內的計時不會被近景重設
#   4. 倒帶不會卡在近景視窗裡
#
# 第 4 點本來想加在 rollback_through_modals 裡 (那裡已經有翻頁視窗與
# 解謎關卡兩段)，但從廚房走到實驗區要多繞五六步，逾時風險比較高。
# 這個 testcase 本來就站在實驗區，所以放這裡。
testcase closeup_flow:

    # 70 秒不是隨便填的：這個 testcase 裡有三段刻意的等待
    # (驗計時用的 pause 1.0 兩次、各種 pause 0.5)，再加上倒帶之後
    # 要把整段近景往前重走一遍。40 秒會剛好不夠。
    $ __import__("renpy").test.testsettings._test.timeout = 70.0
    $ _trace_reset()

    click "開始"
    advance until "前往實驗區(測試區)"

    # 先把實驗區的計時事件殺掉。
    #
    # 近景期間時鐘是「刻意繼續跑」的，所以這個測試只要跑超過 10 秒，
    # 那個腳步聲事件就會在中間插進來，讓斷言變得看運氣。
    # 這不是在迴避 bug —— 計時事件本身由 timer_event_checks 守著。
    $ game_state.events.kill("playground.timer_demo")

    click "前往實驗區(測試區)"
    advance until "🗄 抽屜"
    $ _trace("1_到了實驗區")

    # 先在房間裡站一秒，讓「待了多久」累積出看得出來的量。
    #
    # 不這樣做的話 time_in_room 可能只有 0.0x 秒，底下那條
    # 「近景不該重設計時」的斷言就沒有辨識力 —— 真的被重設成 0
    # 跟本來就趨近 0 看起來一樣。
    pause 1.0

    # 順便守住「探索畫面上時鐘真的在走」。
    # 其他地方只斷言過它「不會變小」，沒有任何一條證明它會變大 ——
    # 驅動時鐘的是 overlay 上那個 timer，整套機制壞掉的話這裡會先叫。
    $ assert world.elapsed > 0.5, f"在探索畫面站了一秒，時鐘應該走了約 1 秒，實際 {world.elapsed}"

    # 進近景之前先記下「在房間待了多久」與底圖是哪一張
    python:
        _rb.cu_time_before = world.time_in_room
        # DynamicDisplayable 把 (cases, default) 原樣收在 args 裡
        _rb.cu_bg_before = pick_state_image(*rooms["playground_drawer"].background.args)

    click "🗄 抽屜"

    # 拉開抽屜那句話講完，框就會跳出來 —— 框裡的照片按鈕出現就代表到了
    advance until "🖼 撕成兩半的照片"

    $ assert renpy.get_screen("closeup") is not None, "點抽屜應該打開近景視窗"
    $ assert not game_state.inventory.has("torn_photo"), "這個測試的前提是照片還沒拿"
    $ _trace("2_近景視窗打開了")

    # 承諾 1：近景期間時鐘照跑。
    #
    # 近景是從熱點的 label 叫出來的，而那些 label 由 run_event_labels 執行，
    # 那裡為了對話把時鐘暫停了 —— 所以這裡會是「沒暫停」唯一的理由
    # 就是 open_closeup 有正確地讓開 (world.suspend_pauses)。
    $ assert not world.paused, f"近景期間世界時鐘不該暫停，實際暫停理由 {world.pause_reasons}"

    # 承諾 2：近景房間不是 current_room
    $ assert current_room.name == "playground", f"近景不該變成當前房間，實際 {current_room.name}"

    # --- 點照片：框消失、講話 ---
    click "🖼 撕成兩半的照片"
    pause 0.5

    $ assert renpy.get_screen("closeup") is None, "點到東西時框應該消失 (對話才不會被框蓋住)"
    $ _trace("3_點了照片，框消失")

    # 記下「正在近景的對話裡」這一刻的暫停計數與派發層數。
    # 測試最後倒帶回到這個時刻時要跟它比對 —— 見檔尾「承諾 5」。
    #
    # 放在 _rb (NoRollback) 裡，不然倒帶會把這兩個值也一起還原掉，
    # 比對就變成「自己跟自己比」，永遠成立。
    python:
        _rb.cu_counts_in_dialogue = dict(store.world_pause_counts)
        _rb.cu_depth_in_dialogue = store.world_dispatch_depth

    # --- 講完話框要回來 ---
    #
    # 用「抽屜底板」當判定：那顆按鈕只存在於近景視窗裡，
    # 它出現就代表框真的回來了。
    advance until "🔍 抽屜底板"

    $ assert renpy.get_screen("closeup") is not None, "講完話框應該再打開"
    $ assert game_state.inventory.has("torn_photo"), "點照片應該拿到照片"
    $ _trace("4_框回來了，照片拿到手")

    # 照片熱點要消失 —— 熱點與底圖是同一個條件的兩面
    python:
        _rb.cu_photo_shown = hotspot_is_shown(
            rooms["playground_drawer"].get_hotspot("photo")
        )
        _rb.cu_bg_after = pick_state_image(*rooms["playground_drawer"].background.args)

    $ assert not _rb.cu_photo_shown, "拿走之後照片熱點應該消失"
    $ assert _rb.cu_bg_after != _rb.cu_bg_before, "拿走之後抽屜的底圖應該換掉 (空抽屜)"
    $ _trace("5_熱點消失、底圖換了")

    # 照片熱點不見了，但底板還在 = 框是「部分更新」不是整個重畫錯
    assert not "🖼 撕成兩半的照片"

    # --- 關掉視窗 ---
    click "✕"
    advance until "🗄 抽屜"

    $ assert renpy.get_screen("closeup") is None, "按 ✕ 應該關掉近景視窗"
    $ assert renpy.get_screen("explore") is not None, "關掉之後要回到探索畫面"
    $ assert current_room.name == "playground", "關掉之後還在原本的房間"
    $ _trace("6_關掉回到探索")

    # 承諾 3：房間內的計時不會被近景重設。
    #
    # 如果 open_closeup 不小心呼叫了 change_room / mark_room_entered，
    # 這個值會掉回 0 附近 —— 那玩家就能靠一直開抽屜無限躲鬼。
    $ assert world.time_in_room >= _rb.cu_time_before, f"近景不該重設房間內的計時，進去前 {_rb.cu_time_before}、出來後 {world.time_in_room}"

    # --- 承諾 4：倒帶不能卡在近景視窗裡 ---
    #
    # 「卡住」的判定方式跟 rollback_through_modals 一樣：連按兩次「返回」。
    # 如果倒帶停在近景裡，近景是 modal 會擋住「返回」鈕，
    # 第二次就會找不到可以點的按鈕而逾時。
    click "返回"
    pause 0.5
    $ assert renpy.get_screen("closeup") is None, "倒帶不該回到近景視窗裡"
    $ _trace("7_返回一次沒進近景")

    click "返回"
    pause 0.5
    $ assert renpy.get_screen("closeup") is None, "繼續倒帶也不該回到近景視窗裡"
    $ _trace("8_返回兩次沒卡住")

    # 把測試游標從「返回」鈕上移開，不然之後推進對話等於又按了一次返回。
    # (這個坑的完整說明見 rollback_through_modals)
    move pos (960, 300)


    # --- 承諾 5：倒帶穿過近景不能把暫停計數灌大 ---
    #
    # 這條來自使用者 2026-10-26 的手動測試：在近景裡拿照片 -> 停在對話上
    # (時鐘暫停是對的) -> 按返回 -> 10 秒事件還能正確觸發。
    #
    # 背景：2026-10-25 修過一個同族的 bug —— 暫停計數原本放在 NoRollback
    # 上，而倒帶是「把執行位置倒回去再重新執行」，所以
    # $ world.pause("dialogue") 那一行會被重播，計數卻不跟著倒回去。
    # +1 重播了、-1 沒補回來，於是時鐘永久停住、鬼再也不會來，
    # 而畫面上完全看不出有什麼不對。
    #
    # 判定方式是「跟原本那一刻比對」，不是斷言絕對數字。
    # 絕對數字不能用：近景裡的對話會讓 run_event_labels 嵌套
    # (外層是「你拉開抽屜」那串)，所以 {'dialogue': 2} 在這個時刻
    # 本來就是合法的 —— 剛好跟當初那個 bug 的數值一樣。
    #
    # 上面那兩次 click "返回" 剛好停在點照片後的那句對話上，
    # 也就是第 3 步記下數值的同一個時刻。
    #
    # ⚠️ 這兩條能抓到什麼、抓不到什麼 (做破壞驗證時才發現的，不要誤信)：
    #
    #   抓得到：計數仍然放在 store 上，但倒帶前後對不起來
    #           (例如有人把 pause/resume 改成不成對，或在倒帶紀錄之外偷改)。
    #
    #   抓不到：有人把計數整個搬回 NoRollback 物件上 —— 那時
    #           store.world_pause_counts 會永遠是 {}，倒帶前後都是 {}，
    #           這兩條會「相等」而通過，但真正的 bug 已經回來了。
    #
    # 要抓住後者只能靠行為：把整串對話推完、回到探索、確認時鐘真的恢復。
    # 那條路被測試框架擋住了 (理由見下面)，所以**那一哩仍然只有手動測試**。
    # 不要因為這兩條是綠的就以為那個 bug 已經被自動化守住了。
    python:
        _rb.cu_counts_after_rollback = dict(store.world_pause_counts)
        _rb.cu_depth_after_rollback = store.world_dispatch_depth

    $ _trace("9_量倒帶後的暫停計數")

    $ assert _rb.cu_counts_after_rollback == _rb.cu_counts_in_dialogue, f"倒帶不該改變暫停計數 (改變了就表示 pause/resume 沒有成對地被倒帶)。倒帶前 {_rb.cu_counts_in_dialogue}、倒帶後 {_rb.cu_counts_after_rollback}"
    $ assert _rb.cu_depth_after_rollback == _rb.cu_depth_in_dialogue, f"倒帶不該改變派發層數 (層數只增不減的話計時器會從此不發動)。倒帶前 {_rb.cu_depth_in_dialogue}、倒帶後 {_rb.cu_depth_after_rollback}"

    # 為什麼這裡不繼續「往前推回探索、確認時鐘真的恢復」：
    #
    # 試過，三種方式都走不通，而且全都是測試框架的限制，不是產品問題：
    #   1. advance until "🗄 抽屜"  -> 那顆按鈕早就在了 (內層對話收尾時
    #      就 show screen explore，探索畫面一直在框後面)，所以會直接返回、
    #      完全沒推進對話；而對話還掛著時暫停是對的，斷言就誤報。
    #   2. 裸 advance              -> 它會「送 dismiss 再等下一句開始」
    #      (renpy/test/testast.py 的 Advance)，而那是最後一句，
    #      沒有下一句，所以永遠等不到而逾時。
    #   3. click pos 點對話框       -> 點不掉。
    #
    # 所以「倒帶之後時鐘真的恢復、計時事件真的還會來」這件事，
    # 目前只有使用者 2026-10-26 的手動測試證明過，沒有自動化。
    # 這是已知缺口，記在 pending_imp.md 的測試缺口那一節。


# 「鬼到了就把視窗關掉」的純邏輯。
#
# 核心是 pending_interrupt()：它是只讀查詢，視窗畫面每 0.2 秒問一次。
# 所以這裡餵假的事件與假的秒數就能驗完，不用真的等鬼來。
testcase interrupt_checks:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0

    # --- Event.interrupt 的寫法驗證 ---
    python:
        def _int_raises(**kw):
            try:
                Event(id="i.bad", **kw)
            except ValueError:
                return True
            return False

    # 只有計時事件能標。進房／點擊事件是玩家自己的動作引發的，
    # 沒有「打斷」可言 —— 標了完全不會有效果，而那種錯誤看不出來。
    $ assert _int_raises(interrupt=True), "沒寫 trigger 卻標 interrupt=True 要報錯"
    $ assert _int_raises(trigger=TriggerType.ENTER_ROOM, interrupt=True), "進房事件標 interrupt=True 要報錯"
    $ assert _int_raises(trigger=TriggerType.CLICK_HOTSPOT, interrupt=True), "點擊事件標 interrupt=True 要報錯"
    $ assert _int_raises(trigger=TriggerType.TIMER, delay=5, interrupt="yes"), "interrupt 只能是 True/False"
    $ assert _int_raises(trigger=TriggerType.TIMER, delay=5, interrupt=1), "1 不是 bool，要報錯"

    # 寫對的要能建起來，而且預設是 False
    $ assert Event(id="i.ok", trigger=TriggerType.TIMER, delay=5, interrupt=True).interrupt is True, "標了就該是 True"
    $ assert Event(id="i.plain", trigger=TriggerType.TIMER, delay=5).interrupt is False, "沒標就該是 False"
    $ assert Event(id="i.enter").interrupt is False, "進房事件沒標也該是 False (只是不能標 True)"

    # --- pending_interrupt ---
    python:
        store._pi_gs = GameState()
        store._pi_room = Room(name="pi_room", background=None, bg_width=1920)
        store._pi_ctx = EventContext(store._pi_gs, store._pi_room)

        store._pi_marked = Event(
            id="pi.ghost", trigger=TriggerType.TIMER, delay=10, interrupt=True,
        )
        store._pi_plain = Event(
            id="pi.steps", trigger=TriggerType.TIMER, delay=10,
        )
        store._pi_gated = Event(
            id="pi.gated", trigger=TriggerType.TIMER, delay=10, interrupt=True,
            condition=Condition(require=["flashlight"]),
        )

    # 沒有事件 / 沒有標記的事件 -> 不打斷
    $ assert pending_interrupt(None, 999, store._pi_ctx) is None, "沒有事件不該打斷"
    $ assert pending_interrupt([], 999, store._pi_ctx) is None, "空清單不該打斷"
    $ assert pending_interrupt([store._pi_plain], 999, store._pi_ctx) is None, "沒標 interrupt 的事件要乖乖排隊，不該打斷視窗"

    # 標了但時間還沒到 -> 不打斷
    $ assert pending_interrupt([store._pi_marked], 9.9, store._pi_ctx) is None, "時間還沒到不該打斷"

    # 標了而且到點 -> 回傳那個事件
    $ assert pending_interrupt([store._pi_marked], 10, store._pi_ctx) is store._pi_marked, "到點就該回傳那個事件"
    $ assert pending_interrupt([store._pi_marked], 999, store._pi_ctx) is store._pi_marked, "過期更要打斷"

    # 已經觸發過而死掉 -> 不打斷。
    # 不排除的話，鬼放完之後這個房間的視窗會永遠一開就被關掉。
    python:
        store._pi_gs_dead = GameState()
        store._pi_gs_dead.events.record_trigger("pi.ghost", 1)
        store._pi_ctx_dead = EventContext(store._pi_gs_dead, store._pi_room)

    $ assert store._pi_gs_dead.events.is_dead("pi.ghost"), "這個測試的前提是事件已經死了"
    $ assert pending_interrupt([store._pi_marked], 999, store._pi_ctx_dead) is None, "死掉的事件不該再打斷視窗"

    # 條件不成立 -> 不打斷。
    #
    # 這條很重要：「視窗關掉了、結果什麼都沒發生」比「視窗沒關」糟得多，
    # 玩家會覺得視窗莫名其妙自己關掉。所以條件也要先算過。
    $ assert pending_interrupt([store._pi_gated], 999, store._pi_ctx) is None, "條件不成立時不該打斷 (不然視窗關了卻什麼都沒發生)"

    $ store._pi_gs.inventory.add("flashlight")
    $ assert pending_interrupt([store._pi_gated], 999, store._pi_ctx) is store._pi_gated, "條件成立之後就該打斷"

    # 好幾個都到點 -> 回傳 sequence 最小的 (最重要的那個)
    python:
        store._pi_early = Event(
            id="pi.early", trigger=TriggerType.TIMER, delay=10,
            interrupt=True, sequence=-5,
        )
        store._pi_late = Event(
            id="pi.late", trigger=TriggerType.TIMER, delay=10,
            interrupt=True, sequence=5,
        )
        store._pi_picked = pending_interrupt(
            [store._pi_late, store._pi_early], 999, store._pi_ctx,
        )

    $ assert store._pi_picked is store._pi_early, f"同時到點要挑 sequence 最小的，實際 {store._pi_picked}"

    # --- 被打斷不算答錯 ---
    #
    # PUZZLE_INTERRUPTED 走的是「認不得的值一律不套用 Effect」那條路，
    # 所以 puzzle_result_effect 不用為它改一行。這條守住那件事。
    python:
        store._pi_puzzle = KeypadPuzzle(
            code="1234",
            on_success=Effect(set_flags=["pi_ok"]),
            on_failure=Effect(actor="player", stats={"hp": -1}),
        )

    $ assert puzzle_result_effect(store._pi_puzzle, PUZZLE_INTERRUPTED) is None, "被鬼打斷不該套用任何 Effect (不是答錯，不該扣血)"
    $ assert puzzle_result_effect(store._pi_puzzle, PUZZLE_CLOSED) is None, "玩家自己關掉也不套用"
    $ assert puzzle_result_effect(store._pi_puzzle, PUZZLE_FAILED) is store._pi_puzzle.on_failure, "真的答錯才套用 on_failure"

    # --- pausable 這個欄位本身 ---
    $ assert KeypadPuzzle(code="1", on_success=Effect(label="x")).pausable is True, "pausable 預設要是 True (世界停下來等玩家)"
    $ assert KeypadPuzzle(code="1", on_success=Effect(label="x"), pausable=False).pausable is False, "填了 False 就要是 False"
    $ assert puzzle_def("playground_locker").pausable is False, "實驗區的鎖櫃是 pausable=False 的示範"
    $ assert puzzle_def("kitchen_safe").pausable is True, "廚房保險箱維持預設的會暫停"


# 真的讓鬼來把解謎視窗關掉，走一遍完整流程。
#
# 守住四件事：
#   1. pausable=False 的關卡開著時，世界時鐘**在走**
#   2. 沒標 interrupt 的計時事件到點時**不會**關掉視窗（乖乖排隊）
#   3. 標了 interrupt 的事件到點時視窗**當場關掉**
#   4. 被關掉**不算答錯** —— 不扣血，而那個事件確實發生了
testcase interrupt_flow:

    # 要真的等時間過去，所以預算開大一點。
    $ __import__("renpy").test.testsettings._test.timeout = 90.0
    $ _trace_reset()

    click "開始"
    advance until "前往實驗區(測試區)"
    click "前往實驗區(測試區)"
    advance until "🗃 鎖櫃"
    $ _trace("1_到了實驗區")

    # 把 demo 的秒數改短，不然這個測試要等 20 秒。
    #
    # 改的是靜態定義（Room 的 Event），跟 rollback_through_modals 改
    # puzzle_def 的 on_failure 是同一種做法。這個行程結束就沒了，
    # 而且「重新載入房間資料」會重建，不會污染其他測試。
    #
    # 腳步聲（沒標 interrupt）排在 1.5 秒，鬼（標了）排在 4 秒 ——
    # 順序刻意是「先讓不該打斷的那個到點」，這樣第 2 點才驗得到。
    #
    # ⚠️ 這裡刻意在**進房之後**才改，而且改完要緊接著 click。
    #
    # explore_loop 進房時就照當下的秒數設好鬧鐘睡下去了，所以改秒數本身
    # 不會讓它醒來 —— 是底下那個 click "🗃 鎖櫃" 打斷了 pause，迴圈
    # 回來才重算。這正好是這個 testcase 要的：1.5 秒的死線要在
    # 解謎視窗**開著的時候**過去。
    #
    # 進房之前就改的話，腳步聲會在玩家還沒點鎖櫃時就先發生，
    # 第 2 點就測不到了。（ghost_approach_flow 是相反的情況，那邊
    # 什麼都不點，所以一定要在進房之前改）
    python:
        for _e in rooms["playground"].events:
            if _e.id == "playground.timer_demo":
                _e.delay = 1.5
            elif _e.id == "playground.ghost_arrives":
                _e.delay = 4

        # 暫時讓答錯會扣血。
        #
        # 鎖櫃原本答錯不扣血（壓力來自時間），但那會讓底下那條
        # 「被打斷不該扣血」變成空話 —— 不管有沒有被當成答錯，
        # 血都不會變。換成會扣血的版本，這條斷言才真的在守東西。
        # （做破壞驗證時發現的：把 PUZZLE_INTERRUPTED 當成答錯，
        #   原本只有純函式測試會叫，這個流程測試不會）
        puzzle_def("playground_locker").on_failure = Effect(
            actor="player",
            stats={"hp": -1},
            label="playground_locker_wrong",
        )

        # 把嚇人視窗拉長到 4 秒。
        #
        # 預設是 1.2 秒，而「鬼被派發」與「圖還在畫面上」之間的空檔
        # 只有 0.2 秒左右（explore_loop 設鬧鐘的下限）——
        # 用預設長度的話，測試要在 1.2 秒的窗口裡剛好量到，看運氣。
        # (第一次就是這樣失敗的：事件派發了，但圖已經演完關掉了)
        #
        # 拉長的是「演出時間」，不是被測的邏輯。
        JUMPSCARE_DURATION = 4.0

        # 這個 testcase 測的是撲到全螢幕那一種演出，所以明寫。
        # demo 的預設值會換（兩種演出都做了），不該讓測試跟著飄。
        PLAYGROUND_GHOST_STYLE = "jumpscare"

        _rb.int_hp_before = game_state.actors.get("player", "hp")

    click "🗃 鎖櫃"
    pause 0.5

    $ assert renpy.get_screen("keypad_puzzle") is not None, "點鎖櫃應該打開密碼鎖"
    $ _trace("2_密碼鎖打開了")

    # 第 1 點：pausable=False -> 世界時鐘在走。
    #
    # 關卡是從熱點的 label 叫出來的，而那些 label 由 run_event_labels
    # 執行，那裡為了對話已經把時鐘暫停了 —— 所以這裡會是「沒暫停」
    # 唯一的理由就是 run_puzzle 看到 pausable=False 而主動讓開。
    $ assert not world.paused, f"pausable=False 的關卡開著時時鐘不該暫停，實際暫停理由 {world.pause_reasons}"

    python:
        _rb.int_elapsed_at_open = world.elapsed

    # 等到「腳步聲」那個事件該到點了（1.5 秒），但它沒標 interrupt。
    pause 2.5

    # 第 2 點：沒標 interrupt 的事件不該關掉視窗。
    #
    # 這條是整個設計的重點 —— 氣氛台詞不該把玩家從密碼鎖裡拽出來，
    # 還害他按到一半的號碼全沒了。
    $ assert renpy.get_screen("keypad_puzzle") is not None, "沒標 interrupt 的計時事件到點時不該關掉視窗 (它該乖乖排隊)"
    $ assert world.elapsed > _rb.int_elapsed_at_open, f"解謎期間時鐘要繼續走，開窗時 {_rb.int_elapsed_at_open}、現在 {world.elapsed}"
    $ _trace("3_腳步聲到點但視窗還開著")

    # 再等到鬼到點（4 秒）。
    pause 2.5

    # 第 3 點：標了 interrupt 的事件要把視窗當場關掉。
    $ assert renpy.get_screen("keypad_puzzle") is None, "標了 interrupt 的事件到點時應該把視窗關掉"
    $ _trace("4_鬼到了，視窗被關掉")

    # 被打斷不算答錯 —— 量在「視窗剛關掉」這一刻。
    #
    # 不能等到最後才量：鬼的事件自己會扣 3 滴血，那是它應得的代價，
    # 跟「被打斷算不算答錯」是兩回事。混在一起量就分不出來了。
    python:
        _rb.int_hp_at_close = game_state.actors.get("player", "hp")

    $ assert _rb.int_hp_at_close == _rb.int_hp_before, f"被鬼打斷不是答錯，視窗關掉的當下不該扣血。之前 {_rb.int_hp_before}、現在 {_rb.int_hp_at_close}"
    $ assert not game_state.flags.has("playground_locker_opened"), "被打斷更不該算答對"

    # 視窗關掉之後執行權回到 explore_loop，它下一圈開始派發到點的事件。
    #
    # ⚠️ 第一個被派發的是**腳步聲**，不是鬼 —— 兩個都到點了，而
    # due_timer_events 按 sequence 排序 (腳步聲 0、鬼 10)，
    # collect_events 又是 max_fires=1，所以這一圈只放腳步聲。
    # 鬼要等腳步聲的對話演完、下一圈才輪到它。
    #
    # (這裡原本寫成「關窗後鬼馬上發生」，跑出來次數是 0 才發現 ——
    #  程式是對的，是我沒照著排序算一遍)
    pause 1.5

    # 腳步聲確實排隊排到了，沒有因為視窗擋著就消失。
    $ assert game_state.events.count_of("playground.timer_demo") == 1, f"沒標 interrupt 的事件應該在視窗關掉後排隊發生，實際次數 {game_state.events.count_of('playground.timer_demo')}"
    $ _trace("5_腳步聲排隊到了")

    # 推完腳步聲的對話，explore 回來之後才輪到鬼。
    advance until "🗃 鎖櫃"

    # 0.6 秒足夠讓 explore_loop 派發 (下限 0.2 秒)，
    # 而嚇人視窗被拉長到 4 秒，所以這時候圖一定還在。
    pause 0.6

    # 第 4 點：事件真的發生了。
    #
    # 次數是 collect_events 在跑對話之前就記的，所以不管鬼的台詞
    # 有沒有被推完，這條都成立。
    $ assert game_state.events.count_of("playground.ghost_arrives") == 1, f"視窗關掉之後那個事件應該真的發生，實際次數 {game_state.events.count_of('playground.ghost_arrives')}"
    $ _trace("6_鬼的事件被派發了")

    # --- 第 5 點：嚇人視窗跳出來，自己關掉，然後才扣血 ---
    #
    # 順序是重點。扣血刻意寫在 label 裡而不是 Event 的 Effect 上，
    # 因為引擎是「先套用 Effect、再跑它帶的 label」—— 掛在 Effect 上
    # 的話左上角的 ❤️ 會在圖跳出來**之前**就少掉，玩家先看到自己掉血、
    # 才看到為什麼。
    $ assert renpy.get_screen("jumpscare") is not None, "鬼的事件應該跳出嚇人視窗"
    $ assert game_state.actors.get("player", "hp") == _rb.int_hp_before, f"圖還在的時候就不該扣血 (那樣玩家會先看到掉血才看到原因)。現在 {game_state.actors.get('player', 'hp')}"
    $ _trace("7_嚇人視窗跳出來了，還沒扣血")

    # 等它自己關掉。刻意沒有關閉鈕也不吃點擊，所以只能等。
    pause 4.5

    $ assert renpy.get_screen("jumpscare") is None, "嚇人視窗應該自己關掉 (timer 到就 Return)"
    $ assert game_state.actors.get("player", "hp") == _rb.int_hp_before - 3, f"視窗關掉之後才扣 3 滴血。之前 {_rb.int_hp_before}、現在 {game_state.actors.get('player', 'hp')}"
    $ _trace("8_視窗自己關掉，扣了 3 滴血")


# 近景視窗被鬼打斷。
#
# 近景沒有 pausable 這種選項 —— 它永遠是「時鐘在走」的，所以永遠
# 可以被打斷。翻抽屜本來就不該是安全的。
#
# 最重要的一條是「被打斷之後**不可以**再把框打開」：
# open_closeup 是一個 while 迴圈，正常情況下跑完事件就會把框放回來。
# 被鬼打斷時那個行為必須停掉，不然玩家會被關在抽屜裡出不來。
testcase closeup_interrupt_flow:

    $ __import__("renpy").test.testsettings._test.timeout = 90.0
    $ _trace_reset()

    click "開始"
    advance until "前往實驗區(測試區)"
    click "前往實驗區(測試區)"
    advance until "🗄 抽屜"
    $ _trace("1_到了實驗區")

    # 腳步聲殺掉（這個測試只關心會打斷的那個），鬼的秒數改短。
    python:
        game_state.events.kill("playground.timer_demo")

        for _e in rooms["playground"].events:
            if _e.id == "playground.ghost_arrives":
                _e.delay = 3

    click "🗄 抽屜"
    advance until "🖼 撕成兩半的照片"

    $ assert renpy.get_screen("closeup") is not None, "點抽屜應該打開近景視窗"
    $ assert not world.paused, f"近景期間時鐘不該暫停，實際 {world.pause_reasons}"
    $ _trace("2_框打開了，時鐘在走")

    # 什麼都不要點，等鬼來。
    pause 4.0

    $ assert renpy.get_screen("closeup") is None, "鬼到了應該把近景視窗關掉"
    $ _trace("3_鬼到了，框被關掉")

    # 關鍵：框**不可以**再打開。
    #
    # 正常的近景迴圈是「跑完事件就把框放回來」，被打斷時那條路必須停掉。
    # 等得比事件派發的時間長一點再看，確定它不是晚一點才跳出來。
    pause 2.0

    $ assert renpy.get_screen("closeup") is None, "被鬼打斷之後絕對不可以再把框打開 (不然玩家被關在抽屜裡出不來)"
    $ _trace("4_框沒有再打開")

    # 這裡**不**斷言「那個事件已經發生」。
    #
    # 框關掉之後 playground_open_drawer 還有一句「你把抽屜推回去。」
    # 在等玩家，而對話期間時鐘是暫停的、explore_loop 也還沒跑到 ——
    # 所以事件要等玩家讀完那句話才會出場。這是對的行為。
    # （我原本寫了 count == 1，跑出來是 0 才發現；程式沒錯，是我沒算到
    #   demo 的收尾台詞還卡在前面）
    #
    # 而那句話沒辦法在測試裡推掉（理由見 closeup_flow 裡的那段說明：
    # advance until 會短路、裸 advance 會等一句不存在的下一句）。
    # 「被打斷之後事件確實會派發」由 interrupt_flow 守著 ——
    # 那個關卡的 label 在 run_puzzle 之後沒有收尾台詞，所以直接回到
    # explore_loop。這個 testcase 的獨特價值是上面那兩條「框關掉、
    # 而且沒有再打開」。

    # 被打斷不該算「拿到了照片」—— 玩家根本還沒點它
    $ assert not game_state.inventory.has("torn_photo"), "被打斷不該憑空拿到近景裡的東西"
    $ _trace("5_沒有憑空拿到東西")


# 第二種演出：鬼從左邊慢慢走到右邊的主角身上（對話模式）。
#
# 這一段完全是普通的 Ren'Py（show / at / with / 對話），沒有用到工具包的
# 任何新元件。所以這個 testcase 要守的不是「元件有沒有壞」，而是兩件
# 內容層很容易寫錯、而且錯了會很難看的事：
#
#   1. 演完有沒有把立繪收掉 —— 忘記 hide 的話一隻巨大的 👻 會從此
#      黏在探索畫面上，而且後面每個房間都跟著
#   2. 血是不是在演出**之後**才扣的
testcase ghost_approach_flow:

    $ __import__("renpy").test.testsettings._test.timeout = 60.0
    $ _trace_reset()

    click "開始"
    advance until "前往實驗區(測試區)"

    # 明寫要測哪一種演出，不要靠 demo 的預設值
    $ PLAYGROUND_GHOST_STYLE = "approach"

    # ⚠️ 秒數一定要在**進房之前**改。
    #
    # explore_loop 是進房之後照當下的秒數設一次鬧鐘然後睡下去的
    # (renpy.pause(還剩幾秒))。進房之後才改成 2 秒的話，它還在睡
    # 原本那個 20 秒的鬧鐘，根本不會醒來。
    #
    # interrupt_flow 那邊是進房之後才改的，能過是因為緊接著
    # click "🗃 鎖櫃" —— 點熱點會打斷 pause，迴圈回來就重算了。
    # 這個 testcase 什麼都不點，所以沒有那個運氣。
    # (第一版就是這樣失敗的：等了 3.5 秒，次數還是 0)
    python:
        # 腳步聲殺掉（這個測試只關心鬼），鬼的秒數改短
        game_state.events.kill("playground.timer_demo")

        for _e in rooms["playground"].events:
            if _e.id == "playground.ghost_arrives":
                _e.delay = 2

        _rb.ga_hp_before = game_state.actors.get("player", "hp")

    click "前往實驗區(測試區)"
    advance until "🗃 鎖櫃"
    $ _trace("1_到了實驗區")

    # 什麼都不做，站著等鬼走過來。
    #
    # 等到演出開始就會**停在第一句對話上**不動（對話要等玩家推進），
    # 所以這裡不用擔心等太久會錯過 —— 跟嚇人視窗那種會自己關掉的不一樣。
    pause 3.5

    $ assert game_state.events.count_of("playground.ghost_arrives") == 1, f"等了 3.5 秒鬼應該到了，實際次數 {game_state.events.count_of('playground.ghost_arrives')}"
    $ assert renpy.showing("pg_player_back"), "演出開始時主角的立繪應該在畫面上"
    $ assert game_state.actors.get("player", "hp") == _rb.ga_hp_before, f"演出還在跑就不該扣血。現在 {game_state.actors.get('player', 'hp')}"
    $ _trace("2_演出開始了，立繪在、還沒扣血")

    # 把整段演出推完，回到探索畫面。
    #
    # 探索畫面在演出期間是收起來的（run_event_labels 會 hide），
    # 所以「🗃 鎖櫃」重新出現就代表整串對話真的推完了。
    advance until "🗃 鎖櫃"
    $ _trace("3_演出推完回到探索")

    # 第 1 件：立繪一定要收乾淨。
    $ assert not renpy.showing("pg_ghost"), "演完要把鬼的立繪收掉 (不然它會黏在探索畫面上)"
    $ assert not renpy.showing("pg_player_back"), "演完要把主角的立繪收掉"

    # 第 2 件：演完才扣血。
    $ assert game_state.actors.get("player", "hp") == _rb.ga_hp_before - 3, f"演完要扣 3 滴血。之前 {_rb.ga_hp_before}、現在 {game_state.actors.get('player', 'hp')}"
    $ _trace("4_立繪收乾淨了，血也扣了")

    # 兩種演出共用同一個代價 —— 換演出方式不該改到扣幾滴血。
    # (扣血寫在分支外面就是為了這件事)
    $ assert renpy.get_screen("explore") is not None, "演完要回到探索畫面"
