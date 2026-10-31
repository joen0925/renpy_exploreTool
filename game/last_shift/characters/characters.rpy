##################################################
# characters.rpy
#
#   角色清單 (遊戲內容，不屬於 game/libs/ 的引擎)
#
#   新增角色的步驟：
#     1. 在 characters/ 底下寫一個 xxx.rpy，裡面有 build_xxx() 回傳 Actor
#     2. 在下面 build_actors() 裡加一行 add_actor(actors, build_xxx())
#
#   立繪、Character、那個角色自己的演出也都寫在他自己的檔案裡 ——
#   要知道安妮長什麼樣、幾滴血、會做什麼，看 annie.rpy 一個檔案就夠了。
#
#   演出用的站位轉換也放在這裡，因為它是所有角色共用的。
##################################################

init python:

    def build_actors():
        actors = {}

        add_actor(actors, build_me())
        #add_actor(actors, build_annie())

        return actors


# 立繪的站位。所有角色共用。
#
# x 是 xalign (0 = 最左, 1 = 最右)，z 是 zoom (越大 = 越近)。
# yalign 固定貼著地面附近 —— 走近的時候不該上下飄。

# 站定在某個位置。只有「第一次出場」用這個。
transform stand(x, z):
    xalign x
    yalign 0.98
    zoom z


# 從「現在的位置」走到 (x, z)，花 t 秒。
#
# 為什麼只寫目標、不用寫起點：Ren'Py 重新 show 一張已經在畫面上的圖時，
# 新的 transform 會繼承舊 transform 的狀態
# (renpy/display/scenelists.py 的 transform_state -> take_state)。
# 所以 linear 是從「它現在在哪」補間過去的。
#
# 附帶好處是**不怕玩家點太快**：上一步的動畫還沒走完就被推進下一句時，
# 下一步會從「動畫走到一半的位置」接著走，不會跳。
transform step(x, z, t=1.0):
    yalign 0.98
    linear t xalign x zoom z


# 角色目錄。
#
# 為什麼是 init 1 而不是 define：
# define 在優先權 0 執行，跟各角色檔的 init python 同一層，所以會照檔名
# 排序 —— 檔名排在 characters.rpy 之後的角色 (例如 me.rpy) 會來不及定義：
#     NameError: name 'build_me' is not defined
# init 1 保證在所有優先權 0 的 init 跑完之後才執行，檔名怎麼取都不會踩到。
# (rooms.rpy 是同一個理由)
#
# 為什麼不是 default：角色是靜態定義，不該進存檔。
# 進存檔的話改了名字、改了初始血量，舊存檔都吃不到 —— 那是 rooms 踩過的坑。
init 1 python:
    actor_catalog = build_actors()


# 打錯 actor id 在遊戲啟動時就報錯。
#
# 排在 init 2 是因為它要等 rooms (init 1) 與 puzzle_catalog 都建好。
#
# 為什麼值得這個檢查：Effect(actor="playr", stats={"hp": -1}) 會讓
# ActorState 憑空生出一個 hp=0 的幽靈角色，而真正的玩家一滴血都沒掉 ——
# 遊戲照跑，只是主角變成無敵。
#init 2 python:
    #check_actor_catalog(rooms, puzzle_catalog)
