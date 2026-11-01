# 開發須知

做《最後一班》時整理出來的速查表，給**下一個遊戲（擴充版）**開工前看。

- 這份只講「常用的、常踩的、常問的」，細節一律連到
  `game/libs/explore/DEVELOPER_GUIDE.md`（以下簡稱 **GUIDE**）的章節
- 《最後一班》本身的劇情與設計在 `GAME_DESIGN.md`
- 實際踩過的坑與當時的錯誤原因在 `MEMORY.md`

---

## 1. 常用功能速查

照「想做的事」查。《最後一班》每一項都實際用過。

### 房間與移動

| 想做的事 | 寫法 | GUIDE |
|---|---|---|
| 開一個房間 | `build_xxx()` 回傳 `Room(...)`，**最後一行一定要 `return room`**，再到 `rooms.rpy` 註冊 | Room 房間 |
| 寬房間（鏡頭會橫向掃） | `bg_width=3200`；1920 就是不捲動 | Room 房間 |
| 換房間 | label 裡 `$ change_room("xxx")` | 為什麼沒有 change_room 和 hide_hotspot |
| 第一次進來講一段話 | `Room(on_enter="label")`，預設只講一次 | on_enter 與 on_enter_limit |
| 離開時發生事情 | `Event(trigger=TriggerType.EXIT_ROOM, ...)` | trigger 是什麼 |

### 熱點

| 想做的事 | 寫法 | GUIDE |
|---|---|---|
| 文字熱點（原型最快） | `Hotspot(..., label="🔑 鑰匙")` | 外觀三選一的差別 |
| 隱形熱點（蓋在背景上） | 只填 `x, y, width, height` | 外觀三選一的差別 |
| 圖片熱點 | `idle="images/xxx.png"`，**比例要跟原圖一樣** | 外觀三選一的差別 |
| 點了只跑一個 label | `on_click="label"` | on_click 還是 events？ |
| 點了要依狀態分支 | `events=[Event(...), ...]` + `sequence` + `stop=True` | on_click 還是 events？ |
| 拿過就消失 | `condition=Condition(forbid=["物品key"])` | condition 控制顯示 |

### 條件、事件、結果

| 想做的事 | 寫法 |
|---|---|
| 有 X 才成立 | `Condition(require=["X"])` |
| **沒有** X 才成立 | `Condition(forbid=["X"])` |
| 任一個就好 | `Condition(require_any=["A", "B"])` |
| 數值判斷 | `Condition(check=lambda s: s.stats("player", "battery") > 0)` |
| 每次都觸發 | `Event(..., limit=None)`（**預設 1 = 只觸發一次**） |
| 這一個成立就不要再往下檢查 | `Event(..., stop=True)` |
| 誰先跑 | `sequence=10`、`20`…，小的先 |
| 給物品／扣物品 | `Effect(give_items=["key", ("battery", 5)])`、`remove_items=[...]` |
| 設旗標 | `Effect(set_flags=["opened"])` |
| 改數值 | `Effect(actor="player", stats={"hp": -1})` |
| 取消別的事件 | `Effect(kill_events=["事件id"])` |
| 進房 N 秒後發生 | `Event(trigger=TriggerType.TIMER, delay=5, ...)` |

> **`give_items`、`set_flags`、`label` 這些都是 `Effect` 的參數，不是 `Event` 的。**
> 寫成 `Event(give_items=...)` 會直接 TypeError。

### 物品、角色、數值

| 想做的事 | 寫法 | GUIDE |
|---|---|---|
| 定義物品 | `items.rpy` 的 `build_items()`，`define item_catalog` | Item 物品 |
| 物品說明視窗顯示大圖 | `Item(icon="images/xxx.png")` | Item 物品 |
| 角色說話 | `define me = Character("你")`，然後 `me "台詞"` | 角色 |
| 一個檔案一個角色 | `characters/xxx.rpy` 寫 `build_xxx()`，再到 `characters.rpy` 的 `build_actors()` 加進去 | 角色 |
| 狀態欄顯示數值 | `Actor(status_display=[...])`；數值還沒設定過就不會顯示 | 把數值顯示給玩家看 |
| 死亡 → Game Over | `define on_player_death = "game_over"` + `label game_over`（最後 `$ renpy.full_restart()`） | 死亡 |

### 視窗與演出

| 想做的事 | 寫法 | GUIDE |
|---|---|---|
| 翻頁說明（告示、筆記） | `call show_pages(PAGES)` | 彈出翻頁視窗 |
| 放大鏡（抽屜內部） | 近景 `Room(bg_width=, bg_height=)` + `call open_closeup("名稱")` | 近景視窗 |
| 密碼鎖 | `KeypadPuzzle(code="4721", ...)` + `call run_puzzle("名稱")` | 寫一個密碼鎖 |
| 九宮格 | `PatternPuzzle(pattern="159", min_length=3, ...)` | 寫一個九宮格解鎖 |
| 嚇人圖 | `call show_jumpscare("圖片名稱")` | 鬼到了要演出來：嚇人視窗 |
| 角色走近 | `show xxx at stand(x, z)` → `show xxx at step(x, z, t)` → **`hide xxx`** | 另一種演出：讓鬼走過來 |
| 背景音樂 | `play music "bgm/xxx.mp3" fadein 1.0 volume 0.5` | （Ren'Py 原生） |
| 配音 | 台詞前一行 `voice "audio/xxx_01.m4a"` | （Ren'Py 原生） |

---

## 2. 圖片格式規定

**畫面是 1920×1080。** 下面的「怎麼縮放」是引擎實際的行為（查過原始碼），
不照尺寸畫就會變形或被裁掉。

| 用途 | 尺寸 | 引擎怎麼縮放 | 格式 | 《最後一班》的例子 |
|---|---|---|---|---|
| **房間背景** | 寬 = `bg_width`（≥1920），高 **1080** | **硬拉成 `bg_width × 1080`**——比例不對就變形 | PNG / JPG / WEBP | `bg_corridor.png` 3200×1080 |
| **近景背景** | 剛好 = `bg_width × bg_height` | **硬拉成框的大小**；框外圍還有 24px 邊，所以最大約 1872×1032 | PNG / JPG / WEBP | `closeup_drawer.png` 1280×720 |
| **圖片熱點**（`idle` / `hover`） | 任意，但熱點的 `width:height` 要等於原圖比例 | **硬拉成 `width × height`** | PNG（透明底） | `item_key.png` 220×120 |
| **物品圖示**（`Item.icon`） | 建議接近正方形 | 物品欄清單裡**硬拉成 28×28**；說明視窗裡**等比例縮進 900×380** | PNG（透明底） | `item_photo.png` 260×320 |
| **翻頁視窗的圖**（`"img"`） | 任意 | 等比例縮進 900×380 | PNG / JPG | — |
| **嚇人圖**（`show_jumpscare`） | 滿版就是 1920×1080 | **不縮放**，原尺寸置中——比畫面大會被裁掉 | PNG / JPG | `jumpscare_sister.png` 1920×1080 |
| **立繪**（`stand` / `step`） | 高度建議 ≤ 1080 | 原尺寸 × `zoom`，**腳貼畫面底**（`yalign 0.98`） | PNG（透明底） | `father_stand.png` 800×1100 |

**要注意的三件事**

1. **「硬拉」的那幾種，比例一定要對。** 測試 `last_shift_step5` 有一個
   `_ls_hotspot_box_problems()`，會用 `renpy.image_size()` 檢查近景熱點的比例，
   擴充版可以照抄給所有圖片熱點用。
2. **物品圖示一張兩用**：清單裡的小圖和說明視窗的大圖是同一張，
   不是正方形的圖在清單裡會被壓扁（見下面〈缺口〉）。
3. **立繪放大時臉會跑出畫面**：腳是貼底的，`zoom` 超過約 1 時頭會超出上緣。
   想讓臉塞滿畫面，要另外寫一個 `yalign 0.0` 的 transform。

### 音訊

| 用途 | 放哪 | 格式 |
|---|---|---|
| 背景音樂 | `game/bgm/` | mp3、ogg（**實測 Ren'Py 8.5.3 可播**） |
| 配音 | `game/audio/` | m4a、ogg（**m4a 實測可播**，9.8 秒的檔讀得到長度） |

找不到音檔時**不會報錯**，只是安靜地不播——
路徑打錯很難發現，第一次放音檔時要實際聽一次。

---

## 3. 缺口確認

工具包目前做不到、要繞路的地方。**不改引擎**，先記在這裡。

| # | 缺口 | 現在怎麼繞 | 狀態 |
|---|---|---|---|
| 1 | **物品欄沒有「使用物品」**——點物品只會開說明 | 在熱點上做（例：客廳的「補充電池」熱點），`remove_items` + `stats` | 繞過，未解 |
| 2 | **計時事件不能重複**——`TIMER` 整場只觸發一次 | 每間房各掛一個 `TIMER`，逃脫時 `kill_events` | 繞過，未解 |
| 3 | **沒有「誰在追你」的顯示**——追逐到點之前畫面上沒有任何跡象 | 主角加一個自訂數值（例如 `chased`）放進 `status_display` | 未解 |
| 4 | **物品圖示一張兩用**——清單 28×28 與說明大圖共用 `icon` | 用接近正方形的圖 | 未解 |
| 5 | **近景的座標要自己算**——F9 標點面板量到的是房間座標 | 對照近景原圖算，左上角是 (0, 0) | 未解 |
| 6 | **沒有地圖（map）** | — | 未做 |

1–3 的完整說明（想做的事、現況、繞法）在 `GAME_DESIGN.md` 的〈做的過程發現的工具包缺口〉。

---

## 4. 常問的問題

做《最後一班》時實際問過的問題，照主題排。

### 概念

**`forbid` 是 `!=` 的意思嗎？**
差不多：`forbid=["X"]` 是「**沒有** X 才成立」。`require` 是「有 X 才成立」。
物品和旗標共用同一個名字空間，所以兩種都能放。

**`limit=1` 和 `stop=True` 一樣嗎？**
不一樣。
- `limit` 管「**這個事件**整場能觸發幾次」，用完就死了（預設 1，`None` 是無限）
- `stop` 管「**這一次**派發，這個成立之後後面的事件還要不要檢查」

**Room 和 Hotspot 都能掛 Event 嗎？**
都能，但 `trigger` 要對：房間上的是進房／離房／計時，熱點上的是點擊。
掛錯地方不會報錯，就是永遠不觸發（GUIDE〈trigger 實際做的事：過濾〉）。

**「門在你背後關上」那種是什麼？**
掛在房間上、`trigger=TriggerType.EXIT_ROOM` 的事件——離開這間時才觸發。

**計時事件的秒數從什麼時候開始算？**
**從進這個房間開始算**，不是從條件成立開始。對話期間時鐘會暫停。
所以「妹妹第 5 秒出現、講完再 2 秒扣血」要寫 `delay=7`。

### 怎麼做

**熱點怎麼加條件？** `Hotspot(..., condition=Condition(require=["flashlight"]))`

**怎麼讓主角講話？** `define me = Character("你")`，然後 `me "台詞"`。
沒有名字的 `"台詞"` 就是旁白。

**狀態欄怎麼顯示手電筒？** 在 `Actor(status_display=[...])` 裡加一行。
數值還沒被設定過就不會顯示——所以拿到手電筒時才用 `Effect` 加電量，🔦 才會出現。

**密碼改在哪？** `puzzles.rpy` 的 `KeypadPuzzle(code=...)` / `PatternPuzzle(pattern=...)`。
`PatternPuzzle` 少於 4 個點要加 `min_length`，否則一啟動就報錯。

**物品說明視窗怎麼顯示原圖？** `Item(icon="images/xxx.png")`。

**背景音樂太大聲？** `play music ... volume 0.5`；或開 Ren'Py 內建的
「語音播放時其他聲道降低」：`define config.default_emphasize_audio = True`。
⚠️ `default_` 開頭的設定只在**第一次執行**時套用，自己測之前要先在啟動器按
「Delete Persistent」。

**語音會被點擊切掉？** Ren'Py 預設就是這樣。要擋點擊可以用
`config.say_allow_dismiss`（《最後一班》試過後決定不用，維持可以點掉）。

### 常見錯誤訊息

| 錯誤訊息 | 原因 | 改法 |
|---|---|---|
| `'NoneType' object has no attribute 'bg_width'` | `build_xxx()` 少了 `return room`（**踩過兩次**：第二次是後面接著寫了另一個 `build_` 函式，`return` 跑到那個函式裡） | 每個 `build_` 函式最後都要有自己的 `return room` |
| `NameError: _build_demo_background` | 用到 demo 裡的函式，但 demo 已經搬出 `game/` | 把需要的函式複製到自己的檔案（例：`placeholder_bg.rpy`） |
| `label xxx is defined twice` | 兩個檔案有同名 label | label 名稱全遊戲唯一，前面加房間名，例如 `living_room_go_corridor` |
| `LabelNotFound` | 熱點或事件寫到的 label 不存在 | 測試的 `_ls_missing_labels()` 會一次列出全部 |
| `Event() got an unexpected keyword argument 'give_items'`（或 `label`） | 把 `Effect` 的參數寫在 `Event` 上 | 包一層 `effect=Effect(...)` |
| 物品 key 不一致的 ValueError，但檔案明明改好了 | 改過檔名，舊的 `.rpyc` 還在，被一起載入 | 刪掉孤兒 `.rpyc` |
| `找不到名稱為 xxx 的解謎關卡` | `run_puzzle("名稱")` 跟 `build_puzzles()` 裡的 key 不一樣 | 兩邊名稱對齊 |
| `圖形鎖 … 只有 3 個點，但 min_length=4` | 九宮格圖形太短 | 加 `min_length=3` |

---

## 5. 開工前要知道的事

- **`build_rooms()`、`build_actors()`、`build_items()`、`build_puzzles()` 全域唯一。**
  兩份同名的會安靜地互相蓋掉。新遊戲開工時，舊遊戲的資料夾要移出 `game/`。
  （細節見 `GAME_DESIGN.md`〈開新遊戲會踩的坑〉）
- **`explore_demo/` 只供閱讀，不能執行。** 2026-11-01 整理時刪掉了
  `kitchen.rpy`、`bed_room.rpy`，留下有教學註解的檔案。
  `room_sample.rpy` 是房間樣板，開新房間可以從它複製。
- **工具包自己的回歸測試（`explore_demo/tests.rpy`，約 3800 行）目前不會執行。**
  擴充版如果要改 `game/libs/` 的引擎，這套測試要先想辦法恢復，不然改壞了不會知道。
- **每做完一步就補測試。** 《最後一班》的 `game/last_shift/tests.rpy` 是範本：
  不開畫面，直接用 `collect_events` / `due_timer_events` 派發，檢查狀態。
  執行：`renpy.exe <專案路徑> test <testcase名稱>`，結果在 `log.txt` 的 `[rpytest] Status`。
- **`check_actor_catalog(rooms, puzzle_catalog)` 在《最後一班》沒有開。**
  它會在啟動時檢查角色 id 有沒有打錯，擴充版建議一開始就打開。
