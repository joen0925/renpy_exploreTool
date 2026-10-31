##################################################
# actors.rpy
#
#   角色初始數值與死亡流程
#   (死亡流程第 6 步再加)
##################################################

# label start 會呼叫這個，要排在第一次 change_room 之前 ——
# 進房事件本身就可能扣血。
#
# 初始數值來自角色目錄 (每個角色的 Actor.stats)。
label init_actor_stats:
    $ init_actor_stats_from_catalog()
    return
