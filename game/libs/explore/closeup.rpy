##################################################
# closeup.rpy
#
#   近景視窗：一個浮在房間上的框，框裡面可以點。
#
#   玩家點抽屜 -> 跳出一個框顯示抽屜內部 -> 點裡面的紙條撿起來
#   -> 框消失、講話 -> 框回來 (紙條不見了) -> 自己關掉。
#
#   拿來做「拉近看一次」的東西：撿小物、嚇人、看細節。
#   就像一支放大鏡。
#
#   ---
#
#   用法
#
#   1. 近景內部就是一個普通的 Room，跟其他房間一樣註冊在 rooms 裡：
#
#          rooms["drawer_inside"] = Room(
#              name="drawer_inside",
#              background=state_image(
#                  (Condition(require=["wet_note"]), "images/drawer_empty.png"),
#                  default="images/drawer_note.png",
#              ),
#              bg_width=1280, bg_height=720,     # 框的大小，兩個都要填
#              hotspots=[
#                  Hotspot(name="note", x=300, y=400, label="📄 濕紙條",
#                          condition=Condition(forbid=["wet_note"]),
#                          events=[Event(id="drawer.take_note",
#                                        effect=Effect(give_items=["wet_note"],
#                                                      label="drawer_take_note"))]),
#              ],
#          )
#
#   2. 房間裡的抽屜熱點呼叫它：
#
#          label hall_open_drawer:
#              call open_closeup("drawer_inside")
#              return
#
#   熱點座標就是「框裡面的座標」—— 背景剛好畫成框的大小，不做任何縮放。
#   (縮放的話熱點座標得跟著換算，那是製造 bug 的最佳方式)
#   所以 F9 標點面板量到的數字不能直接用在近景上，近景的座標要自己算。
#
#   ---
#
#   三件刻意的設計決定 (2026-10-26 與使用者確認)
#
#   1. **點到東西時框會消失，講完話再回來。**
#
#      這不是我們去收它的 —— 是 Ren'Py 的規則：畫面動作只要回傳非 None，
#      當前互動就結束 (見 puzzle.rpy 開頭對 Return() 的說明)。
#      所以玩家點紙條的那一瞬間 call_screen 就返回了，框自己消失。
#
#      這件事讓整個近景變成「只有加法」：對話開始跑的時候畫面上根本
#      沒有這個框，所以 run_event_labels 完全不用知道近景的存在。
#      (原本的計畫是要去改它「收起/放回哪個畫面」的邏輯 ——
#       那是整個事件系統最吃重的地方，每一句對話都從那裡流過去)
#
#   2. **近景裡面不開第二層近景。** 一直往下鑽不如直接開新房間。
#      技術上不會當掉，但 renpy.suspend_rollback 是個全域旗標，
#      嵌套時內層的「解除」會把外層的也解除掉 —— 所以請不要這樣寫。
#
#   3. **近景期間世界時鐘照跑，而且點不到後面的房間。**
#      翻抽屜的時候鬼不會停下來等你 (跟解謎視窗一致，跟翻頁視窗相反)。
#      而框開著時不能換房間，不然「開著抽屜走去別的房間」的狀態很難想。
#
#   ---
#
#   近景房間「不會」變成 current_room
#
#   這點很重要。如果它變成當前房間，change_room() 會重設房間計時
#   (見 room_manager.rpy 的 world.mark_room_entered())，
#   玩家就可以靠一直開抽屜無限躲鬼。
#
#   近景只是「畫出來」而已 —— 玩家身體還在走廊上，鬼照樣在倒數。
##################################################

init python:

    # 近景視窗的回傳值。玩家關掉視窗時回傳這個，
    # 點到熱點時回傳「那個 Hotspot 物件」。
    #
    # 刻意是個非空字串，不要改成 True / False / None ——
    # 理由跟 PUZZLE_SOLVED 那三個常數一樣，見 puzzle.rpy 的開頭。
    CLOSEUP_CLOSED = "closeup_closed"

    # 框比背景圖往外多出來的邊 (像素)，四邊都一樣。
    CLOSEUP_FRAME_PAD = 24

    def closeup_room(name):
        """
        把近景房間的名稱換成 Room 物件。查不到就直接報錯。

        近景房間一定要註冊在 rooms 裡 —— 不只是為了這裡查得到，
        也因為熱點存檔時是用「房間名稱 + 熱點名稱」還原的
        (見 Hotspot.__reduce__)，沒註冊的話點下去那一刻存檔會爆掉。
        """
        room = getattr(store, "rooms", {}).get(name)

        if room is None:
            renpy.error(
                f"找不到名稱為 {name} 的近景房間！\n"
                f"近景房間要跟其他房間一樣註冊在 build_rooms() 裡。"
            )

        return room


    def closeup_misuse(room):
        """
        檢查一個房間拿來當近景用時有沒有被誤用，回傳問題說明的清單。
        沒問題就回傳空清單。

        為什麼要主動擋
        ==============
        近景只處理「點擊」。所以近景房間如果寫了 on_enter，那句開場白
        **永遠不會播** —— 而畫面上完全看不出有什麼不對，
        遊戲照跑、框照開，只是那句話人間蒸發。

        這正是 PROJECT_RULES.md 最在意的那種隱形 bug，所以寧可一啟動
        就吵著報錯。寧可難寫一點，也不要讓設計者對著一句不會播的台詞
        查半天。

        純函式，回傳訊息而不是直接丟例外 —— 這樣測試可以直接斷言
        「這種寫法會被抓到」，不用去接例外。
        """
        problems = []

        if getattr(room, "on_enter", None):
            problems.append(
                f"- on_enter=\"{room.on_enter}\" 不會被執行。"
                f"近景沒有「進房間」這件事，它只是一個框。\n"
                f"  想在打開的瞬間講話，請寫在呼叫 open_closeup() 之前。"
            )

        # on_enter 會被 Room 轉成一個 Event 塞進 events，所以上面那條
        # 命中時這條也會命中。兩條都留著是刻意的 —— 分別報比較好懂，
        # 而寫 on_enter 的人看到上面那條就夠了。
        if getattr(room, "events", None):
            problems.append(
                f"- 掛在房間上的 events 不會被執行 (有 {len(room.events)} 個)。"
                f"近景沒有進房/離房/計時這些時機。\n"
                f"  事件請掛在近景裡面的 Hotspot 上。"
            )

        if getattr(room, "music", None):
            problems.append(
                f"- music=\"{room.music}\" 不會被播放。近景不切背景音樂。\n"
                f"  想要開抽屜的音效請用 Hotspot(sound=...)，"
                f"或是在呼叫 open_closeup() 的 label 裡自己播。"
            )

        if getattr(room, "bg_height", None) is None:
            problems.append(
                "- 近景房間一定要填 bg_height。那是框的高度；"
                "不填的話框會拉滿整個螢幕高，\n"
                "  看起來就不是一個「視窗」了。"
            )

        for hotspot in room.hotspots:
            for event in getattr(hotspot, "events", None) or []:
                if event.trigger is not None and event.trigger != TriggerType.CLICK_HOTSPOT:
                    problems.append(
                        f"- 熱點 \"{hotspot.name}\" 的事件 \"{event.id}\" 寫了 "
                        f"trigger={event.trigger}，近景裡只有點擊會發生。\n"
                        f"  把 trigger 拿掉 (預設就是點擊) 或改成 "
                        f"TriggerType.CLICK_HOTSPOT。"
                    )

        return problems


screen closeup(room):

    # 擋住後方所有東西 —— 框開著時點不到房間的熱點，也換不了房間。
    #
    # 注意 modal 擋的是「點擊」不是「滑鼠移動」，所以底下房間的鏡頭
    # 仍然會跟著滑鼠移動 (跟翻頁視窗、解謎視窗一樣，這是刻意允許的)。
    modal True

    zorder 200

    # 每一幀重新整理畫面，讓底下的 hover 判定跟著更新。
    #
    # 探索畫面是靠 camera.update 的 timer 順便達成這件事的；
    # 近景沒有鏡頭，所以要自己放一個。
    #
    # ⚠️ 一定要用 NullAction()，**不能**用任何會回傳值的東西。
    # 畫面動作回傳非 None 就會結束互動 —— 在這裡等於每 0.016 秒
    # 就把視窗關掉一次。(這個坑在世界時鐘的 timer 上真的踩過)
    timer 0.016 repeat True action NullAction()

    # 框的左上角。
    #
    # 刻意自己算座標而不是用 align (0.5, 0.5)：底下 hover 判定要把
    # 滑鼠的螢幕座標換成「框裡面的座標」，所以必須知道框到底在哪。
    $ _cu_w = room.bg_width
    $ _cu_h = room_bg_height(room)
    $ _cu_ox = (config.screen_width - _cu_w) // 2
    $ _cu_oy = (config.screen_height - _cu_h) // 2

    $ _cu_mx, _cu_my = renpy.get_mouse_pos()

    # 按 ESC (或滑鼠右鍵) 關閉。不攔截的話這兩個操作會跳出遊戲選單。
    key "game_menu" action Return(CLOSEUP_CLOSED)

    # 背景壓暗。沿用翻頁視窗的外觀，讓玩家覺得是同一個遊戲的視窗。
    add "#000000cc"

    frame:
        xpos _cu_ox - CLOSEUP_FRAME_PAD
        ypos _cu_oy - CLOSEUP_FRAME_PAD
        xysize (_cu_w + CLOSEUP_FRAME_PAD * 2, _cu_h + CLOSEUP_FRAME_PAD * 2)
        padding (CLOSEUP_FRAME_PAD, CLOSEUP_FRAME_PAD)
        background Frame(Solid("#1a1a1acc"), 0, 0)

        # 框的內容區剛好是 bg_width x bg_height，而它的螢幕左上角
        # 正好是 (_cu_ox, _cu_oy) —— 外層往外退了 PAD，padding 又補回來。
        # 所以熱點的 x / y 可以直接用，不用加任何位移。
        fixed:
            xysize (_cu_w, _cu_h)

            add room.background:
                xsize _cu_w
                ysize _cu_h

            for hotspot in room.hotspots:
                $ _cu_hw, _cu_hh = hotspot_size(hotspot)

                if hotspot_is_shown(hotspot):
                    if hotspot.label:
                        # 文字/emoji 熱點
                        textbutton hotspot.label:
                            xpos hotspot.x
                            ypos hotspot.y
                            text_size hotspot.label_size
                            text_color hotspot.label_color
                            text_hover_color hotspot.label_hover_color
                            activate_sound hotspot.sound
                            # 回傳「被點到的那個熱點」，由 open_closeup 去跑它的事件。
                            # 不走 Call("_fire_hotspot", ...) 是因為那樣會跳走，
                            # 而我們需要先讓 call_screen 正常返回 (框才會消失)。
                            action Return(hotspot)
                    else:
                        button:
                            xpos hotspot.x
                            ypos hotspot.y
                            xsize _cu_hw
                            ysize _cu_hh
                            background ("#ff000055" if hotspot.debug else None)
                            activate_sound hotspot.sound
                            action Return(hotspot)

                        if hotspot.idle:
                            add Transform(hotspot.idle, xysize=(_cu_hw, _cu_hh)):
                                xpos hotspot.x
                                ypos hotspot.y

                        # hover 圖：把滑鼠的螢幕座標換成框裡面的座標再判定。
                        if hotspot.hover and hotspot_contains(hotspot, _cu_mx - _cu_ox, _cu_my - _cu_oy):
                            add Transform(hotspot.hover, xysize=(_cu_hw, _cu_hh)):
                                xpos hotspot.x
                                ypos hotspot.y

    # 右上角關閉鈕。放在 frame 外面，所以不會被框的大小影響。
    textbutton "✕":
        align (0.97, 0.04)
        text_size 28
        text_color "#888888"
        text_hover_color "#ffffff"
        action Return(CLOSEUP_CLOSED)


# 打開近景視窗，等玩家關掉才會往下走。
#
#     call open_closeup("drawer_inside")
#
# 流程：開框 -> 玩家點東西 -> 框消失 -> 跑那個熱點的事件 (講話)
#      -> 框回來 -> ... -> 玩家按 ✕ -> return
label open_closeup(room_name):

    # 誤用檢查放在最前面，而且只做一次 ——
    # 這種錯誤是設計者寫錯，不是玩家操作造成的，查一次就夠了。
    python:
        _cu_problems = closeup_misuse(closeup_room(room_name))

        if _cu_problems:
            renpy.error(
                "近景房間 \"%s\" 的設定有問題：\n\n%s\n\n"
                "近景只處理「點擊裡面的熱點」這一件事。"
                % (room_name, "\n".join(_cu_problems))
            )

    # 收掉對話框，不然黑框會疊在近景視窗上
    window hide

    while True:

        # 每一圈重新查一次房間，**刻意不把它存在迴圈外面**。
        #
        # 理由是下面那個 call 會離開這裡去跑別的 label。label 裡的
        # $ 變數其實是 store 變數 (全域的)，所以如果那串劇情裡又開了
        # 一個近景，內層就會把外層的房間蓋掉 —— 回來之後打開的是錯的框。
        #
        # room_name 是 label 的參數，Ren'Py 會幫它做 scope，
        # 所以每一層各自記得自己要開哪個房間。
        # (同一個理由見 dispatcher.rpy 裡 run_event_labels 的 labels 參數)
        $ _cu_room = closeup_room(room_name)

        # 倒帶要跳過這個視窗 —— 跟翻頁視窗、解謎視窗同一個問題：
        #
        # call screen 本來是倒帶的停靠點，而近景是 modal，會擋住
        # quick menu 的「返回」。倒帶停在框裡面的話，玩家在裡面按不到
        # 返回、只能關掉，關掉再按返回又回到框裡，永遠出不去。
        $ renpy.suspend_rollback(True)

        # 近景期間世界時鐘要繼續走 —— 玩家在翻抽屜的時候鬼照樣逼近。
        #
        # 需要 suspend 而不是 resume 的理由跟解謎視窗一樣：近景是從熱點的
        # label 叫出來的，而那些 label 由 run_event_labels 執行，
        # 那裡為了對話已經把時鐘暫停了。見 world.suspend_pauses 的說明。
        $ world.suspend_pauses()

        $ _cu_result = renpy.call_screen("closeup", room=_cu_room)

        $ world.restore_pauses()
        $ renpy.suspend_rollback(False)

        # 這裡就是「第 3 件」(Puzzle.pausable + 被鬼抓關窗) 要接上來的地方：
        # 到時候 world.interrupt 會由計時事件舉起來，上面那個 screen 裡
        # 多一個輪詢的 timer 把視窗關掉，然後這裡判斷「是被鬼關的」就
        # 直接 return，不要再把框打開。目前 world.interrupt 還沒有人設。

        # 不是熱點就結束。
        #
        # 涵蓋 CLOSEUP_CLOSED，也涵蓋任何預期外的回傳值 ——
        # 例如之後有人在這個 screen 裡誤寫了 Return() (那會回傳 True)。
        # 那時候「關掉視窗」比「拿 True 去當熱點用」安全得多。
        if not isinstance(_cu_result, Hotspot):
            return

        python:
            # 跟 _fire_hotspot 完全一樣的處理，只是熱點來自近景。
            #
            # context 給的是 current_room (玩家真正站著的房間)，不是近景房間 ——
            # 近景不是一個玩家「在裡面」的地方，條件要用真實所在地判斷。
            _cu_labels = collect_events(
                _cu_result.events,
                TriggerType.CLICK_HOTSPOT,
                EventContext(store.game_state, store.current_room),
                TriggerType.CLICK_HOTSPOT,
            )

            if _cu_result.on_click:
                _cu_labels.append(_cu_result.on_click)

        # 交給既有的第二階段。走這裡而不是自己 call，是為了把死亡檢查
        # 一起吃下來 —— 近景裡的「嚇人」可以扣血，扣到 0 就會走既有的
        # on_player_death 流程，不用在這裡再寫一次。
        call run_event_labels(_cu_labels) from _call_closeup_hotspot

        # 嚇到死了就不要再把框打開。
        #
        # 有宣告 on_player_death 的話 run_event_labels 會直接 jump 走，
        # 根本回不到這裡；這一條是給「沒宣告死亡 label」的專案用的 ——
        # 那種情況下死亡只是 hp=0 的狀態，執行會繼續回來。
        if store.game_state.actors.is_dead(PLAYER_ACTOR):
            return
