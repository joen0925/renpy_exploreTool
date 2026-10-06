# 開發者指南

怎麼用這套工具寫遊戲內容。引擎本身的說明、debug 面板、測試寫法在 [README.md](README.md)。

---

## 目錄

- [五分鐘做出一個房間](#五分鐘做出一個房間)
- [先搞懂三件事的分工](#先搞懂三件事的分工)
- [Room 房間](#room-房間)
- [Hotspot 互動點](#hotspot-互動點)
- [Event 事件](#event-事件)
- [Condition 條件](#condition-條件)
- [Effect 結果](#effect-結果)
- [Item 物品](#item-物品)
- [角色數值與死亡](#角色數值與死亡)
- [解謎關卡](#解謎關卡)
- [常見情境食譜](#常見情境食譜)
- [常見錯誤](#常見錯誤)

---

## 五分鐘做出一個房間

三步驟，每步都在 `game/explore_demo/` 底下（或你自己的內容目錄）。

**1. 寫房間檔案** `bedroom.rpy`

```renpy
init python:

    def build_bedroom():
        room = Room(
            name="bedroom",
            background="images/bg_bedroom.png",
            bg_width=3000,              # 背景圖的實際寬度，填錯鏡頭範圍就會錯
            on_enter="bedroom_enter",   # 第一次進來時講的話
        )

        room.add_hotspot(Hotspot(
            name="bed",
            x=1200, y=500,              # 背景圖座標，不是螢幕座標
            width=400, height=300,
            debug=True,                 # 開發時開著，看得到判定範圍
            on_click="bedroom_look_bed",
        ))

        return room


label bedroom_enter:
    "房間裡有股霉味。"
    return

label bedroom_look_bed:
    "床單皺成一團，像是有人剛離開。"
    return
```

**房間定義和它的 label 放同一個檔案。** 這樣要知道這個房間點下去會發生什麼，看一個檔案就夠。

**2. 註冊** — 打開 `rooms.rpy`，在 `build_rooms()` 裡加一行：

```renpy
rooms["bedroom"] = build_bedroom()
```

> 房間檔的檔名怎麼取都可以。房間清單用 `init 1 python:` 建立，
> 保證在所有房間檔都載入完之後才跑。**不要**把它改回 `default` 或 `define` ——
> 理由見 [README 的「什麼會進存檔，什麼不會」](README.md#什麼會進存檔什麼不會)。

**3. 用** — `$ change_room("bedroom")`

座標不知道怎麼填？進遊戲按 **F9** 開標點面板，滑鼠移到想放的位置按 **F10** 釘住，抄「釘住的房間座標」。

---

## 先搞懂三件事的分工

寫內容時你會一直碰到這三個問題，先分清楚：

| 問題 | 用什麼 |
|---|---|
| 這個東西**看不看得到**？ | `Hotspot.condition` |
| 點下去**發生什麼**？ | `on_click`（簡單）或 `events`（有分支） |
| 遊戲**記得什麼**？ | `GameState` — 物品、旗標、事件觸發次數 |

還有一條貫穿全部的原則：

> **Condition 只讀，Effect 只寫，劇情走 label。**

`Condition` 不能改任何東西（它每 16ms 被求值一次，有副作用會出大事）；
`Effect` 只改 `GameState`；講話、換房間、播動畫一律寫在 label 裡。

---

## Room 房間

```renpy
Room(
    name="kitchen",           # 必填。慣例跟 rooms 字典的 key 取一樣
    background="images/bg.png",   # 必填。圖片路徑或任何 displayable
    bg_width=2400,            # 背景圖實際寬度，預設 1920
    on_enter="kitchen_enter", # 進來時跑的 label
    on_enter_limit=1,         # on_enter 最多觸發幾次
    events=[...],             # 需要條件分支的進房事件
    music=None,               # 進房時播的 BGM。None = 不碰音樂，維持現在那首
    hotspots=[...],           # 也可以建立後用 add_hotspot() 一個個加
)
```

方法：`add_hotspot(h)` / `remove_hotspot(h)` / `get_hotspot(name)` / `add_event(e)`

### on_enter 與 on_enter_limit

```renpy
Room(name="kitchen", on_enter="kitchen_enter")                   # 只第一次進來講
Room(name="hall",    on_enter="hall_enter", on_enter_limit=None) # 每次進來都講
Room(name="cave",    on_enter="cave_enter", on_enter_limit=2)    # 前兩次都講
```

`on_enter` 是簡寫，內部會轉成一個 Event：

```renpy
Event(id="kitchen.on_enter", effect=Effect(label="kitchen_enter"),
      sequence=-1000, limit=1)
```

`sequence=-1000` 表示它排在這個房間所有事件的最前面 —— 開場白通常要先講完，才輪到其他條件事件。

### 進房要分支的時候

`on_enter` 沒有條件。要「看過鬼之後進來講不一樣的話」就得用 `events`：

```renpy
Room(
    name="hall",
    background="images/bg_hall.png",
    events=[
        Event(id="hall.first_time",
              effect=Effect(label="hall_first_visit"),
              sequence=10, stop=True),           # 只有第一次會跑到這

        Event(id="hall.after_ghost",
              condition=Condition(require=["saw_ghost"]),
              effect=Effect(label="hall_scared"),
              sequence=20, limit=None),

        Event(id="hall.normal",
              effect=Effect(label="hall_normal"),
              sequence=30, limit=None),
    ],
)
```

`on_enter` 和 `events` 可以同時用，`on_enter` 產生的那個永遠排最前面。

### Room 沒有 condition

`Hotspot` 有 `condition`（控制看不看得到），但 **`Room` 沒有** ——
房間不存在「顯示與否」的問題，你不會在畫面上「看到一個房間」。

要做條件判斷有兩個位置：

```renpy
# 1. 房間內的事件：進來時依狀態講不同的話
Room(name="hall", events=[
    Event(id="hall.with_lamp",
          condition=Condition(require=["lamp"]),   # ← 這裡
          effect=Effect(label="hall_lit")),
])

# 2. 進入的那一端：沒鑰匙就進不去
Hotspot(name="door", label="🚪 門", events=[
    Event(id="corridor.enter_hall",
          condition=Condition(require=["key"]),    # ← 或這裡
          effect=Effect(label="go_to_hall"), stop=True),
    Event(id="corridor.hall_locked",
          effect=Effect(label="hall_is_locked"), limit=None),
])
```

「這個房間現在能不能進去」屬於**門的判斷**，不是房間的判斷 ——
擋在門那端，玩家才會知道為什麼進不去。

---

## Hotspot 互動點

```renpy
Hotspot(
    name="locker",        # 必填。get_hotspot("locker") 要用
    x=500, y=520,         # 必填。背景圖座標

    # --- 外觀，三選一 ---
    label="🚪 上鎖的櫃子",  # A. 文字/emoji（不需要美術素材）
    idle="images/locker.png", hover="images/locker_glow.png",  # B. 圖片
    # C. 三個都不填 = 隱形熱點，配合 debug=True 開發

    width=240, height=200,   # 判定範圍，不填預設 100×100
    debug=False,             # True 會畫半透明紅框標出判定範圍

    # --- 行為，二選一 ---
    on_click="look_locker",  # 簡單：每次點都跑這個 label
    events=[...],            # 有分支：見下面 Event

    # --- 顯示條件 ---
    condition=Condition(forbid=["key"]),   # 條件不成立就不顯示

    # --- 其他 ---
    sound="audio/click.ogg",  # 點擊音效
    visible=True,             # 手動開關，與 condition 是 AND 關係
    tag=None, examine=None, data=None,   # 自訂欄位，引擎不碰
    label_size=28, label_color="#e67e22", label_hover_color="#ffffff",
)
```

方法：`show()` / `hide()` / `add_event(e)`

> 沒有「可以點／不能點」的開關。要控制熱點能不能互動請用 `condition` ——
> 條件是由狀態推導的，reload 與讀存檔都會自己算對；
> 手動旗標要靠「當初有沒有執行到」來維持，會遇到跟 `hide()` 一樣的問題。

### 外觀三選一的差別

```renpy
# A. 文字熱點 —— 做原型最快，不用等美術
Hotspot(name="key", x=800, y=600, label="🔑 撿起鑰匙", on_click="pick_key")

# B. 圖片熱點 —— idle/hover 會被縮放成 width × height
Hotspot(name="lamp", x=800, y=600, width=200, height=300,
        idle="images/lamp.png", hover="images/lamp_glow.png",
        on_click="look_lamp")

# C. 隱形熱點 —— 背景圖上一塊看不見的可點區域
Hotspot(name="door", x=1500, y=400, width=300, height=600,
        debug=True,          # 開發時看得到，上線改 False
        on_click="open_door")
```

### on_click 還是 events？

**點下去每次都做同一件事** → `on_click`

```renpy
Hotspot(name="sign", x=520, y=500, label="🪧 看板", on_click="read_sign")
```

**點下去要看狀態決定做什麼** → `events`

```renpy
Hotspot(name="door", x=800, y=400, label="🚪 門",
        events=[
            Event(id="hall.door_open",
                  condition=Condition(require=["key"]),
                  effect=Effect(label="open_door"),
                  sequence=10, stop=True),
            Event(id="hall.door_locked",
                  effect=Effect(label="door_locked"),
                  sequence=20, limit=None),
        ])
```

兩個可以同時存在（`events` 先跑、`on_click` 後跑），但多數情況只需要其中一個。

### condition 控制顯示

**用條件推導，不要用 `hide()`。**

```renpy
# 好：撿走鑰匙後自動消失
Hotspot(name="key_pickup", x=2400, y=620, label="🔑 鑰匙",
        condition=Condition(forbid=["key"]),
        events=[Event(id="room.pick_key",
                      effect=Effect(give_items=["key"], label="pick_key"))])

# 不好：要自己記得在每條路徑上呼叫 hide()
label pick_key:
    $ current_room.get_hotspot("key_pickup").hide()   # 別這樣
```

差別在於**冪等**：條件寫法不管讀哪個存檔、reload 幾次都一致，
因為顯示與否完全由 `GameState` 推導。`hide()` 則要靠「當初有沒有正確執行過」，
一旦某條路徑漏掉就永遠不一致。

---

## Condition 條件

「什麼時候成立」。它同時用在兩個地方：

```renpy
Hotspot(..., condition=Condition(...))   # 這個熱點看不看得到
Event(..., condition=Condition(...))     # 這個事件要不要執行
```

```renpy
Condition(
    require=["key", "map"],          # 全部都要有（AND）
    require_any=["axe", "crowbar"],  # 至少要有一個（OR）
    forbid=["saw_ghost"],            # 全部都不能有（NOT）
    check=lambda v: v.item_count("coin") >= 3,   # 前三個表達不了時用
)
```

四個欄位都不填 = 無條件通過。單一項目可以直接寫字串：`require="key"`。

### 物品與旗標共用命名空間

```renpy
Condition(require=["key"])            # 查得到物品欄裡的鑰匙
Condition(require=["locker_opened"])  # 也查得到旗標
```

`require` 會同時查物品欄和旗標，有一邊算「有」就算通過。
寫條件時不用記住每個 key 屬於哪一類。

**代價是物品與旗標不能取同樣的名字。**

### 要判斷數量

`require` 只查「有沒有」，不查數量。要判斷數量用 `check`：

```renpy
Condition(check=lambda v: v.item_count("coin") >= 5)
```

**`require=[("coin", 5)]` 不會運作** —— 它會拿整個 tuple 去查 key，
永遠找不到，條件恆假而且不會報錯。

### check 逃生艙

`check` 收到的是 `StateView`（唯讀），可用這些方法：

```renpy
v.has(key)              # 物品或旗標，有一邊就算
v.has_item(key)
v.has_flag(key)
v.item_count(key)
v.item_keys()
v.event_count(event_id)
v.is_event_dead(event_id)
```

```renpy
Condition(check=lambda v: v.item_count("coin") >= 3)
Condition(check=lambda v: len(v.item_keys()) == 0)      # 兩手空空
```

**`check` 裡絕對不能改狀態。** 它會在畫面每次重繪時被呼叫，每秒 60 次。

---

## Event 事件

「在什麼時機、滿足什麼條件、就做什麼事」。

```renpy
Event(
    id="kitchen.locker_open",   # 必填，全域唯一
    condition=Condition(...),   # None = 無條件
    effect=Effect(...),         # None = 什麼都不做
    sequence=10,                # 同一個掛載點內的順序，小的先跑
    limit=1,                    # 最多觸發幾次，用完自動死亡。None = 無限
    stop=False,                 # 觸發後不再檢查後面的
    chance=None,                # 觸發機率 0.0~1.0。None = 一定觸發，見下面
    trigger=None,               # 觸發時機。一般不用填，見下面
)
```

### 第 N 次才發生（次數累積）

不靠計時器製造意外感的做法：**數玩家的動作次數，不數秒數**。
次數本來就記在 `GameState.events` 裡，所以存檔、倒帶天生就對，不需要任何額外機制。

```renpy
# 計數器：只負責數，永遠不死
room.add_event(visit_counter("attic.visits"))

# 第 3 次進來才觸發
room.add_event(Event(
    id="attic.third_visit_scare",
    condition=Condition(check=count_at_least("attic.visits", 3)),
    effect=Effect(set_flags=["attic_scared"], label="attic_third_visit"),
    limit=1,
))
```

掛在 `Room.events` 是數進房次數，掛在 `Hotspot.events` 是數點擊次數 ——
跟一般 Event 一樣，時機由掛載位置決定。

**為什麼要一個專門的計數器，不能直接數 `on_enter`**：
`on_enter` 的 `limit` 就是 `on_enter_limit`（預設 1），開場白講完一次就死亡，
而死掉的 Event 連觸發次數都不會再記 —— 次數永遠停在 1。

**`visit_counter` 幫你擋掉的坑**：它的 `sequence` 是 -900，比一般事件的 0 小，
所以計數器一定先跑。派發是「跑完一個才換下一個」（套用 Effect、記錄次數，
才輪到下一個），計數器先把這次記進去、條件才求值 —— 所以「第 3 次」
就是真的第 3 次。順序反過來的話會變成第 4 次才觸發，而這種差一次的錯誤
在遊戲裡幾乎看不出來，只會覺得怪。

`count_at_least()` 是純讀取的，所以掛在 `Hotspot` 的顯示條件上（每幀求值）也安全：

```renpy
# 來過三次以上才看得到的東西
Hotspot(name="scratch", x=800, y=400, label="🩸 牆上的抓痕",
        condition=Condition(check=count_at_least("attic.visits", 3)))
```

### 機率觸發（偶爾才發生）

不靠計時器製造意外感的第二種做法：**骰機率**。
玩家不知道哪一次會中獎，所以「突然」的感覺跟計時器很接近，
但骨子裡完全是離散事件，不需要世界時鐘。

機率事件**要兩個一組**：

```renpy
Hotspot(name="wardrobe", x=1600, y=620, label="🚪 破舊的衣櫃",
        events=[
            # 骰中：演出 + stop 擋掉後面那個
            Event(id="attic.wardrobe_scare",
                  sequence=10, chance=0.25, limit=None, stop=True,
                  effect=Effect(label="attic_wardrobe_scare")),

            # 保底：骰不中時講一句「什麼都沒有」
            Event(id="attic.wardrobe_empty",
                  sequence=20, limit=None,
                  effect=Effect(label="attic_wardrobe_empty")),
        ])
```

**保底那個一定要寫。** 少了它，骰不中的時候點下去完全沒反應，
玩家會以為這個熱點壞了。

**骰輸「不算觸發過」**：次數不會 +1，`limit` 也不會被消耗，跟條件不符同一個待遇。
所以 `chance=0.25, limit=1` 的意思是「總共只會發生一次，但要骰中才算」——
而不是「骰一次就用完了」。這個設計沒有的話，`limit=1` 的機率事件
第一次骰輸就死亡，玩家永遠遇不到它。

**機率不是百分比**：25% 要寫 `0.25`。填 `25` 會在建立房間時直接報錯，
不會安靜地變成「永遠觸發」。

**不能寫進 `Hotspot.condition`。** 機率只能掛在 `Event` 上，這是刻意的限制：
熱點的顯示條件每幀都會求值（探索畫面每 16ms 重繪一次），
在那裡骰機率的話熱點會瘋狂閃爍，每秒還燒掉 60 個亂數與 60 個倒帶檢查點。
`Event.chance` 只在派發當下骰一次。

**倒帶是可重現的。** 用的是 `renpy.random`（不是 Python 內建的 `random`）——
它產生的數字會被記進倒帶紀錄，倒帶時照原順序重新發一次，
所以玩家倒帶回去重玩，骰出來的結果跟上次一樣，不會變成「倒帶大法刷到中獎」。

### trigger 是什麼（通常你不用填）

`trigger` 決定這個 Event 在**什麼時機**被檢查。

**不填的話由掛載位置自動決定**，這也是絕大多數情況：

| 掛在哪 | 自動採用的時機 |
|---|---|
| `Room.events` | `ENTER_ROOM`（進入房間時） |
| `Hotspot.events` | `CLICK_HOTSPOT`（點擊熱點時） |

所以下面兩種寫法完全一樣：

```renpy
Room(name="hall", events=[Event(id="hall.x", ...)])
Room(name="hall", events=[Event(id="hall.x", trigger=TriggerType.ENTER_ROOM, ...)])
```

`TriggerType` 定義了七種時機，但**目前只有上面兩種真的會被派發**：

```renpy
TriggerType.ENTER_ROOM        # ✓ 已實作
TriggerType.CLICK_HOTSPOT     # ✓ 已實作

TriggerType.EXIT_ROOM         # 預留：離開房間（change_room 還沒有離開的鉤子）
TriggerType.INTERACT          # 預留：語意還沒定義
TriggerType.QUEST_COMPLETED   # ┐
TriggerType.EVENT_COMPLETED   # │ 預留：由 Effect 改完狀態反過來觸發的「衍生事件」
TriggerType.ITEM_OBTAINED     # ┘ 需要一整套 event bus，還沒做
```

**那為什麼要留這個欄位？** 因為之後接上 `EXIT_ROOM` 時，
同一個 `Room.events` 清單裡會同時有進房和離房的事件，那時就需要區分：

```renpy
Room(name="hall", events=[
    Event(id="hall.welcome", ...),                                  # 進來時
    Event(id="hall.footsteps", trigger=TriggerType.EXIT_ROOM, ...), # 離開時
])
```

現在填了預留的那五種不會出錯，但**永遠不會被觸發**，因為沒有東西會派發它們。

### trigger 實際做的事：過濾

派發的時候（進房或點擊），引擎只會檢查 **trigger 符合這次時機**的 Event，
其餘的連條件都不算，直接跳過。

所以 trigger 填錯的後果是**那個 Event 永遠不會執行，而且不會有任何錯誤訊息**。

```renpy
# ✗ 掛在 Room 裡卻標成點擊 —— 永遠不會觸發
#   因為進房時只派發 ENTER_ROOM，這個被過濾掉了
Room(name="hall", events=[
    Event(id="hall.x", trigger=TriggerType.CLICK_HOTSPOT, ...),
])

# ✗ 掛在 Hotspot 裡卻標成進房 —— 同樣永遠不會觸發
Hotspot(name="door", events=[
    Event(id="hall.y", trigger=TriggerType.ENTER_ROOM, ...),
])
```

**「進房事件」與「點擊事件」不能混掛。** 房間的事件掛在 `Room.events`，
熱點的事件掛在 `Hotspot.events`，各自派發各自的。
`Room` 沒有辦法掛點擊事件，因為房間本身不能被點。

### 同一件事要在進房和點擊時都發生

寫兩個 Event 指向同一個 label 就好 —— **id 必須不同**：

```renpy
# 房間定義
Room(name="hall", events=[
    Event(id="hall.check_lamp_on_enter",
          condition=Condition(require=["lamp"]),
          effect=Effect(label="hall_lamp_glows"),
          limit=None),
])

# 熱點定義
Hotspot(name="lamp", label="🕯 燈", events=[
    Event(id="hall.check_lamp_on_click",
          condition=Condition(require=["lamp"]),
          effect=Effect(label="hall_lamp_glows"),
          limit=None),
])
```

兩個 Event 有各自的觸發次數與死亡狀態（因為 id 不同），
所以「進房算一次、點擊算一次」是分開計算的。
如果你要的是「總共只發生一次」，那應該用旗標：
其中一個 Effect 設 `set_flags=["lamp_seen"]`，兩個 Condition 都加 `forbid=["lamp_seen"]`。

### id 一定要唯一

`id` 是 `GameState.events` 記錄觸發次數與死亡狀態用的 key。
**兩個 Event 撞名會共用狀態**，症狀是「另一個房間的事件莫名其妙不觸發了」，很難查。

慣例用 `"房間名.事件名"`：

```renpy
"kitchen.locker_open"
"hall.ghost_warn"
"demo_room.pick_key"
```

### 派發的順序

一次派發（進房或點擊）會這樣跑：

```
依 sequence 排序（小的先）
   ↓
跳過已死亡的（連條件都不算）
   ↓
條件不通過 → 跳過，而且不算觸發過
   ↓
條件通過 → 執行 Effect → 收集 label → 觸發次數 +1
   ↓
次數達到 limit → 這個 Event 死亡
   ↓
如果 stop=True → 不再檢查後面的
   ↓
全部跑完 → 依序執行收集到的 label
```

兩個重點：

**條件不符不算觸發過。** 玩家沒鑰匙點了門，`locker_open` 不會消耗掉次數，
之後拿到鑰匙再點還是能開。

**符合條件的會全部執行**，除非某個設了 `stop=True`。

### limit 與死亡

```renpy
limit=1      # 預設。講一次就結束（開場白、撿東西）
limit=None   # 無限次（「鎖住了」這種每次都要講的）
limit=3      # 前三次
```

死掉的事件會被直接跳過，連條件都不求值 —— 所以 sequence 的檢查成本會隨遊戲進行遞減。

也可以用 `Effect(kill_events=[...])` 讓別的事件提前死亡，見下面。

---

## Effect 結果

```renpy
Effect(
    give_items=["key", ("coin", 5)],   # 給物品，支援 (key, 數量)
    remove_items=["torch"],            # 拿走物品
    set_flags=["opened_drawer"],       # 設旗標
    clear_flags=["is_hiding"],         # 清旗標
    kill_events=["hall.ghost_warn"],   # 讓別的事件永久失效，可跨房間

    stats={"hp": -1},                  # 角色數值的增減量
    actor="player",                    # stats 要改到誰身上。有 stats 就必填

    label="found_key",                 # 狀態改完才跑這個 label
)
```

除了 `label` 之外全都是改 `GameState`。執行順序由引擎固定，你不用管
（給物品 → 拿物品 → 設旗標 → 清旗標 → 殺事件 → 改數值 → 跑 label）。

### 為什麼沒有 change_room 和 hide_hotspot

**換房間寫在 label 裡：**

```renpy
label go_kitchen:
    "你推開門走進廚房。"
    $ change_room("kitchen")
    return
```

這樣「先講話再換過去」的順序才自然。放進 Effect 反而要多定一條規則。

**熱點顯隱用 `Hotspot.condition`：**

```renpy
Hotspot(..., condition=Condition(forbid=["key"]))
```

因為熱點是 Room 物件上的狀態，而 Room 會被「重新載入房間資料」重建 ——
命令式改的顯隱會消失，條件推導的不會。

---

## Item 物品

在 `items.rpy` 定義：

```renpy
init python:
    def build_items():
        items = {}

        items["key"] = Item(
            key="key",                       # 條件判斷用的就是這個
            name="生鏽的鑰匙",                 # 物品欄顯示的名稱
            description="一把沾滿鏽的舊鑰匙。",  # 點物品時顯示
            icon=None,                       # 圖片路徑或任何 displayable
            tag="鑰匙",                       # 自訂分類，引擎不碰
        )

        return items

define item_catalog = build_items()
```

**注意是 `define` 不是 `default`。** 物品目錄是靜態定義，用 `define` 才不會進存檔 ——
改了名稱或描述，連舊存檔都會馬上吃到新的。

### dict key 與 Item.key 必須一致

```renpy
items["coin10"] = Item(key="coin10", ...)   # ✓
items["coin10"] = Item(key="coin", ...)     # ✗ 啟動時直接報錯
```

真正被使用的是 **dict 的 key** —— `give_items` / `require` / `item_def` 查的都是它，
`Item.key` 只是給人看的。兩邊不一致的話遊戲照跑、物品欄也顯示正常，
只有在你照著 `Item.key` 寫條件時才會發現「明明有這個物品卻查不到」。

`build_items()` 最後包一層 `validate_item_catalog(items)` 就會在啟動時擋下來：

```renpy
def build_items():
    items = {}
    ...
    return validate_item_catalog(items)
```

物品欄（`InventoryState`）只存 `{key: 數量}`，名稱圖示都是即時查目錄。
畫面在右上角，已經自動掛好了，數量大於 1 會顯示 `×N`，點一下會用翻頁視窗顯示描述。

---

## 角色數值與死亡

血量、憤怒值、體力、電池量 —— 這些都是「綁在某個角色身上的整數計數器」，
統一存在 `GameState.actors` 裡，用同一套語法。

### 設定初始數值

在 `actors.rpy` 定義，這是**唯一**要改數字的地方：

```renpy
define actor_start_stats = {
    "player":      {"hp": 5},
    "annie_ghost": {"hp": 3, "rage": 0},
}

label init_actor_stats:
    python:
        for _actor, _stats in actor_start_stats.items():
            for _stat, _value in _stats.items():
                game_state.actors.set(_actor, _stat, _value)
    return
```

然後在 `label start` 呼叫，**要排在第一次 `change_room` 之前** ——
進房事件本身就可能扣血：

```renpy
label start:
    call init_actor_stats from _call_init_actor_stats
    show screen explore
    $ change_room("demo_room")
    jump explore_loop
```

> **沒有設定 `hp` 的角色是無敵的。** 引擎不給任何預設血量，
> 所以會被打死的角色一定要出現在上面那張表裡。
> 這個失敗方向是刻意選的：忘了初始化的症狀是「打不死」，
> 比「一開場就死」好查太多。

### 改數值

```renpy
Effect(actor="player",      stats={"hp": -1})                 # 主角扣一滴血
Effect(actor="annie_ghost", stats={"rage": +1})               # 安妮的憤怒值 +1
Effect(actor="player",      stats={"battery": -10, "hp": -1}) # 一次改多個
```

三件要記得的事：

1. **`actor` 一定要寫。** 沒寫會在遊戲啟動時直接報錯 ——
   `Effect(stats={"hp": -1})` 看不出來扣的是誰的血，
   而扣錯角色是那種「遊戲照跑、幾天後才發現」的錯誤。
2. **`stats` 是增減量，不是設定值。** 同一個 Effect 套兩次會累積。
3. **一個 Effect 只對一個角色。** 要同時改兩個角色就寫兩個 Event。
4. **夾在 0 以上。** 扣過頭不會變負數，所以不會有「hp 跑到 -5、吃了藥加 1 還是死的」這種 bug。

### 查數值（寫條件用）

```renpy
# 瀕死才會出現的熱點
Hotspot(..., condition=Condition(check=lambda s: s.stats("player", "hp") <= 1))

# 安妮夠生氣才出現
Hotspot(..., condition=Condition(check=lambda s: s.stats("annie_ghost", "rage") >= 3))

# 鬼還沒被解決
Condition(check=lambda s: s.is_alive("annie_ghost"))
```

查不到的數值回傳 `0`，跟 `item_count()` 同一個約定。

### 死亡

引擎只認得一個數值名稱：**`hp`**。歸零就判定死亡，其他名稱
（`rage` / `battery` / `stamina`）歸零就只是歸零，要有後果請自己用 `Condition` 接。

死亡 label 由你宣告，引擎不寫死名字：

```renpy
define on_player_death = "game_over"

label game_over:
    scene black with fade
    "你的意識沉了下去……"
    "GAME OVER"
    $ renpy.full_restart()      # 回主選單
```

> 不能寫 `$ MainMenu(confirm=False)` —— `MainMenu` 是一個**畫面動作（Action）**類別，
> 那樣寫只是「建立一個動作物件然後丟掉」，什麼都不會發生。
> 動作是給 screen 的 `action=` 用的（`textbutton "主選單" action MainMenu()`）。
> 在 label 裡要直接執行，用 `renpy.full_restart()`。

**只有主角（`"player"`）死亡會跳過去。** 鬼死掉引擎不做任何事，
後果由你的 `Condition` 表達。

### 死亡的時機：對話會完整演完

```renpy
Event(id="attic.annie", effect=Effect(actor="player", stats={"hp": -1}, label="annie_attack"))

label annie_attack:
    "有什麼東西從你背後掠過。"
    show ghost with vpunch
    "你的手臂上多了一道抓痕。"
    return
    # ↑ 這裡跑完，引擎才檢查 hp<=0 → jump game_over
```

死亡檢查是在**整串事件的 label 都跑完之後**才做的，
所以「鬼撲上來」的演出不會被扣血硬生生打斷。

> ⚠️ **死亡 label 是被 `jump` 進來的，不是 `call`** ——
> 死掉不該回到探索迴圈。所以它**不會 return 回來**，要自己收尾：
> `renpy.full_restart()`、`jump` 回檢查點、或跳到你自己的結局畫面。
> 寫 `return` 的話會跳回一個你意想不到的地方。

### 把數值顯示給玩家看

狀態欄在**左上角**，已經自動掛好了。要顯示哪些數值在 `actors.rpy` 宣告：

```renpy
define player_status_display = [
    {"stat": "hp",      "icon": "❤️"},
    {"stat": "battery", "icon": "🔦", "name": "電量"},
]
```

| 欄位 | 說明 |
|---|---|
| `stat` | 要顯示哪個數值 |
| `icon` | 前面的圖示，emoji 就夠，不需要美術素材 |
| `name` | 圖示後面的文字說明，可省略 |

由上往下依這個順序排。**只有列在這裡的會顯示** ——
所以 `annie_ghost` 的 `rage` 不會不小心漏給玩家看到。

而且列在這裡但**沒被設定過**的數值會自動跳過。
所以玩家還沒拿到手電筒時，畫面上不會出現一列「🔦 0」；
`Effect(actor="player", stats={"battery": +100})` 給了電池之後才會冒出來。

沒宣告 `player_status_display` 的話狀態欄整個不顯示，不會出錯。

> 狀態欄跟 F9 的 debug 標點面板都在左上角，會疊在一起。
> 那是刻意的 —— debug 面板只在開發時開，正式環境用不到。

### 讓立繪跟著數值變

這一段 Ren'Py 原生就能做，引擎不介入：

```renpy
image annie_ghost = ConditionSwitch(
    "game_state.actors.is_dead('annie_ghost')",          "annie_gone.png",
    "game_state.actors.get('annie_ghost', 'rage') >= 5", "annie_furious.png",
    "True",                                              "annie_calm.png",
)
```

之後只要 `show annie_ghost`，憤怒值一改立繪自己就換。
條件字串會被頻繁求值，所以**只能讀不能寫** —— 跟 `Hotspot.condition` 同一條紀律。

---

## 解謎關卡

### 先確認你真的需要它

**「打開抽屜 → 裡面有小物可以拿」不需要 Puzzle。** 那用一個近景房間就好：

```renpy
Room(name="drawer", background="images/drawer_open.png", bg_width=1920)
```

`bg_width` 等於螢幕寬 → 鏡頭不會捲動 → 看起來就是定格特寫。
熱點、hover 發光、拿了就消失、再往下開一層，全部是現成的，**零行新程式碼**。

**只有「有臨時內部狀態」的關卡才需要 Puzzle** —— 密碼鎖按到一半的數字、
拼圖現在的排列、連線連到一半。那個狀態不是遊戲進度，不該進存檔。

### 寫一個密碼鎖

在 `puzzles.rpy` 定義：

```renpy
init python:
    def build_puzzles():
        puzzles = {}

        puzzles["kitchen_safe"] = KeypadPuzzle(
            code="4721",
            title="保險箱",
            hint="門把旁邊有一個四位數的鍵盤。",

            on_success=Effect(set_flags=["safe_opened"],
                              give_items=["documents"],
                              label="kitchen_safe_opens"),

            # 答錯的代價。不填就是答錯沒事，可以一直重試
            on_failure=Effect(actor="player", stats={"hp": -1},
                              label="kitchen_safe_shock"),
        )

        return puzzles

define puzzle_catalog = build_puzzles()
```

熱點照舊走 label，**不給 `Hotspot` 加 `puzzle` 欄位**：

```renpy
Hotspot(name="safe", x=1400, y=300, label="🔒 保險箱",
        condition=Condition(forbid=["safe_opened"]),   # 開過就消失
        on_click="kitchen_open_safe")

label kitchen_open_safe:
    call run_puzzle("kitchen_safe") from _call_kitchen_open_safe
    return
```

**傳名稱不傳物件** —— label 參數會進呼叫堆疊，呼叫堆疊會進存檔。
關卡是靜態定義，跟房間與物品目錄一樣不該進存檔。

### 三種結果

| 玩家做了什麼 | 引擎做什麼 |
|---|---|
| 密碼正確 | 套用 `on_success` |
| 密碼錯誤 | 套用 `on_failure`（沒填就什麼都不做） |
| 按 ✕ 或 ESC 關掉 | **什麼都不做**，不算失敗 |

結果走的是既有的 `Effect` 與 `run_event_labels`，所以
**`on_failure` 扣血扣到 0 會自動接上 `on_player_death`**，不用另外寫。

答錯就關掉視窗，要重試再點一次熱點。刻意不做「視窗留著一直試」——
因為 Effect 要跑 label，label 沒辦法在視窗開著時跑，
那樣「答錯扣一滴血」這種即時代價就做不出來。

### 寫一個九宮格解鎖

跟手機的圖形鎖一樣，按住一個點拖曳連線，放開送出：

```renpy
puzzles["old_phone"] = PatternPuzzle(
    pattern="1235789",       # 也可以寫 [1, 2, 3, 5, 7, 8, 9]
    title="舊手機",
    hint="螢幕上的指紋油漬，看起來像一個 Z。",
    on_success=Effect(set_flags=["phone_unlocked"], label="phone_unlocked"),
    on_failure=None,         # 畫錯沒代價，可以一直重試
)
```

點的編號由左到右、由上到下：

```
1   2   3
4   5   6
7   8   9
```

規則照 Android：

| 規則 | 說明 |
|---|---|
| 從點上開始 | 按在空白處拖不算數 |
| 點不能重複 | 已經連過的點會被略過 |
| **直線跨過的點會自動連上** | 從 1 拖到 3，中間的 2 一定會被連到 |
| 太短不算 | 少於 `min_length`（預設 4）個點就放開 = 手滑，視窗不關、不算失敗 |

> ⚠️ **第三條的後果：有些圖形畫不出來。**
>
> `pattern=[1, 3, 6, 9]` 照著畫實際會變成 `[1, 2, 3, 6, 9]`，玩家永遠解不開。
> `PatternPuzzle` 建立時會把圖形重播一次檢查，**畫不出來就在遊戲啟動時直接報錯**：
>
> ```
> 圖形鎖 [1, 3, 6, 9] 畫不出來 —— 照著畫實際會變成 [1, 2, 3, 6, 9]。
> ```

### 做新的關卡類型

不要繼承。`run_puzzle` 只認四個屬性（鴨子型別）：

| 屬性 | 說明 |
|---|---|
| `screen` | 要顯示哪個 screen（字串），那個 screen 會收到 `puzzle=自己` |
| `on_success` | 答對時套用的 `Effect` |
| `on_failure` | 答錯時套用的 `Effect`，可以是 `None` |
| `pausable` | 解謎途中世界要不要暫停（**尚未生效**，等 TIMER） |

任何有這四個屬性的物件都能跑。寫一個普通類別 + 一個 screen 就好，引擎不用改。

> ⚠️ **一定會踩的地雷：screen 的回傳值不能用 `Return()`**
>
> Ren'Py 的 `Return()` 不帶參數時**回傳的是 `True` 不是 `None`**：
>
> ```python
> def __call__(self):
>     if self.value is None:
>         ...
>         return True        # ← 這裡
>     else:
>         return self.value
> ```
>
> 因為畫面動作回傳 `None` 代表「什麼都沒發生、互動不要結束」。
>
> 所以關閉鈕寫 `Return()` 的話，如果契約是「True = 答對」，
> **玩家一按 ✕ 就直接過關了**。這個 bug 真的發生過。
>
> 一律用具名常數：`Return(PUZZLE_SOLVED)` / `Return(PUZZLE_FAILED)` /
> `Return(PUZZLE_CLOSED)`。收到任何其他值一律當成「什麼都不做」。
>
> 自訂 displayable（像九宮格的 `PatternPad`）也一樣：`event()` 回傳非 `None`
> 就會結束互動，回傳值一律用這三個常數。

> **倒帶不用自己處理。** `run_puzzle` 已經在關卡畫面期間 `renpy.suspend_rollback(True)`，
> 新的關卡 screen 不用再做一次。
>
> 但如果你**自己**寫了別的 modal `call screen`（不透過 `run_puzzle` 或 `show_pages`），
> 就要記得包起來 —— 不然玩家關掉視窗後按「返回」會倒帶回視窗裡，
> 而 modal 視窗擋住了 quick menu 的「返回」鈕，玩家會卡在裡面出不去。

---

## 常見情境食譜

### 只講一次的開場白

```renpy
Room(name="hall", background="...", on_enter="hall_enter")
```

### 每次進來都講

```renpy
Room(name="hall", background="...", on_enter="hall_enter", on_enter_limit=None)
```

### 撿一個物品，撿完熱點消失

```renpy
Hotspot(name="key_pickup", x=2400, y=620, label="🔑 生鏽的鑰匙",
        condition=Condition(forbid=["key"]),
        events=[
            Event(id="hall.pick_key",
                  effect=Effect(give_items=["key"], label="hall_pick_key")),
        ])

label hall_pick_key:
    "你撿起了一把生鏽的鑰匙。"
    return
```

### 上鎖的東西（三種狀態）

```renpy
Hotspot(name="locker", x=500, y=520, label="🚪 上鎖的櫃子",
        events=[
            # 有鑰匙：開鎖。stop 讓它不再檢查下面兩個，limit=1 所以只開一次
            Event(id="kitchen.locker_open",
                  condition=Condition(require=["key"]),
                  effect=Effect(set_flags=["locker_opened"],
                                give_items=["note"],
                                label="kitchen_open_locker"),
                  sequence=10, stop=True),

            # 還沒開過而且沒鑰匙：每次點都講
            Event(id="kitchen.locker_locked",
                  condition=Condition(forbid=["locker_opened"]),
                  effect=Effect(label="kitchen_locker_locked"),
                  sequence=20, limit=None),

            # 開過了
            Event(id="kitchen.locker_empty",
                  condition=Condition(require=["locker_opened"]),
                  effect=Effect(label="kitchen_locker_empty"),
                  sequence=30, limit=None),
        ])
```

`locker_locked` 的 `forbid=["locker_opened"]` 是關鍵 —— 沒有它的話，
開過之後 `locker_open` 死了，會掉下來講「鎖住了」，很怪。

### 需要湊齊多個物品

```renpy
Event(id="hall.ritual",
      condition=Condition(require=["candle", "knife", "book"]),
      effect=Effect(label="do_ritual"))
```

### 第 N 次進來才發生的事

```renpy
room.add_event(visit_counter("attic.visits"))
room.add_event(Event(id="attic.scare",
                     condition=Condition(check=count_at_least("attic.visits", 3)),
                     effect=Effect(label="attic_scare")))
```

詳見上面的「第 N 次才發生（次數累積）」。

### 偶爾才發生的事（機率）

```renpy
events=[
    Event(id="attic.wardrobe_scare", sequence=10, chance=0.25,
          limit=None, stop=True,
          effect=Effect(label="attic_wardrobe_scare")),

    # 保底：骰不中時要有反應，不然玩家以為壞了
    Event(id="attic.wardrobe_empty", sequence=20, limit=None,
          effect=Effect(label="attic_wardrobe_empty")),
]
```

詳見上面的「機率觸發（偶爾才發生）」。

### 任一把鑰匙都能開

```renpy
Event(id="hall.force_door",
      condition=Condition(require_any=["key", "lockpick", "crowbar"]),
      effect=Effect(label="force_the_door"))
```

### 事件連鎖：A 做完 B 才出現

```renpy
# A：剪斷電線
Event(id="hall.cut_wire",
      effect=Effect(set_flags=["wire_cut"], label="cut_the_wire"))

# B：電線剪斷後，門才打得開
Event(id="hall.open_gate",
      condition=Condition(require=["wire_cut"]),
      effect=Effect(label="gate_opens"))
```

**同一次派發裡也成立** —— 如果 A 和 B 掛在同一個熱點上，
A 的 Effect 設完旗標，B 的 Condition 馬上就看得到（依 `sequence` 順序）。

### 讓某個事件永久失效

```renpy
Event(id="hall.take_shortcut",
      effect=Effect(set_flags=["took_shortcut"],
                    kill_events=["cave.hidden_path"],   # 可以殺別房間的
                    label="shortcut_taken"))
```

### 進房後條件式地講不同的話

```renpy
Room(name="hall", background="...",
     events=[
         Event(id="hall.with_lamp",
               condition=Condition(require=["lamp"]),
               effect=Effect(label="hall_lit"),
               sequence=10, stop=True, limit=None),

         Event(id="hall.dark",
               effect=Effect(label="hall_dark"),
               sequence=20, limit=None),
     ])
```

### 彈出翻頁視窗

```renpy
Hotspot(name="notice", x=1000, y=300, label="📖 讀說明書",
        on_click="show_notice")

define NOTICE_PAGES = [
    {"title": "第一頁", "text": "內容。\n用 \\n 換行。"},
    {"title": "第二頁", "text": "三個欄位都可以省略。", "img": "images/page.png"},
]

label show_notice:
    call show_pages(NOTICE_PAGES)
    return
```

視窗是 modal，開著時點不到底下的熱點。玩家用底部按鈕、右上 ✕ 或 ESC 關閉。
只有一頁時翻頁按鈕會自動隱藏。

### 讀過說明書之後才會出現的東西

把「讀過了」記成旗標，別的地方就能拿來當條件：

```renpy
Hotspot(name="notice", label="📖 讀說明書",
        events=[
            Event(id="hall.read_notice",
                  effect=Effect(set_flags=["read_notice"], label="show_notice")),
        ])

Hotspot(name="secret_switch", label="🔘 開關",
        condition=Condition(require=["read_notice"]),   # 讀過才看得到
        on_click="press_switch")
```

---

## 常見錯誤

**`Room` 沒有 `on_click`，`Hotspot` 沒有 `on_enter`**

```renpy
Room(name="kitchen", on_click="...")      # ✗
Room(name="kitchen", on_enter="...")      # ✓ 進房觸發

Hotspot(name="door", on_enter="...")      # ✗
Hotspot(name="door", on_click="...")      # ✓ 點擊觸發
```

**在熱點上直接用 `Jump()`**

會跳過整套畫面處理，熱點按鈕不會被收起來，對話會卡住。
用 `on_click="label名"`，畫面切換是自動的。

**兩個 Event 用同樣的 id**

它們會共用觸發次數與死亡狀態。慣例用 `"房間名.事件名"` 就不太會撞。

**在 `Condition` 的 `check` 裡改狀態**

它每秒被呼叫 60 次，會把存檔改爛。要改狀態請用 `Effect`。

**改了房間定義卻沒生效**

`rooms` 會存進存檔。改完座標要**先按 Shift+R，再按 debug 面板的「重新載入房間資料」**，
兩步都要做。詳見 [README](README.md#改完座標怎麼讓它生效)。

**`bg_width` 沒填對**

鏡頭會掃不到背景右邊，或是掃過頭出現黑邊。

**熱點座標填成螢幕座標**

`x` / `y` 是**背景圖座標**。外層容器已經統一做過鏡頭位移，不要自己再加 `camera.offset`。
