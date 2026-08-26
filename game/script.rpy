# 遊戲腳本位於此檔案。

# 宣告該遊戲使用的角色。 color 參數
# 為角色的名稱著色。

define e = Character("艾琳")


# 遊戲從這裡開始。

label start:

    # 設定角色的初始數值 (血量、憤怒值)。
    # 一定要排在第一次 change_room 之前 —— 進房事件本身就可能扣血。
    # 沒有設定 hp 的角色在引擎眼中是無敵的。
    call init_actor_stats from _call_init_actor_stats

    # 先把探索畫面顯示出來，之後 say_in_room 會負責在講話時暫時收起它、
    # 講完再自動放回來。
    show screen explore

    # 切換到示範房間。這個房間設了 on_enter="demo_room_enter"，
    # 所以 change_room() 會自動去跑那個 label 講開場白。
    $ change_room("demo_room")

    # 進入探索主迴圈，把控制權交給玩家。
    # 這個 label 不會自己結束，要離開探索狀態時
    # 從熱點的 label 裡 jump 出去即可。
    jump explore_loop