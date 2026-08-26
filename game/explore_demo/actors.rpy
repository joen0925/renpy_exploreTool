##################################################
# actors.rpy
#
#   角色的初始數值 (遊戲內容，不屬於 game/libs/ 的引擎)
#
#   引擎只認得一個數值名稱：hp，歸零代表死亡。
#   其他名稱 (rage / battery / stamina) 引擎完全不管，
#   歸零就只是歸零，要有後果請自己用 Condition 接。
#
#   沒有設定 hp 的角色是「無敵」的 —— 引擎不會給任何預設血量。
#   所以要能被打死的角色，一定要在下面這張表裡出現。
##################################################

# 要調整血量、憤怒值就改這裡。
# 外層是角色 id，內層是那個角色的初始數值。
define actor_start_stats = {
    "player":      {"hp": 5},
    "annie_ghost": {"hp": 3, "rage": 0},
}

# 玩家死亡時要跳過去的 label。
#
# 引擎用 getattr(store, "on_player_death", None) 去找這個名字，
# 所以它屬於遊戲內容，引擎不寫死。沒宣告的話玩家死掉不會有任何事發生。
define on_player_death = "game_over"


# label start 會呼叫這個，要排在第一次 change_room 之前 ——
# 進房事件本身就可能扣血。
label init_actor_stats:
    python:
        for _actor, _stats in actor_start_stats.items():
            for _stat, _value in _stats.items():
                game_state.actors.set(_actor, _stat, _value)
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
