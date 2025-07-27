import sys
import math
from collections import deque
import time

# Win the water fight by controlling the most territory, or out-soak your opponent!

C_DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
g_blocked_positions = []
tile_list = []
turn = 0
C_INVERSE = {
    (-1, 0): (1, 0),
    (1, 0): (-1, 0),
    (0, -1): (0, 1),
    (0, 1): (0, -1)
}
C_WALL_PROTECTION = [1, 0.5, 0.25]
G_ADVANCE = False

def manhatan_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)

class Map():
    def __init__(self, width, height):
        self.game_map = [[Tiles(0, 0, 0) for _ in range(width)] for _ in range(height)]
        self.width = width
        self.height = height
        self.covers = []


    def protected_or_not_protected(self, x1, y1, x2, y2):
        cover = 0
        for tile in self.covers:
            if (abs(x1 - tile.x) + abs(y1 - tile.y) != 1):
                continue
            if abs(x2 - tile.x) + abs(y2 - tile.y) == 1:
                continue
            dx, dy = x1 - tile.x, y1 - tile.y
            if (dx != 0 and (x2 - tile.x) * dx > 0) or (dy != 0 and (y2 - tile.y) * dy > 0):
                continue
            if cover != 2:
                cover = tile.tile_type
        return C_WALL_PROTECTION[cover]

    def generate_covers(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.game_map[y][x].tile_type != 0:
                    self.covers.append(self.game_map[y][x])                    


    def valid_tile(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        if self.game_map[y][x].tile_type != 0:
            return False
        if (x, y) in g_blocked_positions:
            return False
        return True

    def walk_backwards(self, start, target, parent):
        current = target
        while parent.get(current) != start:
            current = parent[current]
        return current

    def bfs(self, x, y, new_x, new_y):
        if (x, y) == (new_x, new_y):
            return (x, y)
        queue = deque()
        queue.append((x, y))
        visited = set([x, y])
        parent = {}
        while queue:
            temp_x, temp_y = queue.popleft()
            for dx, dy in C_DIRECTIONS:
                nx, ny = temp_x + dx, temp_y + dy
                if self.valid_tile(nx, ny) and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    parent[(nx, ny)] = (temp_x, temp_y)
                    if (nx, ny) == (new_x, new_y):
                        return self.walk_backwards((x, y), (new_x, new_y), parent)
                    queue.append((nx, ny))
        return (x, y)


class Tiles():
    def __init__(self, tile_type, x, y):
        self.tile_type = tile_type
        self.x = x
        self.y = y

class Agent():
    def __init__(self, agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs):
        self.agent_id = agent_id
        self.player = player
        self.shoot_cooldown = shoot_cooldown
        self.optimal_range = optimal_range
        self.soaking_power = soaking_power
        self.splash_bombs = splash_bombs
        self.x = 0
        self.y = 0
        self.new_x = 0
        self.new_y = 0
        self.cooldown = -1
        self.wetness = 0
        self.updated = 1
        self.step = 0
        self.command_to_execute = ""
        self.possible_moves = []
        self.possible_bombin_positions = []
        self.message = ""

    def create_possible_moves(self, game):
        self.possible_moves.clear()
        self.possible_moves.append((self.x, self.y))
        for (dx, dy) in C_DIRECTIONS:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < game.width and 0 <= ny < game.height:
                if game.game_map[ny][nx].tile_type == 0:
                    self.possible_moves.append((nx, ny))


    def calculate_dmg(self, possibility, enemys, game):
        max_dmg_taken = 0
        prot = 0
        for enemy in enemys:
            distance = manhatan_distance(possibility[0], possibility[1], enemy.x, enemy.y)
            if (enemy.splash_bombs > 0 and distance <= 7):
                max_dmg_taken += 30
            else:
                protection_score = game.protected_or_not_protected(possibility[0], possibility[1], enemy.x, enemy.y)
                prot += protection_score
                if (distance <= enemy.optimal_range + 1):
                    max_dmg_taken += enemy.soaking_power * protection_score
                elif (distance <= enemy.optimal_range * 2 + 1):
                    max_dmg_taken += enemy.soaking_power * protection_score * 0.5
        return max_dmg_taken, prot

    def explore_dmg_to_be_done(self, possibility, enemys, game):
        max_dmg = 0
        for enemy in enemys:
            distance = manhatan_distance(possibility[0], possibility[1], enemy.x, enemy.y)
            if (self.splash_bombs > 0 and distance <= 4):
                return 30
            else:
                protection_score = game.protected_or_not_protected(enemy.x, enemy.y, possibility[0], possibility[1])
                if (distance <= self.optimal_range):
                    return self.soaking_power * protection_score
                elif (distance <= self.optimal_range * 2):
                    max_dmg = protection_score * 0.5 * self.soaking_power
        return max_dmg


    def explore_best_move(self, enemys, game):
        delta_dmg_taken_dmg_done = []
        for possibility in self.possible_moves:
            if (possibility in g_blocked_positions):
                continue
            max_dmg, prot = self.calculate_dmg(possibility, enemys, game)
            dmg_to_be_done = self.explore_dmg_to_be_done(possibility, enemys, game)
            delta_dmg_taken_dmg_done.append((possibility, dmg_to_be_done - max_dmg))
            
        delta_dmg_taken_dmg_done.sort(key=lambda x: x[1], reverse=True)
        return delta_dmg_taken_dmg_done[0]

    def update_agent(self, agent_id, x, y, cooldown, splash_bombs, wetness):
        self.x = x
        self.y = y
        self.agent_id = agent_id
        self.cooldown = cooldown
        self.splash_bombs = splash_bombs
        self.wetness = wetness
        self.command_to_execute = ""
        self.new_x = x
        self.new_y = y

    def estimate_attack_pattern(self, enemys, game):
        self.command_to_execute += ";HUNKER_DOWN"

    def calculate_movement(self, enemys, game):
        self.command_to_execute += f"{self.agent_id}; MOVE {self.new_x} {self.new_y}"

    # Count guarateed hits only, check where enemy, might go, if all enemy movements are within range throw
    def find_bombing_position(self, enemys, game):
        range_of_bombs = 4
        guaranteed_plosible_hits = []
        for dx in range(-range_of_bombs, range_of_bombs + 1):
            for dy in range(-range_of_bombs, range_of_bombs + 1):
                if abs(dx) + abs(dy) > range_of_bombs:
                    continue
                nx, ny = self.new_x + dx, self.new_y + dy
                if not (0 <= nx < game.width and 0 <= ny < game.height):
                    continue
                continue_val = False
                for (x, y) in g_blocked_positions:
                    if (abs(nx - x) <= 1 and abs(ny - y) <= 1):
                        continue_val = True
                        break
                if continue_val:
                    continue
                at_least_1_enemy_will_be_hit = 0
                side_damage = 0
                for enemy in enemys:
                    all_covered = True
                    side_attack = 0
                    for (x, y) in enemy.possible_moves:
                        if (abs(nx - x) <= 1 and abs(ny - y) <= 1):
                            side_attack += 1
                        else:
                            all_covered = False
                    if (all_covered == True):
                        at_least_1_enemy_will_be_hit += 1
                    else:
                        side_damage += side_attack / len(enemy.possible_moves)
                if (at_least_1_enemy_will_be_hit > 0):
                    guaranteed_plosible_hits.append(((nx, ny), at_least_1_enemy_will_be_hit, side_damage))
        guaranteed_plosible_hits.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return guaranteed_plosible_hits[0] if guaranteed_plosible_hits else None


    def execute_command(self):
        print(self.command_to_execute)

    def append_message(self, time):
        self.command_to_execute += f";MESSAGE {self.message}"

    def find_closest_enemy(self, enemys, game):
        enemy_to_return = None
        current_man_dist = 1000
        for enemy in enemys:
            man_dist = manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y)
            if (man_dist < current_man_dist):
                enemy_to_return = enemy
                current_man_dist = man_dist
        return enemy_to_return
    

    def dps_find_closest_enemy(self, enemys, game):
        enemies_in_range = []
        for enemy in enemys:
            protection = game.protected_or_not_protected(enemy.x, enemy.y, self.new_x, self.new_y)
            man_dist = manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y)
            dmg = 0
            if (man_dist <= self.optimal_range):
                dmg = protection * self.soaking_power
            elif (man_dist < self.optimal_range * 2):
                dmg = protection * self.soaking_power * 0.5
            enemies_in_range.append((enemy, dmg))
        enemies_in_range.sort(key=lambda x: x[1], reverse=True)
        return enemies_in_range[0][0] if enemies_in_range else None


class Sniper(Agent):
    def __init__(self, agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs):
        super().__init__(agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs)

    def append_message(self, time):
        message = "Sho'em"
        self.command_to_execute += f";MESSAGE {message} {self.message}"


    def estimate_attack_pattern(self, enemys, game):
        enemy = self.dps_find_closest_enemy(enemys, game)
        if enemy != None and self.cooldown == 0 and manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y) <= self.optimal_range * 2:
            self.command_to_execute += f"; SHOOT {enemy.agent_id}"
        else:
            self.command_to_execute += f"; HUNKER_DOWN"


    def calculate_movement(self, enemys, game):
        enemy = self.find_closest_enemy(enemys, game)
        g_blocked_positions.remove((self.x, self.y))
        pos, score = self.explore_best_move(enemys, game)
        if (enemy != None and manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y) >= self.optimal_range + 2 or G_ADVANCE):
            (x, y) = game.bfs(self.x, self.y, enemy.x, enemy.y)          
            self.new_x = x
            self.new_y = y
        else:
            self.new_x = pos[0]
            self.new_y = pos[1]
        self.command_to_execute += f"{self.agent_id}; MOVE {self.new_x} {self.new_y}"
        g_blocked_positions.append((self.new_x, self.new_y))

class Bomber(Agent):
    def __init__(self, agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs):
        super().__init__(agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs)

    def append_message(self, time):
        message = "Bomba"
        self.command_to_execute += f";MESSAGE {message} {self.message}"

    def estimate_attack_pattern(self, enemys, game):
        enemy = self.dps_find_closest_enemy(enemys, game)
        if (enemy != None and manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y) <= 6 and self.splash_bombs > 0):
            result = self.find_bombing_position(enemys, game)
            if (result != None):
                self.command_to_execute += f"; THROW {result[0][0]} {result[0][1]}"
            elif enemy != None and self.cooldown == 0 and manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y) <= self.optimal_range * 2 + 2:
                self.command_to_execute += f"; SHOOT {enemy.agent_id}"
            else:
                self.command_to_execute += f"; HUNKER_DOWN"
        elif enemy != None and self.cooldown == 0 and manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y) <= self.optimal_range * 2 + 2:
            self.command_to_execute += f"; SHOOT {enemy.agent_id}"
        else:
            self.command_to_execute += f"; HUNKER_DOWN"

    def calculate_movement(self, enemys, game):
        enemy = self.find_closest_enemy(enemys, game)
        g_blocked_positions.remove((self.x, self.y))
        pos, score = self.explore_best_move(enemys, game)
        if (enemy != None and manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y) >= 7 or G_ADVANCE):            
            (x, y) = game.bfs(self.x, self.y, enemy.x, enemy.y)          
            self.new_x = x
            self.new_y = y
        else:
            self.new_x = pos[0]
            self.new_y = pos[1]
        self.command_to_execute += f"{self.agent_id}; MOVE {self.new_x} {self.new_y}"
        g_blocked_positions.append((self.new_x, self.new_y))


class RifleMan(Agent):
    def __init__(self, agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs):
        super().__init__(agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs)

    def append_message(self, time):
        message = "RifleMan"
        self.command_to_execute += f";MESSAGE {message} {self.message}"

    def calculate_movement(self, enemys, game):
        enemy = self.find_closest_enemy(enemys, game)
        g_blocked_positions.remove((self.x, self.y))
        pos, score = self.explore_best_move(enemys, game)
        if (enemy != None and manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y) >= 8 or G_ADVANCE):            
            (x, y) = game.bfs(self.x, self.y, enemy.x, enemy.y)          
            self.new_x = x
            self.new_y = y
        else:
            self.new_x = pos[0]
            self.new_y = pos[1]
        self.command_to_execute += f"{self.agent_id}; MOVE {self.new_x} {self.new_y}"
        g_blocked_positions.append((self.new_x, self.new_y))

    def estimate_attack_pattern(self, enemys, game):
        enemy = self.dps_find_closest_enemy(enemys, game)
        if (enemy != None and manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y) <= 6 and self.splash_bombs > 0):
            result = self.find_bombing_position(enemys, game)
            if (result != None):
                self.command_to_execute += f"; THROW {result[0][0]} {result[0][1]}"
            elif enemy != None and self.cooldown == 0 and manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y) <= self.optimal_range * 2 + 1:
                self.command_to_execute += f"; SHOOT {enemy.agent_id}"
            else:
                self.command_to_execute += f"; HUNKER_DOWN"
        elif enemy != None and self.cooldown == 0 and manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y) <= self.optimal_range * 2 + 1:
            self.command_to_execute += f"; SHOOT {enemy.agent_id}"
        else:
            self.command_to_execute += f"; HUNKER_DOWN"

def create_agent(agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs):
    if (optimal_range >= 6):
        return Sniper(agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs)
    elif (2 < optimal_range < 6):
        return RifleMan(agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs)
    else:
        return Bomber(agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs)


my_id = int(input())  # Your player id (0 or 1)
agent_data_count = int(input())  # Total number of agents in the game
agents = {}
for i in range(agent_data_count):
    # agent_id: Unique identifier for this agent
    # player: Player id of this agent
    # shoot_cooldown: Number of turns between each of this agent's shots
    # optimal_range: Maximum manhattan distance for greatest damage output
    # soaking_power: Damage output within optimal conditions
    # splash_bombs: Number of splash bombs this can throw this game
    agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs = [int(j) for j in input().split()]
    agents[agent_id] = create_agent(agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs)
# width: Width of the game map
# height: Height of the game map
width, height = [int(i) for i in input().split()]
game = Map(width, height)

for i in range(height):
    inputs = input().split()
    for j in range(width):
        # x: X coordinate, 0 is left edge
        # y: Y coordinate, 0 is top edge
        x = int(inputs[3*j])
        y = int(inputs[3*j+1])
        tile_type = int(inputs[3*j+2])
        game.game_map[y][x].tile_type = tile_type
        game.game_map[y][x].x = x
        game.game_map[y][x].y = y

game.generate_covers()

# game loop
while True:
    agent_count = int(input())  # Total number of agents still in the game
    turn += 1
    for agent_id, agent in agents.items():
        agent.updated = 0
    for i in range(agent_count):
        # cooldown: Number of turns before this agent can shoot
        # wetness: Damage (0-100) this agent has taken
        agent_id, x, y, cooldown, splash_bombs, wetness = [int(j) for j in input().split()]
        agents[agent_id].update_agent(agent_id, x, y, cooldown, splash_bombs, wetness)
        agents[agent_id].updated = 1
    agents_to_remove = [agent_id for agent_id, agent in agents.items() if agent.updated == 0]
    for agent_id in agents_to_remove:
        del agents[agent_id]
    enemy_agents = []
    my_agents = []
    g_blocked_positions.clear()

    for agent_id, agent in agents.items():
        agent.create_possible_moves(game)
        if (agent.player == my_id):
            my_agents.append(agent)
            g_blocked_positions.append((agents[agent_id].x, agents[agent_id].y))
        else:
            enemy_agents.append(agent)
    if (turn >= game.width + game.height // 2):
        G_ADVANCE = True
    my_agent_count = int(input())  # Number of alive agents controlled by you
    for i in range(my_agent_count):
        start_time = time.time()
        my_agents[i].calculate_movement(enemy_agents, game)
        my_agents[i].estimate_attack_pattern(enemy_agents, game)
        end_time = time.time()
        delta_time = (end_time - start_time) * 1000
        my_agents[i].append_message(delta_time)
        my_agents[i].execute_command()
        # Write an action using print
        # To debug: print("Debug messages...", file=sys.stderr, flush=True)


        # One line per agent: <agentId>;<action1;action2;...> actions are "MOVE x y | SHOOT id | THROW x y | HUNKER_DOWN | MESSAGE text"
