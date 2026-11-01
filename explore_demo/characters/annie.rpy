##################################################
# annie.rpy —— 安妮
#
#   關於安妮的一切都在這一個檔案裡：立繪、名字、數值、她自己的演出。
#   跟「一個檔案一個房間」同一個原則。
#
#   她的台詞「不在」這裡 —— 對話屬於那一場戲，所以寫在房間的檔案裡
#   (使用者 2026-10-28 的決定：至少看得出那段對話在哪個房間會出現)。
#   這裡只放「只有她自己的」演出，例如走近。
##################################################

# 立繪。
#
# 沒有美術素材，所以用放大的 emoji —— Text(...) 本身就是一張合法的圖。
# 有素材之後把這幾行換成 "characters/annie/calm.png" 之類的路徑就好，
# 其他地方一個字都不用動。
#
# 圖名的第一個字 annie 是「tag」，後面是屬性。所以：
#   show annie angry     只換表情，衣服與位置都保留
#   hide annie           一行收乾淨，不用管她現在是哪個表情
image annie calm    = Text("👻", size=300, color="#cdd6e0")
image annie angry   = Text("😠", size=300, color="#ffaaaa")
image annie furious = Text("😡", size=300, color="#ff6666")
image annie weak    = Text("👻", size=300, color="#55606e")

# 撲到全螢幕用的臉。比上面那幾張大很多 ——
# 那幾張是「站在場景裡的人」，這張是嚇人視窗 (show_jumpscare) 用的。
image annie scare   = Text("👻", size=420, color="#e8eaed")


# 「看情況」的臉。
#
# 這一張刻意不是固定圖，而是每次要畫的時候問一下遊戲狀態。
# 什麼時候該用這種、什麼時候該直接 show annie angry：
#
#   show annie angry    這一句我就是要她生氣 —— 大部分情況用這個
#   show annie mood     她的臉要跟著狀態走，而且會散在好幾個房間，怕漏改
#
# 這裡的規則：在禮拜堂裡她一直是虛弱的（不管哪一句），
# 否則照憤怒值決定。條件由上往下試，第一個成立的就贏。
image annie mood = state_image(
    (Condition(check=lambda s: s.in_room("chapel")), "annie weak"),
    (Condition(check=lambda s: s.stats("annie_ghost", "rage") >= 4), "annie furious"),
    (Condition(check=lambda s: s.stats("annie_ghost", "rage") >= 2), "annie angry"),
    default="annie calm",
)


# 她說話時對話框上顯示的名字
define annie = Character("安妮")


init python:

    def build_annie():
        return Actor(
            key="annie_ghost",
            name="安妮",

            # rage 引擎完全不管 —— 歸零就只是歸零。
            # 要有後果請自己用 Condition 接（attic.rpy 就是這樣用的）。
            stats={"hp": 3, "rage": 0},

            # 沒有 status_display：rage 不該給玩家看到。
        )


# 她走過來的演出。
#
# 這一段完全是普通的 Ren'Py —— 演出本來就是 Ren'Py 的部門
# (見 effect.rpy 開頭：劇情走 label，不要再實作一套流程控制)。
#
# ⚠️ 最後一定要 hide。立繪畫在 master layer 上，跟房間背景同一層；
#    run_event_labels 收尾時只會換畫面，不會幫你收立繪 ——
#    忘記的話一隻巨大的安妮會從此黏在探索畫面上。
label annie_approaches:

    # 第一次出場用 stand 定位（遠 = 小）
    show annie mood at stand(0.06, 0.30)
    with dissolve

    "走廊的另一頭站著一個東西。"

    # 之後每一步只寫目標位置，補間自動從現在的位置開始。
    # 動畫跟講話同時進行，所以「走多快」其實是玩家的閱讀速度。
    show annie mood at step(0.40, 0.60, 1.2)
    annie "你為什麼還在這裡。"

    show annie mood at step(0.78, 1.15, 0.9)
    annie "我說過了。"

    # 最後一步刻意又快又大 —— 前面慢慢靠近就是為了這一下的對比
    show annie mood at step(0.86, 2.0, 0.22)
    annie "——"

    hide annie
    with dissolve

    return
