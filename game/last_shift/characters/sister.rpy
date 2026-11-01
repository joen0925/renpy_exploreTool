##################################################
# sister.rpy —— 妹妹
#
#   
##################################################

image sister_scare = "images/jumpscare_sister.png"

define sister = Character("妹妹")

init python:

    def build_sister():
        return Actor(
            key="sister",          # 引擎認得這個 id (PLAYER_ACTOR)，不要改
            name="妹妹",
        )
