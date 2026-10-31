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

    # --- 抽屜：拿到三樣東西，之後熱點消失 ---
    $ assert _ls_shown("living_room", "drawer"), "一開始要看得到抽屜"
    $ _labels = _ls_click("living_room", "drawer")
    $ assert _labels == ["open_drawer", "found_item"], f"抽屜的 label 順序不對，實際 {_labels}"
    $ assert game_state.inventory.count_of("drawer_key") == 1
    $ assert game_state.inventory.count_of("note") == 1
    $ assert game_state.inventory.count_of("photo") == 1
    $ assert not _ls_shown("living_room", "drawer"), "拿完東西抽屜熱點應該消失"

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
