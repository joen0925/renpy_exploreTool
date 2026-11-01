##################################################
# father.rpy —— 爸爸
#
#   
##################################################

image father_stand = "images/father_stand.png"

define father = Character("爸爸")

init python:

    def build_father():
        return Actor(
            key="father",          # 引擎認得這個 id (PLAYER_ACTOR)，不要改
            name="爸爸",

        )
