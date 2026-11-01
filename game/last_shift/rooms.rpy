init python:

    def build_rooms():
        rooms = {}

        rooms["corridor"] = build_corridor()
        rooms["sister_room"] = build_sister_room()
        rooms["living_room"] = build_living_room()
        rooms["drawer_inside"] = build_drawer_inside()

        return rooms

init 1 python:
    rooms = build_rooms()