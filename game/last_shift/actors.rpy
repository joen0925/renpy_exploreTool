##################################################
# actors.rpy
#
#   角色初始數值與死亡流程
#   (死亡流程第 6 步再加)
##################################################

#角色死亡路線
define on_player_death = "game_over"



label game_over:
    scene black with fade
    "在他眼裡，你只是一個闖進家裡的陌生人。"
    "刀落下的時候，你連叫都來不及。"
    "（重新開始，或讀取存檔再試一次。）"
    "GAME OVER"

    $ renpy.full_restart()


# label start 會呼叫這個，要排在第一次 change_room 之前 ——
# 進房事件本身就可能扣血。
#
# 初始數值來自角色目錄 (每個角色的 Actor.stats)。
label init_actor_stats:
    $ init_actor_stats_from_catalog()
    return


