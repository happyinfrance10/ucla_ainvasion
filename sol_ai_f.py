from colorfight import Colorfight
import time
import random
import numpy as np
from colorfight.constants import BLD_GOLD_MINE, BLD_ENERGY_WELL, BLD_FORTRESS, BUILDING_COST, BLD_HOME

def get_home_x(game):
    for cell in game.me.cells.values():
        if(cell.building.is_home):
            return cell.position.x
    return -1

def get_home_y(game):
    for cell in game.me.cells.values():
        if(cell.building.is_home):
            return cell.position.y
    return -1

def surrounded_by_us(me, cell):
    x = cell.position.x
    y = cell.position.y
    for i in range(max(0,x-1), min(29, x+1)):
        for j in range(max(0, y-1), min(29, y+1)):
            if game.game_map[(i, j)].owner != me.uid:
                return False
    return True

def play_game(
        game, \
        room     = 'public', \
        username = 'nullptr', \
        password = 'null', \
        join_key = ''):
    # Connect to the server. This will connect to the public room. If you want to
    # join other rooms, you need to change the argument
    game.connect(room = room)

    # game.register should return True if succeed.
    # As no duplicate usernames are allowed, a random integer string is appended
    # to the example username. You don't need to do this, change the username
    # to your ID.
    # You need to set a password. For the example AI, the current time is used
    # as the password. You should change it to something that will not change
    # between runs so you can continue the game if disconnected.
    if game.register(username = username, \
            password = password, join_key = join_key):
        # This is the game loop
        while True:
            # The command list we will send to the server
            cmd_list = []
            # The list of cells that we want to attack
            my_attack_list = []
            # update_turn() is required to get the latest information from the
            # server. This will halt the program until it receives the updated
            # information.
            # After update_turn(), game object will be updated.
            # update_turn() returns a Boolean value indicating if it's still
            # the same game. If it's not, break out
            if not game.update_turn():
                break

            # Check if you exist in the game. If not, wait for the next round.
            # You may not appear immediately after you join. But you should be
            # in the game after one round.
            if game.me == None:
                continue

            me = game.me
            home_x = get_home_x(game)
            home_y = get_home_y(game)
            if(home_x==-1 and home_y ==-1):
                for cell in game.me.cells.values():
                    if(cell.owner==game.me.uid and cell.building.is_empty and me.gold >= BUILDING_COST[0]):
                        cmd_list.append(game.build(cell.position, BLD_HOME))
                        print("We build {} on ({}, {})".format(BLD_HOME, cell.position.x, cell.position.y))
                        me.gold -= 100
            # game.me.cells is a dict, where the keys are Position and the values
            # are MapCell. Get all my cells.
            home = game.game_map[(home_x, home_y)]
            if(home.building.can_upgrade and (home.building.upgrade_gold < me.gold and home.building.upgrade_energy < me.energy)):
                cmd_list.append(game.upgrade(home.position))
                print("We upgraded ({}, {})".format(home.position.x, home.position.y))
                me.gold   -= home.building.upgrade_gold
                me.energy -= home.building.upgrade_energy
            for cell in game.me.cells.values():

                # If we can upgrade the building, upgrade it.
                # Notice can_update only checks for upper bound. You need to check
                # tech_level by yourself.
                gmult = min((-1/np.pi)*(np.arctan(.015*(len(me.cells)-425)))+0.675, 1.0)
                if cell.building.can_upgrade and \
                        (cell.building.is_home or (surrounded_by_us(me, cell) and \
                        cell.building.level < me.tech_level)) and \
                        cell.building.upgrade_gold < (gmult*me.gold) and \
                        cell.building.upgrade_energy < me.energy:
                    cmd_list.append(game.upgrade(cell.position))
                    print("We upgraded ({}, {})".format(cell.position.x, cell.position.y))
                    me.gold   -= cell.building.upgrade_gold
                    me.energy -= cell.building.upgrade_energy


                # Check the surrounding position
                for pos in cell.position.get_surrounding_cardinals():
                    # Get the MapCell object of that position
                    c = game.game_map[pos]
                    # Attack if the cost is less than what I have, and the owner
                    # is not mine, and I have not attacked it in this round already
                    # We also try to keep our cell number under 100 to avoid tax
                    multiplier = max(1.25, (me.energy/6000)+1)
                    if(c.building.is_home):
                        multiplier = max(4.5, multiplier)
                    if(c.owner == 0):
                        multiplier = 1
                    attack = int(c.attack_cost*multiplier)
                    if attack < me.energy and c.owner != game.uid \
                            and c.position not in my_attack_list \
                            and (len(me.cells) < max(225, me.gold/250)) \
                            and ((me.tech_level >1 and (c.energy > 4 or c.gold > 4 or random.randint(0,6)>3)) or \
                            (c.energy > 8 or c.gold > 8 or random.randint(0,9)>6) or (c.owner!=0) or (random.randint(0,9)==0)):
                        # Add the attack command in the command list
                        # Subtract the attack cost manually so I can keep track
                        # of the energy I have.
                        # Add the position to the attack list so I won't attack
                        # the same cell
                        cmd_list.append(game.attack(pos, attack))
                        print("We are attacking ({}, {}) with {} energy".format(pos.x, pos.y, attack))
                        game.me.energy -= attack
                        # cmd_list.append(game.attack(pos, c.attack_cost))
                        # print("We are attacking ({}, {}) with {} energy".format(pos.x, pos.y, c.attack_cost))
                        # game.me.energy -= c.attack_cost
                        my_attack_list.append(c.position)


                # Build a random building if we have enough gold
                if cell.owner == me.uid and cell.building.is_empty and me.gold >= BUILDING_COST[0] \
                and (10-int(len(me.cells)/35)<=0 or random.randint(0, 10-int(len(me.cells)/35))==0 or len(me.cells)>125):
                    # if(me.buildings%200 == 0):
                    #     building = BLD_HOME
                    if(cell.gold <=6 and cell.energy <= 6):
                        if(9-int(len(me.cells)/15)<=0 or random.randint(0, 9-int(len(me.cells)/15))==0):
                            building = BLD_FORTRESS
                        elif(cell.gold > cell.energy):
                            if(len(me.cells)<100 and cell.gold < 9):
                                building = BLD_ENERGY_WELL
                            else:
                                building = BLD_GOLD_MINE
                        else:
                            building = BLD_ENERGY_WELL
                    elif(cell.gold > cell.energy):
                        if(len(me.cells)<100 and cell.gold < 9):
                            building = BLD_ENERGY_WELL
                        else:
                            building = BLD_GOLD_MINE
                    else:
                        building = BLD_ENERGY_WELL
                    cmd_list.append(game.build(cell.position, building))
                    print("We build {} on ({}, {})".format(building, cell.position.x, cell.position.y))
                    me.gold -= 100


            # Send the command list to the server
            result = game.send_cmd(cmd_list)
            print(result)

    # Do this to release all the allocated resources.
    game.disconnect()

if __name__ == '__main__':
    # Create a Colorfight Instance. This will be the object that you interact
    # with.
    game = Colorfight()

    # ================== Find a random non-full rank room ==================
    #room_list = game.get_gameroom_list()
    #rank_room = [room for room in room_list if room["rank"] and room["player_number"] < room["max_player"]]
    #room = random.choice(rank_room)["name"]
    # ======================================================================
    # room = 'nullptr' # Delete this line if you have a room from above
    room = 'public'
    # ==========================  Play game once ===========================
    play_game(
        game     = game, \
        room     = room, \
        username = 'nullptr', \
        password = 'null', \
        join_key = ''
    )
    # ======================================================================

    # ========================= Run my bot forever =========================
    # while True:
    #    try:
    #        play_game(
    #            game     = game, \
    #            room     = room, \
    #            username = 'ExampleAI' + str(random.randint(1, 100)), \
    #            password = str(int(time.time()))
    #        )
    #    except Exception as e:
    #        print(e)
    #        time.sleep(2)
