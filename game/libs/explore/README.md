# 探索工具包 v0.1 使用說明

FNAF 風格的橫向掃視探索系統：一張比螢幕寬的背景圖，滑鼠往左右移動、鏡頭跟著掃過去，
圖上放可以點擊的熱點，點下去講話或觸發事件。

> **想直接開始寫遊戲內容 → 看 [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)**
> 那份有完整的欄位說明與常見情境食譜。
> 這份 README 講的是引擎本身、debug 面板與測試。

---

## 檔案結構

```
game/libs/explore/          探索引擎，不要放具體房間資料
├── camera.rpy              Camera 類別 + default camera
├── room.rpy                Room 類別
├── hotspot.rpy             Hotspot 類別 + label _fire_hotspot
├── room_manager.rpy        change_room() / explore_loop / say_in_room
├── explore_screen.rpy      screen explore() / room_background()
├── explore_debug.rpy       F9 標點面板（疊加式 overlay）
└── event/                  事件系統
    ├── trigger.rpy         TriggerType
    ├── condition.rpy       Condition（只讀）
    ├── effect.rpy          Effect（只寫）
    ├── event.rpy           Event / EventContext
    └── dispatcher.rpy      collect_events() + run_event_labels

game/libs/state/            遊戲狀態，不依賴 explore，可單獨複製
├── item.rpy                Item + item_def()
├── inventory_state.rpy     物品欄
├── flag_state.rpy          旗標
├── event_state.rpy         事件的觸發次數與死亡名單
└── game_state.rpy          GameState + StateView + default game_state

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
            on_click="kitchen_look_fridge",
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
on_click="go_to_kitchen"

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
        on_click="pick_key")
```

**B. 圖片熱點**：

```renpy
Hotspot(name="lamp", x=800, y=600, width=200, height=300,
        idle="images/lamp.png",         # 平常顯示
        hover="images/lamp_glow.png",   # 滑鼠移上去時顯示
        on_click="look_lamp")
```

`idle` / `hover` 會被縮放成 `width` × `height`。

**C. 隱形熱點** — 三個都不填，熱點就是背景圖上一塊看不見的可點區域。
開發時加 `debug=True` 會畫出半透明紅框，正式上線改回 `False` 就隱形。

### 行為

| 參數 | 說明 |
|---|---|
| `on_click` | 點一下要跑的 label 名稱（字串）。**簡寫**，等同於「無條件、每次都執行」 |
| `events` | 完整的 Event 清單，需要條件分支或次數限制時用 |
| `condition` | 顯示條件（`Condition`）。條件不成立時這個熱點不會出現 |
| `sound` | 點擊音效，用按鈕內建的 `activate_sound` 播放 |
| `visible` | 手動顯示開關，預設 `True`。與 `condition` 是 AND 關係 |
| `enabled` | **尚未接上**，改了不會有效果 |

`on_click` 與 `events` 可以同時存在，`events` 先跑、`on_click` 後跑。
但多數情況只需要其中一個。

### 用條件控制顯示，不要用 hide()

```renpy
# 撿走鑰匙後這個熱點自動消失
Hotspot(name="key_pickup", x=800, y=600, label="🔑 鑰匙",
        condition=Condition(forbid=["key"]),
        on_click="pick_up_key")
```

這比命令式的 `hide()` 好，因為它是**冪等**的：不管讀哪個存檔、reload 幾次，
只要 `GameState` 裡有 `key`，這個熱點就是不顯示。
`hide()` 則要靠「當初有沒有正確執行過」來維持狀態，一旦漏掉就永遠不一致。

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

## 探索中的對話是怎麼運作的

探索畫面 `explore()` 的熱點按鈕鋪滿整個畫面，會把點擊全部吃掉，
對話框會點不下去。所以講話之前一定要先把熱點收起來。

**這件事現在是自動的** —— `on_click` 和 `events` 的 label 都會經過 `run_event_labels`：

```
收起 explore（熱點消失）
   ↓
顯示 room_background（只剩背景，放在 master layer，立繪能正常疊上去）
   ↓
依序跑收集到的 label
   ↓
window hide（收掉對話框）
   ↓
收起 room_background、放回 explore（回到可互動狀態）
```

所以你只要寫 `on_click="label名"` 就好，不用自己處理畫面。

**`say_in_room` 還在，但你多半用不到它** —— 它現在只是
「只跑一個 label 的 `run_event_labels`」，留給從 python 直接呼叫的場合：

```renpy
$ renpy.call("say_in_room", "某個label")
```

**不要在熱點上直接用 `Jump("你的label")`** —— 那會跳過整套畫面處理，
熱點按鈕不會被收起來，對話會卡住。

---

## 事件系統

需要「有鑰匙才開得了門」這種條件分支時，用 `events` 取代 `on_click`。

```
Room / Hotspot  →  Trigger  →  Event  →  Condition  →  通過  →  Effect  →  GameState
                                             ↓
                                           不通過（什麼都不做）
```

一句話分工：**`Condition` 只讀不寫，`Effect` 只寫不讀，劇情走 label。**

### 完整範例：有鑰匙才開得了門

```renpy
Hotspot(name="door", x=800, y=400, label="🚪 門",
        events=[
            Event(id="hall.door_open",
                  condition=Condition(require=["key"]),
                  effect=Effect(set_flags=["door_opened"], label="open_the_door"),
                  sequence=10,
                  stop=True),          # 開了就不要再講「鎖住了」

            Event(id="hall.door_locked",
                  effect=Effect(label="door_is_locked"),
                  sequence=20,
                  limit=None),         # 沒鑰匙的話每次點都要講
        ])

label open_the_door:
    "鑰匙轉動了。"
    $ change_room("corridor")
    return

label door_is_locked:
    "鎖住了，需要鑰匙。"
    return
```

### Event

| 參數 | 說明 |
|---|---|
| `id` | **全域唯一**字串，慣例用 `"房間名.事件名"`。撞名會讓兩個事件共用觸發次數與死亡狀態 |
| `condition` | `Condition`。`None` = 無條件 |
| `effect` | `Effect`。`None` = 什麼都不做 |
| `sequence` | 同一個掛載點內的執行順序，小的先跑。每個房間各自獨立計算 |
| `limit` | 最多觸發幾次，用完自動死亡。預設 `1`，`None` = 無限次 |
| `stop` | 這個事件觸發後，就不再檢查後面的 |
| `trigger` | 觸發時機。不填就由掛載位置決定（`Room` → 進房，`Hotspot` → 點擊） |

**符合條件的事件會依 `sequence` 全部執行**，除非某個設了 `stop`。
死掉的事件會被直接跳過，連條件都不求值 —— 所以檢查成本會隨遊戲進行遞減。

### Condition

```renpy
Condition(
    require=["key", "map"],          # 全部都要有（AND）
    require_any=["axe", "crowbar"],  # 至少要有一個（OR）
    forbid=["saw_ghost"],            # 全部都不能有（NOT）
    check=lambda v: v.item_count("coin") >= 3,   # 逃生艙
)
```

四個欄位都不填 = 無條件通過。單一項目可以直接寫字串不用包 list。

**物品與旗標共用同一個命名空間** —— `require=["key"]` 會同時查物品欄和旗標，
有一邊算「有」就算通過。寫條件時不用記住每個 key 屬於哪一類，
代價是物品與旗標不能取同樣的名字。

`check` 收到的是 `StateView`（唯讀），可用 `has` / `has_item` / `has_flag` /
`item_count` / `event_count` / `is_event_dead`。

### Effect

```renpy
Effect(
    give_items=["key", ("coin", 5)],   # 支援 (key, 數量)
    remove_items=["torch"],
    set_flags=["opened_drawer"],
    clear_flags=["is_hiding"],
    kill_events=["hall.ghost_warn"],   # 讓別的事件提前失效，可跨房間
    label="found_key",                 # 狀態改完才跑
)
```

六個欄位全都是改 `GameState`。執行順序由引擎固定（給物品 → 拿物品 → 設旗標 →
清旗標 → 殺事件 → 跑 label），因為它們彼此不相依，順序不影響結果。

**刻意沒有 `change_room` 和熱點顯隱**：換房間寫在 label 裡順序才自然；
熱點顯隱用 `Hotspot.condition` 由條件推導，才不會被「重新載入房間資料」洗掉。

### 進房事件

`Room` 的 `on_enter` 就是簡寫，內部轉成一個 `id` 為 `"房間名.on_enter"`、
`sequence=-1000`（排最前面）的無條件 Event。需要條件分支時直接用 `Room(events=[...])`。

### 狀態存在哪裡

觸發次數與死亡名單存在 `game_state.events`，**不在 Event 物件上**。
因為 Event 跟 Room 一樣是 `build_rooms()` 產生的靜態定義，
按「重新載入房間資料」時會被整個重建 —— 狀態記在物件上就會跟著歸零。

---

## 物品與物品欄

### 定義物品

`game/explore_demo/items.rpy`：

```renpy
init python:
    def build_items():
        items = {}

        items["key"] = Item(
            key="key",
            name="生鏽的鑰匙",
            description="一把沾滿鏽的舊鑰匙。\n看起來能開某個櫃子。",
            icon=None,       # 可以是圖片路徑或任何 displayable
            tag="鑰匙",       # 自訂分類，引擎不碰它
        )

        return items

define item_catalog = build_items()
```

**注意是 `define` 不是 `default`。** 物品目錄是純靜態定義，
玩家有幾把鑰匙記在 `GameState.inventory`，不在這裡。
用 `define` 就不會進存檔 —— 改了物品名稱或描述，連舊存檔都會馬上吃到新的。
用 `default` 的話會重蹈 `rooms` 的覆轍（改了定義要重開新遊戲才看得到）。

### 給予與檢查

```renpy
Effect(give_items=["key"])           # 給一個
Effect(give_items=[("coin", 5)])     # 給五個
Effect(remove_items=["torch"])       # 拿走

Condition(require=["key"])           # 檢查有沒有
Condition(check=lambda v: v.item_count("coin") >= 3)   # 檢查數量
```

### 撿取物品的完整寫法

```renpy
Hotspot(name="key_pickup", x=2400, y=620, label="🔑 生鏽的鑰匙",
        condition=Condition(forbid=["key"]),      # 撿走之後自動消失
        events=[
            Event(id="demo_room.pick_key",
                  effect=Effect(give_items=["key"], label="demo_pick_key")),
        ])

label demo_pick_key:
    "你撿起了一把生鏽的鑰匙。"
    return
```

`condition=Condition(forbid=["key"])` 這行是重點：**撿走之後熱點自動消失**，
不需要在 label 裡呼叫 `hide()`。讀舊存檔、按「重新載入房間資料」都不會
讓已經撿過的東西又冒出來，因為顯示與否完全由 `GameState` 推導。

### 物品欄畫面

`explore()` 已經 `use inventory_display` 了，會顯示在**右上角**
（左上角留給 F9 的 debug 面板）。

物品欄裡只存 key 與數量，畫面上的名稱與圖示都是即時查 `item_catalog`。
數量大於 1 時會顯示 `×N`。點一下物品會用翻頁視窗顯示它的 `description`。

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

**正確流程是兩步，順序不能反**（已實測確認）**：**

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
        on_click="demo_show_help")
```

---

## 自動化測試

`game/explore_demo/tests.rpy` 有十份測試，在 SDK 目錄下執行：

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
| `state_checks` | `InventoryState` / `FlagState` / `EventState` / `GameState` / `StateView` 的純邏輯 |
| `event_checks` | `Condition` 四種欄位、`Effect` 六種改動、`collect_events` 的排序／stop／死亡／trigger 過濾 |
| `inventory_flow` | 撿鑰匙 → 熱點自動消失 → 物品欄出現 → 開櫃子拿紙條 → 再點變空的 |
| `locked_without_key` | 同一個熱點在沒鑰匙時走另一條分支，且條件不符的事件不該被算成觸發過 |

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
