##################################################
# tests.rpy —— 《最後一班》第 3 步的自動化測試
#
#   執行方式（在 SDK 目錄下）：
#       renpy.exe <專案路徑> test last_shift_step3
#
#   testcase 只在 test 模式下執行，正常玩遊戲不受影響。
#
#   測的是「狀態」不是「畫面」：直接拿真正的房間定義，用 collect_events
#   派發點擊／進房事件，檢查回傳的 label 與 GameState 的變化。
#   不跑 label、不點畫面，所以改台詞或改熱點座標都不用改測試。
##################################################

init python:

    def _ls_fresh_state():
        """
        換一個全新的 GameState，照 label start 的方式寫入初始數值。
        回傳舊的那份，測完要放回去。
        """
        old = store.game_state
        store.game_state = GameState()
        init_actor_stats_from_catalog()
        return old

    def _ls_click(room_name, hotspot_name):
        """模擬點一下熱點，回傳要跑的 label 清單 (和 _fire_hotspot 同一套流程)。"""
        room = rooms[room_name]
        hs = room.get_hotspot(hotspot_name)
        assert hs is not None, f"{room_name} 找不到熱點 {hotspot_name}"

        labels = collect_events(
            hs.events,
            TriggerType.CLICK_HOTSPOT,
            EventContext(store.game_state, room),
            TriggerType.CLICK_HOTSPOT,
        )
        if hs.on_click:
            labels.append(hs.on_click)
        return labels

    def _ls_enter(room_name):
        """模擬進房 (只派發 ENTER_ROOM，不換畫面)，回傳要跑的 label 清單。"""
        room = rooms[room_name]
        return collect_events(
            room.events,
            TriggerType.ENTER_ROOM,
            EventContext(store.game_state, room),
            TriggerType.ENTER_ROOM,
        )

    def _ls_shown(room_name, hotspot_name):
        return hotspot_is_shown(rooms[room_name].get_hotspot(hotspot_name))

    def _ls_battery():
        return store.game_state.actors.get("player", "battery")

    def _ls_has_battery_stat():
        return store.game_state.actors.has_stat("player", "battery")


testcase last_shift_step3:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _ls_old_state = _ls_fresh_state()

    # --- 開場 ---
    $ assert game_state.actors.get("player", "hp") == 5, "開場 hp 應該是 5"
    $ assert not _ls_has_battery_stat(), "開場不該有 battery (狀態欄才不會出現 🔦 0)"

    # 還沒拿手電筒時換房間不扣電，也不會憑空生出 battery
    $ _ls_enter("corridor")
    $ _ls_enter("living_room")
    $ assert not _ls_has_battery_stat(), "沒有手電筒時進房不該扣電"

    # 補充電池的熱點要拿到手電筒才看得到
    $ assert not _ls_shown("living_room", "flashlight_charge"), "沒手電筒時不該看到補充電池"

    # 沒電 (還沒拿手電筒) 爬不進老鼠洞
    $ _labels = _ls_click("corridor", "hole_sister")
    $ assert _labels == ["cantgo_sister_room_dark"], f"沒光時應該進不去，實際 {_labels}"

    # --- 配電箱：沒鑰匙 → 鎖住，而且每次都講 ---
    $ _labels = _ls_click("living_room", "distribution_box")
    $ assert _labels == ["distribution_box_lock"], f"沒鑰匙應該講鎖住，實際 {_labels}"
    $ _labels = _ls_click("living_room", "distribution_box")
    $ assert _labels == ["distribution_box_lock"], f"第二次點也要講鎖住，實際 {_labels}"

    # --- 抽屜：拿到鑰匙與紙條 (第 5 步起改成近景，細節見 last_shift_step5) ---
    $ _ls_click("drawer_inside", "key")
    $ _ls_click("drawer_inside", "note")
    $ assert game_state.inventory.count_of("drawer_key") == 1
    $ assert game_state.inventory.count_of("note") == 1
    $ assert game_state.inventory.count_of("photo") == 0, "第 4 步起相片改放保險箱，抽屜不該給"

    # --- 配電箱：有鑰匙 → 手電筒 + 電池，只給一次 ---
    $ _labels = _ls_click("living_room", "distribution_box")
    $ assert _labels == ["found_flashlight_spare_battery"], f"有鑰匙應該打開，而且不能接著講鎖住，實際 {_labels}"
    $ assert game_state.inventory.count_of("flashlight") == 1
    $ _spares = game_state.inventory.count_of("spare_battery")
    $ assert _spares > 0, "應該拿到備用電池"
    $ assert _ls_battery() == 5, f"拿到手電筒電量應該是 5，實際 {_ls_battery()}"

    $ _labels = _ls_click("living_room", "distribution_box")
    $ assert _labels == ["distribution_box_no_item"], f"打開過應該講空了，實際 {_labels}"
    $ assert game_state.inventory.count_of("flashlight") == 1, "手電筒不能給第二支"
    $ assert _ls_battery() == 5, "再點一次不能再加電"

    # --- 每進一個房間扣 1 ---
    $ _ls_enter("corridor")
    $ assert _ls_battery() == 4, f"進走廊應該剩 4，實際 {_ls_battery()}"
    $ _ls_enter("sister_room")
    $ assert _ls_battery() == 3, f"進妹妹房間應該剩 3，實際 {_ls_battery()}"
    $ _ls_enter("living_room")
    $ assert _ls_battery() == 2, f"進客廳應該剩 2，實際 {_ls_battery()}"

    # 有電時可以爬進老鼠洞，而且不會接著講「太黑了」
    $ _labels = _ls_click("corridor", "hole_sister")
    $ assert _labels == ["go_sister_room"], f"有電時應該進得去，實際 {_labels}"

    # --- 換電池 ---
    $ assert _ls_shown("living_room", "flashlight_charge"), "有手電筒時要看得到補充電池"

    # 還有電：不換
    $ _labels = _ls_click("living_room", "flashlight_charge")
    $ assert _labels == ["battery_even_full"], f"還有電時不該換，實際 {_labels}"
    $ assert game_state.inventory.count_of("spare_battery") == _spares, "沒換就不該扣電池"

    # 扣到 0，而且不會變負數
    $ _ls_enter("corridor")
    $ _ls_enter("corridor")
    $ _ls_enter("corridor")
    $ assert _ls_battery() == 0, f"電量應該夾在 0，實際 {_ls_battery()}"

    # 沒電：進不了老鼠洞
    $ _labels = _ls_click("corridor", "hole_sister")
    $ assert _labels == ["cantgo_sister_room_dark"], f"沒電時應該進不去，實際 {_labels}"

    # 沒電：換一顆，補回 5
    $ _labels = _ls_click("living_room", "flashlight_charge")
    $ assert _labels == ["battery_swapped"], f"沒電時應該換電池，實際 {_labels}"
    $ assert _ls_battery() == 5, f"換完應該是 5，實際 {_ls_battery()}"
    $ assert game_state.inventory.count_of("spare_battery") == _spares - 1, "換電池要扣一顆"

    # 備用電池用完、手電筒還有電：講「省著點用」，不是「只能重玩」
    $ game_state.inventory.remove("spare_battery", game_state.inventory.count_of("spare_battery"))
    $ _labels = _ls_click("living_room", "flashlight_charge")
    $ assert _labels == ["battery_no_spare"], f"還有電但沒備用電池，實際 {_labels}"

    # 備用電池用完、手電筒也沒電
    $ game_state.actors.set("player", "battery", 0)
    $ _labels = _ls_click("living_room", "flashlight_charge")
    $ assert _labels == ["no_battery"], f"完全沒電，實際 {_labels}"

    # --- 保險箱不會把人傳回走廊 ---
    $ _labels = _ls_click("living_room", "safe")
    $ assert "living_room_go_corridor" not in _labels, f"點保險箱不該換房間，實際 {_labels}"

    # --- 靜態檢查：熱點名稱與事件 id 不能重複 ---
    python:
        _seen_ids = {}
        for _rn, _r in rooms.items():
            _names = [h.name for h in _r.hotspots]
            assert len(_names) == len(set(_names)), f"{_rn} 有重複的熱點名稱：{_names}"

            _all = list(_r.events)
            for _h in _r.hotspots:
                _all += list(_h.events)
            for _e in _all:
                assert _e.id not in _seen_ids, f"事件 id 重複：{_e.id} ({_seen_ids.get(_e.id)} 與 {_rn})"
                _seen_ids[_e.id] = _rn

    # 放回原本的狀態
    $ store.game_state = _ls_old_state


##################################################
# 第 4 步：兩個解謎
#
#   執行方式：renpy.exe <專案路徑> test last_shift_step4
#
#   不開關卡畫面 —— 直接拿 puzzle_result_effect 餵三種結果，
#   跟 run_puzzle 套用 Effect 是同一個函式。
##################################################

init python:

    def _ls_puzzle(key, result):
        """模擬關卡結束，回傳要跑的 label (沒有就是 None)。"""
        p = puzzle_def(key)
        assert p is not None, f"找不到關卡 {key}"
        eff = puzzle_result_effect(p, result)
        return eff.apply(store.game_state) if eff is not None else None

    def _ls_missing_labels():
        """房間、熱點、事件、關卡裡寫到的 label，回傳找不到的那些。"""
        missing = []

        def need(where, name):
            if name and not renpy.has_label(name):
                missing.append(f"{where} → {name}")

        for rn, r in rooms.items():
            need(f"{rn}.on_enter", r.on_enter)
            evs = list(r.events)
            for h in r.hotspots:
                need(f"{rn}.{h.name}.on_click", h.on_click)
                evs += list(h.events)
            for e in evs:
                need(e.id, e.effect.label if e.effect else None)

        for pk, p in puzzle_catalog.items():
            for kind, eff in (("on_success", p.on_success), ("on_failure", p.on_failure)):
                need(f"puzzle {pk}.{kind}", eff.label if eff else None)

        return missing


testcase last_shift_step4:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _ls_old_state = _ls_fresh_state()

    # --- 保險箱 ---
    $ assert _ls_shown("living_room", "safe"), "一開始要看得到保險箱"
    $ _labels = _ls_click("living_room", "safe")
    $ assert _labels == ["living_room_safe_locked"], f"點保險箱應該開密碼鎖，實際 {_labels}"
    $ assert puzzle_def("safe").code == "4721", "保險箱密碼應該跟紙條一樣"
    $ assert "4721" in item_def("note").description, "紙條上要寫著密碼"
    $ assert puzzle_def("safe").pausable is False, "保險箱解的時候世界不停"

    # 按 ✕：什麼都不做
    $ _hp = game_state.actors.get("player", "hp")
    $ assert _ls_puzzle("safe", PUZZLE_CLOSED) is None
    $ assert game_state.actors.get("player", "hp") == _hp, "關掉不該扣血"
    $ assert not game_state.inventory.has("photo")

    # 答錯：扣 1 滴血，講話
    $ _label = _ls_puzzle("safe", PUZZLE_FAILED)
    $ assert _label == "living_room_safe_shock", f"答錯的 label，實際 {_label}"
    $ assert game_state.actors.get("player", "hp") == _hp - 1, "答錯要扣 1 滴血"
    $ assert not game_state.inventory.has("photo"), "答錯不該拿到相片"
    $ assert _ls_shown("living_room", "safe"), "答錯保險箱還在"

    # 答對：拿到相片，保險箱消失
    $ _label = _ls_puzzle("safe", PUZZLE_SOLVED)
    $ assert _label == "living_room_safe_opens", f"答對的 label，實際 {_label}"
    $ assert game_state.inventory.count_of("photo") == 1, "答對要拿到一張相片"
    $ assert game_state.flags.has("safe_opened")
    $ assert not _ls_shown("living_room", "safe"), "打開過保險箱熱點應該消失"
    $ assert item_def("photo").icon, "相片要有圖，說明視窗才看得到刮痕"

    # --- 舊手機 ---
    $ assert _ls_shown("sister_room", "sister_phone"), "一開始要看得到手機"
    $ _labels = _ls_click("sister_room", "sister_phone")
    $ assert _labels == ["sister_room_old_phone"], f"點手機應該開圖形鎖，實際 {_labels}"

    $ _p = puzzle_def("sister_phone")
    $ assert _p.pattern == [1, 5, 9], f"手機圖形應該是 159，實際 {_p.pattern}"
    $ assert len(_p.pattern) >= _p.min_length, "圖形比 min_length 短會永遠解不開"

    # 玩家直接從 1 拖到 9，中間的 5 自動連上 —— 一樣算對
    $ assert pattern_extend([1], 9) == [1, 5, 9], "1 拖到 9 應該自動經過 5"

    $ _hp = game_state.actors.get("player", "hp")
    $ assert _ls_puzzle("sister_phone", PUZZLE_CLOSED) is None
    $ _label = _ls_puzzle("sister_phone", PUZZLE_FAILED)
    $ assert _label == "sister_phone_wrong", f"畫錯的 label，實際 {_label}"
    $ assert game_state.actors.get("player", "hp") == _hp, "畫錯不扣血"
    $ assert _ls_shown("sister_room", "sister_phone"), "畫錯手機還在"

    $ _label = _ls_puzzle("sister_phone", PUZZLE_SOLVED)
    $ assert _label == "sister_phone_unlocked", f"解開的 label，實際 {_label}"
    $ assert game_state.flags.has("sister_phone_unlocked")
    $ assert not _ls_shown("sister_room", "sister_phone"), "解開後手機熱點應該消失"

    # --- 靜態檢查：所有會被跑到的 label 都存在 ---
    #
    # label 打錯不會在啟動時報錯，要等玩家真的點到才會跳 LabelNotFound。
    $ _missing = _ls_missing_labels()
    $ assert not _missing, "找不到這些 label：\n" + "\n".join(_missing)

    $ store.game_state = _ls_old_state


##################################################
# 第 5 步：近景抽屜
#
#   執行方式：renpy.exe <專案路徑> test last_shift_step5
##################################################

init python:

    def _ls_hotspot_box_problems(room_name):
        """
        近景裡的圖片熱點：有沒有超出框、圖的比例有沒有被拉歪。
        回傳問題清單，沒問題就是空的。
        """
        room = rooms[room_name]
        problems = []
        for h in room.hotspots:
            if h.x < 0 or h.y < 0 or h.x + h.width > room.bg_width or h.y + h.height > room.bg_height:
                problems.append(f"{h.name} 超出框 ({h.x}, {h.y}, {h.width}×{h.height})")

            if h.idle:
                if not renpy.loadable(h.idle):
                    problems.append(f"{h.name} 的圖 {h.idle} 不存在")
                    continue
                iw, ih = renpy.image_size(h.idle)
                # 寬高比差 2% 以內算一樣
                if abs((h.width / h.height) / (iw / ih) - 1) > 0.02:
                    problems.append(f"{h.name} 被拉歪：原圖 {iw}×{ih}，熱點 {h.width}×{h.height}")
        return problems


testcase last_shift_step5:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _ls_old_state = _ls_fresh_state()

    # --- 近景本身 ---
    $ _cu = rooms["drawer_inside"]
    $ assert _cu.bg_height == 720 and _cu.bg_width == 1280, "近景框應該是 1280×720"
    $ _problems = _ls_hotspot_box_problems("drawer_inside")
    $ assert not _problems, "\n".join(_problems)

    # --- 客廳的抽屜開近景，不再直接給東西 ---
    $ _labels = _ls_click("living_room", "drawer")
    $ assert _labels == ["open_drawer"], f"點抽屜應該只開近景，實際 {_labels}"
    $ assert not game_state.inventory.has("drawer_key"), "點抽屜不該直接拿到鑰匙"
    $ assert not game_state.inventory.has("note"), "點抽屜不該直接拿到紙條"

    # --- 先拿紙條：鑰匙還在 ---
    $ assert _ls_shown("drawer_inside", "note") and _ls_shown("drawer_inside", "key")
    $ _labels = _ls_click("drawer_inside", "note")
    $ assert _labels == ["drawer_inside_take_note"], f"拿紙條的 label，實際 {_labels}"
    $ assert game_state.inventory.count_of("note") == 1
    $ assert not _ls_shown("drawer_inside", "note"), "拿過紙條就該消失"
    $ assert _ls_shown("drawer_inside", "key"), "只拿了紙條，鑰匙還要在"
    $ assert not game_state.inventory.has("drawer_key")

    # 鑰匙還沒拿，配電箱還是鎖著
    $ _labels = _ls_click("living_room", "distribution_box")
    $ assert _labels == ["distribution_box_lock"], f"沒鑰匙配電箱應該鎖著，實際 {_labels}"

    # --- 再拿鑰匙 ---
    $ _labels = _ls_click("drawer_inside", "key")
    $ assert _labels == ["drawer_inside_take_key"], f"拿鑰匙的 label，實際 {_labels}"
    $ assert game_state.inventory.count_of("drawer_key") == 1
    $ assert not _ls_shown("drawer_inside", "key"), "拿過鑰匙就該消失"

    # 兩樣都拿完：抽屜還能打開 (看空抽屜)，東西不會重複給
    $ assert _ls_shown("living_room", "drawer"), "拿完之後抽屜還在"
    $ _ls_click("living_room", "drawer")
    $ assert game_state.inventory.count_of("note") == 1
    $ assert game_state.inventory.count_of("drawer_key") == 1

    # 第 3 步的流程沒壞：有鑰匙就打得開配電箱
    $ _labels = _ls_click("living_room", "distribution_box")
    $ assert _labels == ["found_flashlight_spare_battery"], f"有鑰匙應該打開配電箱，實際 {_labels}"

    # --- 反過來的順序：先拿鑰匙也可以 ---
    $ _ls_fresh_state()
    $ _ls_click("drawer_inside", "key")
    $ assert game_state.inventory.has("drawer_key") and not game_state.inventory.has("note")
    $ assert _ls_shown("drawer_inside", "note"), "只拿了鑰匙，紙條還要在"
    $ _ls_click("drawer_inside", "note")
    $ assert game_state.inventory.has("note")

    # label 存在性 (新加的近景也一起查)
    $ _missing = _ls_missing_labels()
    $ assert not _missing, "找不到這些 label：\n" + "\n".join(_missing)

    $ store.game_state = _ls_old_state


##################################################
# 第 6 步：結局
#
#   執行方式：renpy.exe <專案路徑> test last_shift_step6
#
#   計時事件不等真的時間 —— 直接拿「在房間待了幾秒」去問
#   due_timer_events，跟探索主迴圈 (room_manager.rpy) 同一套派發。
##################################################

init python:

    def _ls_tick(room_name, seconds):
        """模擬在房間待了 seconds 秒，回傳這一輪計時事件要跑的 label。"""
        room = rooms[room_name]
        due = due_timer_events(room.events, seconds)
        return collect_events(
            due,
            TriggerType.TIMER,
            EventContext(store.game_state, room),
            TriggerType.TIMER,
            max_fires=1,
        )

    def _ls_hp():
        return store.game_state.actors.get("player", "hp")


testcase last_shift_step6:

    $ __import__("renpy").test.testsettings._test.timeout = 30.0
    $ _ls_old_state = _ls_fresh_state()

    # --- 素材與角色 ---
    $ assert renpy.has_image("sister_scare"), "妹妹的嚇人圖沒有宣告"
    $ assert renpy.has_image("father_stand"), "爸爸的立繪沒有宣告"
    $ assert "sister" in actor_catalog and "father" in actor_catalog, "妹妹與爸爸要加進角色目錄"
    $ assert player_death_label() is None, "活著的時候不該有死亡 label"

    # --- 回電之前：什麼都不會發生，而且事件不會被用掉 ---
    $ assert "sister_phone_unlocked_hear_something" not in _ls_enter("corridor"), "還沒回電不該聽到聲音"
    $ assert _ls_tick("living_room", 30) == [], "還沒回電，在客廳待多久妹妹都不該出現"
    $ assert game_state.events.count_of("living_room.sister_appears") == 0
    $ assert not game_state.events.is_dead("living_room.sister_appears"), "條件不符不該把妹妹的事件用掉"

    # --- 回電 ---
    $ _ls_puzzle("sister_phone", PUZZLE_SOLVED)

    # 走廊：聽到聲音，只講一次
    $ _labels = _ls_enter("corridor")
    $ assert "sister_phone_unlocked_hear_something" in _labels, f"回電後進走廊要聽到聲音，實際 {_labels}"
    $ assert "sister_phone_unlocked_hear_something" not in _ls_enter("corridor"), "聲音只講一次"
    $ assert _ls_tick("corridor", 30) == [], "妹妹警告之前，走廊不該扣血"

    # 客廳：第 5 秒妹妹出現
    $ assert _ls_tick("living_room", 4.9) == [], "還沒到 5 秒"
    $ _labels = _ls_tick("living_room", 5)
    $ assert _labels == ["sister_appears"], f"第 5 秒妹妹要出現，實際 {_labels}"
    $ assert game_state.flags.has("sister_warned")

    # --- 壞結局：客廳待到 7 秒、走廊待到 2 秒，兩次加起來要死 ---
    $ _hp0 = _ls_hp()
    $ _spare0 = game_state.inventory.count_of("spare_battery")
    $ assert _ls_tick("living_room", 6.9) == [], "妹妹講完後要給玩家 2 秒"
    $ _labels = _ls_tick("living_room", 7)
    $ assert _labels == ["demage_by_father"], f"客廳第 7 秒要扣血，實際 {_labels}"
    $ assert _ls_hp() == _hp0 - 2, f"客廳扣 2，實際 {_hp0} → {_ls_hp()}"
    $ assert game_state.inventory.count_of("spare_battery") == _spare0 + 1, "客廳那一下要補一顆電池，避免卡死"
    $ assert _ls_tick("living_room", 30) == [], "客廳的追逐只有一次"

    $ assert _ls_tick("corridor", 1.9) == []
    $ _labels = _ls_tick("corridor", 2)
    $ assert _labels == ["demage_by_father"], f"走廊第 2 秒要扣血，實際 {_labels}"
    $ assert _ls_hp() == _hp0 - 5, f"走廊扣 3，實際 {_ls_hp()}"

    # 開場 hp 5，兩下扣 5 —— 保險箱一次都沒答錯也會死，壞結局一定到得了
    $ assert _hp0 == 5
    $ assert game_state.actors.is_dead("player"), "hp 歸零要算死亡"
    $ assert player_death_label() == "game_over", f"死亡要跳 game_over，實際 {player_death_label()}"
    $ assert renpy.has_label("game_over")

    # --- 真結局：被警告後直接逃進妹妹房間，剩下的追逐全部取消 ---
    $ _ls_fresh_state()
    $ _ls_puzzle("sister_phone", PUZZLE_SOLVED)
    $ assert _ls_enter("sister_room").count("true_ending") == 0, "還沒被警告，進妹妹房間不該是結局"
    $ _ls_tick("living_room", 5)
    $ _labels = _ls_enter("sister_room")
    $ assert "true_ending" in _labels, f"被警告後進妹妹房間要進結局，實際 {_labels}"
    $ assert game_state.events.is_dead("living_room.chase"), "結局要取消客廳的追逐"
    $ assert game_state.events.is_dead("corridor.chase"), "結局要取消走廊的追逐"
    $ _hp0 = _ls_hp()
    $ assert _ls_tick("living_room", 30) == [] and _ls_tick("corridor", 30) == [], "取消之後不該再扣血"
    $ assert _ls_hp() == _hp0

    # label 存在性
    $ _missing = _ls_missing_labels()
    $ assert not _missing, "找不到這些 label：\n" + "\n".join(_missing)

    $ store.game_state = _ls_old_state
