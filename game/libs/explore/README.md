# 探索工具包 v0.1 使用說明

FNAF 風格的橫向掃視探索系統：一張比螢幕寬的背景圖，滑鼠往左右移動、鏡頭跟著掃過去，
圖上放可以點擊的熱點，點下去講話或觸發事件。

---

## 檔案結構

```
game/libs/explore/          引擎，不要放具體房間資料
├── camera.rpy              Camera 類別 + default camera
├── room.rpy                Room 類別
├── hotspot.rpy             Hotspot 類別 + hotspot_action()
├── room_manager.rpy        change_room() / explore_loop / say_in_room
├── explore_screen.rpy      screen explore() / room_background()
└── explore_debug.rpy       F9 標點面板（疊加式 overlay）

game/libs/ui/               通用 UI，跟探索工具包無關
└── page_popup.rpy          翻頁視窗 show_pages()

game/explore_demo/          遊戲內容，可以整個刪掉換成自己的
├── rooms.rpy               build_rooms() + default rooms
├── demo_room.rpy           示範房間與它的 label
├── kitchen.rpy             第二個示範房間（驗證房間切換）
└── tests.rpy               自動化測試
```

分界原則：**引擎層不出現任何具體房間名稱**。
新增房間只動內容層，`game/libs/explore/` 完全不用碰。

---

## 建立一個新房間：三個步驟

### 步驟 1：寫房間檔案

在 `game/explore_demo/`（或你自己的內容目錄）新增一個 `.rpy`，例如 `kitchen.rpy`：

```renpy
init python:

    def build_kitchen():
        room = Room(
            name="kitchen",
            background="images/bg_kitchen.png",
            bg_width=3000,                  # 背景圖的實際寬度，一定要填對
            on_enter="kitchen_enter",       # 進來時自動跑的 label，不要可以省略
        )

        room.add_hotspot(Hotspot(
            name="fridge",
            x=1200, y=400,                  # 背景圖座標，不是螢幕座標
            width=300, height=500,
            debug=True,                     # 開發時開著看得到判定範圍
            action=Call("say_in_room", "kitchen_look_fridge"),
        ))

        return room


label kitchen_enter:
    "廚房裡有股燒焦味。"
    return

label kitchen_look_fridge:
    "冰箱門上貼滿了便條紙。"
    return
```

**把房間定義和它的 label 放在同一個檔案。**
這樣要知道「這個房間點下去會發生什麼」，看一個檔案就夠了。

### 步驟 2：註冊到房間清單

打開 `game/explore_demo/rooms.rpy`，在 `build_rooms()` 裡加一行：

```renpy
def build_rooms():
    rooms = {}

    rooms["demo_room"] = build_demo_room()
    rooms["kitchen"] = build_kitchen()      # 加這行

    return rooms
```

### 步驟 3：切換過去

```renpy
$ change_room("kitchen")
```

熱點的 action 裡要切房間的話，包成 label 再用 `Call`：

```renpy
action=Call("say_in_room", "go_to_kitchen")

label go_to_kitchen:
    $ change_room("kitchen")
    return
```

---

## Room 參數

| 參數 | 必填 | 說明 |
|---|---|---|
| `name` | 是 | 房間名稱，建議跟 `rooms` 字典的 key 取一樣 |
| `background` | 是 | 背景圖，可以是圖片路徑字串或任何 Ren'Py displayable |
| `bg_width` | | 背景圖實際寬度，預設 1920。**填錯鏡頭範圍就會錯** |
| `music` | | v0.1 尚未實作，填了不會播放 |
| `hotspots` | | 熱點列表，也可以建立後用 `add_hotspot()` 一個個加 |
| `on_enter` | | 進入房間時自動呼叫的 label 名稱（字串） |
| `on_enter_limit` | | `on_enter` 最多觸發幾次，**預設 1**（只有第一次進來會講）。`None` = 每次都觸發，`2` = 前兩次都講 |

方法：`add_hotspot(h)` / `remove_hotspot(h)` / `get_hotspot(name)`

---

## Hotspot 參數

### 位置與判定

| 參數 | 說明 |
|---|---|
| `name` | 熱點名稱，`room.get_hotspot("名稱")` 要用 |
| `x` / `y` | **背景圖座標**（左上角為原點），不是螢幕座標 |
| `width` / `height` | 判定範圍，不填預設 100×100 |

### 外觀（三選一）

**A. 文字／emoji 熱點** — 不需要任何美術素材，最適合先做原型：

```renpy
Hotspot(name="key", x=800, y=600,
        label="🔑 撿起鑰匙",
        label_size=28,
        label_color="#e67e22",
        label_hover_color="#ffffff",
        action=Call("say_in_room", "pick_key"))
```

**B. 圖片熱點**：

```renpy
Hotspot(name="lamp", x=800, y=600, width=200, height=300,
        idle="images/lamp.png",         # 平常顯示
        hover="images/lamp_glow.png",   # 滑鼠移上去時顯示
        action=Call("say_in_room", "look_lamp"))
```

`idle` / `hover` 會被縮放成 `width` × `height`。

**C. 隱形熱點** — 三個都不填，熱點就是背景圖上一塊看不見的可點區域。
開發時加 `debug=True` 會畫出半透明紅框，正式上線改回 `False` 就隱形。

### 行為

| 參數 | 說明 |
|---|---|
| `action` | 點擊時執行的 screen action，通常是 `Call("say_in_room", "label名")` |
| `sound` | 點擊音效，用按鈕內建的 `activate_sound` 播放 |
| `visible` | 是否顯示，預設 `True` |
| `enabled` | **v0.1 尚未接上**，改了不會有效果 |

### 尚未實作的欄位

`item` / `require_item` / `action_if_missing` 這三個欄位可以填，
但 v0.1 沒有 inventory 模組，目前不會被消費，點擊一律執行 `action`。

### 其他

`tag` / `examine` / `data` 是給你自己用的自訂欄位，引擎不會碰它們。
`data` 預設是空 dict，可以塞任何東西。

---

## 座標怎麼抓

demo 房間的背景是程式產生的測試圖，每 400px 一條色帶並標上該處的 X 座標
（`demo_room.rpy` 的 `_build_demo_background()`）。

換成自己的背景圖之後，最快的方式是：

1. 先用 `debug=True` 開一個隱形熱點，隨便填一個座標
2. 進遊戲看紅框跑到哪裡，回頭調整數字
3. 位置對了再把 `debug` 改成 `False`

Y 座標比較單純：背景圖高度會被強制縮放成螢幕高度（1080），
所以 `y` 直接就是螢幕上的垂直位置。

---

## 對話為什麼要走 say_in_room

探索畫面 `explore()` 的熱點按鈕鋪滿整個畫面，會把點擊全部吃掉，
對話框會點不下去。所以**所有探索中途的對話都必須走 `say_in_room`**：

```renpy
action=Call("say_in_room", "你的label名稱")
```

`say_in_room` 做的事：

```
收起 explore（熱點消失）
   ↓
顯示 room_background（只剩背景，放在 master layer，立繪能正常疊上去）
   ↓
跑你的 label
   ↓
收起 room_background、放回 explore（回到可互動狀態）
```

**不要直接寫 `action=Jump("你的label")`** —— 熱點按鈕不會被收起來，對話會卡住。

---

## 啟動探索

```renpy
label start:
    show screen explore
    $ change_room("demo_room")
    jump explore_loop
```

`explore_loop` 是探索狀態的主迴圈，不會自己結束。
要離開探索（例如進入劇情章節），從熱點的 label 直接 `jump` 出去即可。

---

## 常見錯誤

**對話講完跳回主選單**
入口沒有 `jump explore_loop`，或是自己寫了單獨一句 `renpy.pause()`。
`Call()` 講完 return 時，返回點是「pause 的下一句」而不是 pause 本身，
執行流會往下衝出 label 結尾導致遊戲結束。必須用 `explore_loop` 的 `while True` 接住。

**鏡頭掃不到背景右邊 / 掃過頭出現黑邊**
`bg_width` 跟背景圖實際寬度對不上。

**熱點位置整個偏掉**
`x` 填成了螢幕座標。熱點用的是**背景圖座標**，
外層容器已經統一做過鏡頭位移，不要自己再加 `camera.offset`。

**改了 hotspot 卻沒反應**
`rooms` 是用 `default` 宣告的，房間物件會存進存檔，改了原始碼不會自動生效。
按 Shift+R 再按 debug 面板的「重新載入房間資料」，兩步都要做
（原因見上面「改完座標怎麼讓它生效」）。

**進房間的開場白只講一次**
這是預設行為，`on_enter_limit` 預設為 1。想每次進來都講就設 `on_enter_limit=None`。

---

## Debug 標點面板

標 hotspot 位置時用的。

| 按鍵 | 作用 |
|---|---|
| `F9` | 顯示／隱藏面板 |
| `F10` | 釘住目前滑鼠座標 |

面板顯示目前房間、`bg_width`、`camera.offset`、即時滑鼠的螢幕座標與**房間座標**，
以及 F10 釘住的座標。**「滑鼠房間座標」那一行的數字，就是直接填進 `Hotspot(x=…, y=…)` 的值。**

標點流程：按 F9 → 滑鼠移到想放熱點的位置 → 按 F10 釘住 → 抄下「釘住的房間座標」。

用按鍵釘選而不是用點擊記錄，是因為想標的位置常常就在某個熱點附近，
點下去會直接觸發那個熱點跳出對話。

### 改完座標怎麼讓它生效

**正確流程是兩步，順序不能反：**

```
1. 在遊戲中按 Shift+R      ← 重新載入腳本，build_rooms() 變成新的
2. 按「重新載入房間資料」   ← 用新的 build_rooms() 重建 rooms
```

**為什麼需要兩步**：`Shift+R` 的實際行為是「存檔 → 重載腳本 → **讀回那個存檔**」。
而 `rooms` 是 `default` 宣告的，會被存進存檔，所以讀回來的還是舊物件 ——
此時 `build_rooms()` 函式已經更新，但 `rooms` 資料還是舊世代的。
`default` 只在變數不存在時執行，讀檔後 `rooms` 已存在，不會重跑。

所以單按 Shift+R 看不到新熱點，單按「重新載入房間資料」則是用**舊函式**重建，
兩個都沒用。必須先 Shift+R 更新函式，再按按鈕重建資料。

（回標題再 Shift+R 也會生效，因為那條路徑是完全重啟 + 開新遊戲，`default` 會重跑。
只是繞得比較遠。）

「重新載入房間資料」按下去會先跳確認，因為它會**重建所有 Room / Hotspot 物件**，
遊戲中改過的狀態（`hotspot.visible`、`on_enter_count` 等）會全部回到初始值。

它需要內容層有一個叫 `build_rooms()` 的函式，找不到會顯示提示而不是當掉。

按鍵設定在 `explore_debug.rpy` 的 `config.keymap`，想換鍵改那裡。
Ren'Py 內建已佔用 F1／F2／F3／F4／F7／F8／F11。

---

## 翻頁視窗

`game/libs/ui/page_popup.rpy`，通用元件 —— 教學、道具說明、線索筆記都能用。
它不依賴探索工具包的任何東西，可以單獨複製到別的專案。

```renpy
define PAGES_HELP = [
    {"title": "移動", "text": "把滑鼠移到左右兩側…", "img": "images/arrow.png"},
    {"title": "互動", "text": "可互動的東西點下去會有反應。"},
]

label show_help:
    call show_pages(PAGES_HELP)
    return
```

`title` / `text` / `img` 三個欄位都可省略。只有一頁時翻頁按鈕自動隱藏。
關閉方式：底部按鈕、右上角 ✕、ESC（或滑鼠右鍵）。

呼叫端會**停在這裡**，等玩家關掉視窗才往下走。

視窗是 `modal`，開著時點不到底下的熱點。但 modal 擋的是點擊不是滑鼠移動，
所以探索畫面上開視窗時，底下的鏡頭仍會跟著滑鼠晃 —— 這是刻意允許的，
視窗置中且面積大，不影響閱讀。

熱點要開視窗的話，**不需要走 `say_in_room`**（modal 本身就擋住熱點了）：

```renpy
Hotspot(name="help", x=1500, y=880, label="📖 看說明",
        action=Call("demo_show_help"))
```

---

## 自動化測試

`game/explore_demo/tests.rpy` 有六份測試，在 SDK 目錄下執行：

```
renpy.exe <專案路徑> test <測試名稱>
```

| 測試 | 驗證內容 |
|---|---|
| `explore_smoke` | 完整探索流程：開場白 → 點熱點 → 換房間 → 換回來 → 再換一次。重點是連續多次互動後探索狀態還在 |
| `popup_and_debug` | 翻頁視窗開關翻頁、F9／F10、面板開著時熱點仍可點、重新載入房間資料含確認流程 |
| `unit_checks` | 純邏輯：`Camera.enter_room` 的三種寬度、`Room` 熱點增刪查、`on_enter_limit` 的 1／2／None／未設定、`Hotspot` 狀態方法 |
| `regression_fixes` | 已修 bug 的回歸：對話結束後對話框要收起來、F10 釘住的座標不隨鏡頭移動而改變 |
| `popup_edge_cases` | ESC 關閉、單頁時翻頁鈕消失、空頁面不會爆掉 |
| `hotspot_visibility` | `hide()` / `show()` 之後畫面上是不是真的看不到／看得到 |

結果寫在專案根目錄的 `log.txt`（搜尋 `[rpytest]`），
每個步驟的狀態則寫在 `test_trace.txt`。

### 寫測試時會踩到的三個坑

**1. 從主選單開始，第一步要先進遊戲**

```renpy
click "開始"
```

介面是繁體中文，按鈕文字是「開始」不是 "Start"。

**2. 用 `advance until` 推對話，不要數 advance 次數**

```renpy
advance until "走去廚房"
```

一直推進對話，直到畫面上出現這個熱點 —— 熱點出現就代表 `say_in_room` 已經把
`explore` 畫面放回來了。這樣改對話長度不用跟著改測試。

**3. 要移動鏡頭必須用 `renpy.set_mouse_pos()`，不能用測試框架的 `move`**

```renpy
$ renpy.set_mouse_pos(60, 540)
pause 2.0
```

`camera.update()` 讀的是 `renpy.get_mouse_pos()`，而那個函式**不經過測試框架的滑鼠覆寫**
（覆寫只套用在 `core.py` 的事件迴圈，用來決定 focus 與點擊目標）。
用 `move` 的話鏡頭完全不會動，測試會變成靠執行當下真實游標剛好在哪裡來決定成敗。
副作用是這會實際移動你的滑鼠游標。

`click` 不受影響 —— 它走 focus 系統，會自己找到目標。

### 另外兩件事

- **文字選擇器只找得到按鈕**。`assert "某文字"` 走的是 `find_focus`，
  標題、說明文字這種純 `text` 永遠找不到，不能拿來當斷言對象。
- **斷言不要綁死 demo 的可變內容**。例如不要寫 `assert on_enter_count == 1` ——
  demo 房間的 `on_enter_limit` 隨時可能被調整，改一下測試就誤報。
  改成驗證不變量（沒超過上限），精確邏輯交給 `unit_checks` 用自建物件去測。

結果寫在專案根目錄的 `log.txt`（搜尋 `[rpytest]`），
每個步驟的狀態則寫在 `test_trace.txt`。

寫這種測試有三個要點：

**1. 從主選單開始，第一步要先進遊戲**

```renpy
click "開始"
```

介面是繁體中文，按鈕文字是「開始」不是 "Start"。

**2. 用 `advance until` 推對話，不要數 advance 次數**

```renpy
advance until "走去廚房"
```

意思是「一直推進對話，直到畫面上出現這個熱點」。
熱點出現就代表 `say_in_room` 已經把 `explore` 畫面放回來了。
這樣之後改對話長度，測試不用跟著改。

**3. 熱點在畫面外時要先移動鏡頭**

```renpy
move pos (100, 540)
pause 2.0
click "回到測試房間"
```

測試框架點不到畫面外的東西。先把滑鼠移到該側、等鏡頭掃過去，熱點才會進入畫面。

**注意**：測試失敗時 Ren'Py 會停在錯誤畫面不會自動退出，進程要自己關掉。

---

## 鏡頭手感調整

`camera.smooth` 控制鏡頭跟隨的速度，預設 `0.10`：
數字越小越慢越滑順，越大越跟手越銳利。

```renpy
$ camera.smooth = 0.05      # 更慢、更有重量感
```
