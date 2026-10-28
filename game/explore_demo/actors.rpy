##################################################
# actors.rpy
#
#   玩家死亡流程 (遊戲內容，不屬於 game/libs/ 的引擎)
#
#   角色本身的定義已經搬到 characters/ 了 ——
#   一個檔案一個角色，立繪／名字／初始數值／那個角色自己的演出都在裡面。
#   (2026-10-28。原本這裡有 actor_start_stats 與 player_status_display
#    兩張表，而「安妮是誰」沒有任何地方定義，只有散在各處的 "annie_ghost"
#    字串。現在初始數值在 Actor.stats、狀態欄在 Actor.status_display)
#
#   引擎只認得一個數值名稱：hp，歸零代表死亡。
#   其他名稱 (rage / battery / stamina) 引擎完全不管，
#   歸零就只是歸零，要有後果請自己用 Condition 接。
#
#   沒有設定 hp 的角色是「無敵」的 —— 引擎不會給任何預設血量。
#   所以要能被打死的角色，一定要在他的 Actor 裡填 stats={"hp": n}。
##################################################

# 玩家死亡時要跳過去的 label。
#
# 引擎用 getattr(store, "on_player_death", None) 去找這個名字，
# 所以它屬於遊戲內容，引擎不寫死。沒宣告的話玩家死掉不會有任何事發生。
define on_player_death = "game_over"


# label start 會呼叫這個，要排在第一次 change_room 之前 ——
# 進房事件本身就可能扣血。
#
# 初始數值來自角色目錄 (每個角色的 Actor.stats)，
# 所以新增角色不用回來改這裡。
label init_actor_stats:
    $ init_actor_stats_from_catalog()
    return


##################################################
# 死亡流程
##################################################

# 注意：這個 label 是被 jump 進來的，不是 call ——
# 死掉不該回到探索迴圈，所以這裡不能 return，要自己收尾。
label game_over:
    scene black with fade
    "你的意識沉了下去……"
    "GAME OVER"

    # 回主選單。
    #
    # 不能寫 $ MainMenu(confirm=False) —— MainMenu 是一個「畫面動作 (Action)」
    # 類別，那樣寫只是「建立一個動作物件然後丟掉」，什麼都不會發生。
    # 動作是給 screen 的 action= 用的 (例如 textbutton "主選單" action MainMenu())。
    # 在 label 裡要直接執行，用 renpy.full_restart()。
    $ renpy.full_restart()
