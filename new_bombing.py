import sys
import math

# Win the water fight by controlling the most territory, or out-soak your opponent!

turn = 0
g_width = 0
g_height = 0
player = 0
position_list = []

def prepare_map(game_map):
    for y in range(g_height):
        for x in range(g_width):
            if game_map[y][x].tile_type != 0:
                continue
            score = (g_height - y)
            if player == 0:
                score += x * 20
            elif player == 1:
                score += (g_width - x) * 20
            game_map[y][x].advance_score = score

def manhatan_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


class Tiles():
    def __init__(self, tile_type, x, y):
        self.tile_type = tile_type
        self.x = x
        self.y = y
        self.advance_score = 0
        

class Agent():
    def __init__(self, agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs):
        self.agent_id = agent_id
        self.player = player
        self.shoot_cooldown = shoot_cooldown
        self.optimal_range = optimal_range
        self.soaking_power = soaking_power
        self.splash_bombs = splash_bombs
        self.x = -1
        self.y = -1
        self.cooldown = -1
        self.wetness = 0
        self.updated = 1
        self.step = 0



    def update_agent(self, agent_id, x, y, cooldown, splash_bombs, wetness):
        self.x = x
        self.y = y
        self.agent_id = agent_id
        self.cooldown = cooldown
        self.splash_bombs = splash_bombs
        self.wetness = wetness

    def find_best_enemy(self, enemys, game_map):
        enemy_to_prio = None
        lowest_hp = 0
        if enemys:
            for enemy in enemys:
                if (abs(self.x - enemy.x) + abs(self.y - enemy.y) <= self.optimal_range * 2):
                    if (enemy.wetness >= lowest_hp):
                        lowest_hp = enemy.wetness
                        enemy_to_prio = enemy
        return enemy_to_prio

    def step_0_sniper(self, enemys, game_map):
        middle_x = g_width // 2
        middle_y = g_height // 2
        best_tile = None
        tiles_type_2 = []
        for y in range(g_height):
            if (player == 0):
                for x in range(g_width // 2 - 1):
                    if game_map[y][x].tile_type == 2:
                        tiles_type_2.append(game_map[y][x])
            else:
                for x in range(g_width // 2 + 1, g_width):
                    if game_map[y][x].tile_type == 2:
                        tiles_type_2.append(game_map[y][x])
        if not tiles_type_2:
            for y in range(g_height):
                if (player == 0):
                    for x in range(g_width // 2 - 1):
                        if game_map[y][x].tile_type == 1:
                            tiles_type_2.append(game_map[y][x])
                else:
                    for x in range(g_width // 2 + 1, g_width):
                        if game_map[y][x].tile_type == 1:
                            tiles_type_2.append(game_map[y][x])
        if not tiles_type_2:
            return middle_x // 2, middle_y / 2
        tiles_type_2.sort(key=lambda tiles: (abs(tiles.x - middle_x), abs(tiles.y - middle_y), tiles.x))
        best_tile = tiles_type_2[0]
        if (player == 0):
            return best_tile.x - 1, best_tile.y
        else:
            return best_tile.x + 1, best_tile.y

    def step_0_bomber(self, enemys, game_map):
        middle_x = g_width // 2
        middle_y = g_height // 2
        if (self.y < middle_y):
            return middle_x, 0
        else:
            return middle_x, g_height


    def step_0_rifle_man(self, enemys, game_map):
        middle_x = g_width // 2
        middle_y = g_height // 2
        return middle_x, middle_y


    def step_1_bomber(self, enemys, game_map):
        find_closest_enemy = None
        distance = 100000
        for enemy in enemys:
            if (manhatan_distance(self.x, self.y, enemy.x, enemy.y) < distance):
                distance = manhatan_distance(self.x, self.y, enemy.x, enemy.y)
                find_closest_enemy = enemy
        if find_closest_enemy != None:
            return find_closest_enemy.x, find_closest_enemy.y
        else:
            return self.x, self.y

    def step_1_rifle_man(self, enemys, game_map):
        find_closest_enemy = None
        distance = 100000
        for enemy in enemys:
            if (manhatan_distance(self.x, self.y, enemy.x, enemy.y) < distance):
                distance = manhatan_distance(self.x, self.y, enemy.x, enemy.y)
                find_closest_enemy = enemy
        if find_closest_enemy != None:
            return find_closest_enemy.x, find_closest_enemy.y
        else:
            return self.x, self.y


    def find_cover(self, enemys, game_map):
        x, y = self.x, self.y
        if (self.optimal_range != 6 and self.x == g_width // 2):
            self.step = 1
        if (self.step == 0):
            if (self.optimal_range == 6):
                return self.step_0_sniper(enemys, game_map)
            if (self.optimal_range == 2):
                return self.step_0_bomber(enemys, game_map)
            if (self.optimal_range == 4):
                return self.step_0_rifle_man(enemys, game_map)
        else:
            if (self.optimal_range == 6):
                return self.step_0_sniper(enemys, game_map)
            if (self.optimal_range == 2):
                return self.step_1_bomber(enemys, game_map)
            if (self.optimal_range == 4):
                return self.step_1_rifle_man(enemys, game_map)
        return x, y

    def check_for_best_bombing_positions(self, enemys, game_map, enemy):
        best_pos = (-1, -1)
        best_score = 0
        for x in range(-1, 1):
            for y in range(-1, 1):
                dx, dy = enemy.x + x, enemy.y + y   
                if not (0 <= dx < g_width and 0 <= dy <g_height):
                    continue
                if (abs(self.x -dx) + abs(self.y - dy) > 4):
                    continue
                score = 0
                for element in position_list:
                    if (abs(dx - element[0]) <= 1 and abs(dy-element[1]) <= 1):
                        score -= 10
                for enemy in enemys:
                    if (abs(dx - enemy.x) <= 1 and abs(dy-enemy.y) <= 1):
                        score += 5
                if (score > best_score):
                    best_score = score
                    best_pos = (dx, dy)
        return best_pos[0], best_pos[1]


    def performe_move(self, enemys, my_agents, game_map):
        enemy = self.find_best_enemy(enemys, game_map)
        position_list.append((self.x, self.y))
        x, y = self.find_cover(enemys, game_map)
        position_list.append((x, y))
        if enemy != None and self.cooldown == 0:
            print(f"{self.agent_id}; MOVE {x} {y}; SHOOT {enemy.agent_id}")
        elif enemy != None and self.splash_bombs > 0 and manhatan_distance(self.x, self.y, enemy.x, enemy.y) <= 5:
            bombing_x, bombing_y = self.check_for_best_bombing_positions(enemys, game_map, enemy)
            if (bombing_x != -1):
                print(f"{self.agent_id}; MOVE {x} {y}; THROW {bombing_x} {bombing_y}")
            else:
                print(f"{self.agent_id}; MOVE {x} {y}; HUNKER_DOWN")
        else:
            print(f"{self.agent_id}; MOVE {x} {y}; HUNKER_DOWN")


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
    agents[agent_id] = Agent(agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs)
# width: Width of the game map
# height: Height of the game map
width, height = [int(i) for i in input().split()]
g_width = width
g_height = height
player = my_id
game_map = [[Tiles(0, 0, 0) for _ in range(width)] for _ in range(height)]
for i in range(height):
    inputs = input().split()
    for j in range(width):
        # x: X coordinate, 0 is left edge
        # y: Y coordinate, 0 is top edge
        x = int(inputs[3*j])
        y = int(inputs[3*j+1])
        tile_type = int(inputs[3*j+2])
        game_map[y][x].tile_type = tile_type
        game_map[y][x].x = x
        game_map[y][x].y = y

# game loop

prepare_map(game_map)
while True:
    turn += 1
    agent_count = int(input())  # Total number of agents still in the game
    enemy_agents = []
    my_agents = []
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
    my_agent_count = int(input())  # Number of alive agents controlled by you
    for agent_id, agent in agents.items():
        if (agent.player == my_id):
            my_agents.append(agent)
        else:
            enemy_agents.append(agent)
    #for i in range(my_agent_count):
    position_list = []
    if enemy_agents:
        sorted_agents = sorted(enemy_agents, key=lambda agent: agent.wetness, reverse=True)
        priority_map = {6: 0, 2: 0, 4: 1}
        my_sorted_agents = sorted(my_agents, key=lambda agent: (priority_map.get(agent.optimal_range, 2), -agent.optimal_range))
        for agent in my_agents:
            agent.performe_move(sorted_agents, my_sorted_agents, game_map)
