import sys
import math

# Win the water fight by controlling the most territory, or out-soak your opponent!
g_width = 0
g_height = 0
throws = [(2, 9), (2, 2), (12, 2), (12, 9)]
turn = 0

def manhatan_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


class Tiles():
    def __init__(self, tile_type, x, y):
        self.tile_type = tile_type
        self.x = x
        self.y = y
        self.protection_score = 0
        self.taken = False
        

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


    def update_agent(self, agent_id, x, y, cooldown, splash_bombs, wetness):
        self.x = x
        self.y = y
        self.agent_id = agent_id
        self.cooldown = cooldown
        self.splash_bombs = splash_bombs
        self.wetness = wetness

    def potential_life_lost_score(self):
        pass

    def find_best_cover(self, enemys, game_map):
        x, y = self.x, self.y
        distance_to_check = 5
        prot_score = game_map[self.y][self.x].protection_score
        for j in range(-distance_to_check, distance_to_check):
            for k in range(-distance_to_check, distance_to_check):
                if (self.y + j >= 0 and self.y + j < g_height and self.x + k >= 0 and self.x + k < g_width):
                    if (game_map[self.y + j][self.x + k].protection_score > prot_score and game_map[self.y + j][self.x + k].taken == False):
                        x = self.x + k
                        y = self.y + j
                        prot_score = game_map[self.y + j][self.x + k].protection_score
        return x, y


    def remove_protection_score(self, game_map, x, y):
        x, y = self.x, self.y
        distance_to_check = 2
        game_map[y][x].taken = True
        for j in range(-distance_to_check, distance_to_check):
            for k in range(-distance_to_check, distance_to_check):
                if (self.y + j > 0 and self.y + j < g_height and self.x + k > 0 and self.x + k < g_width):
                    game_map[self.y + j][self.x + k].protection_score -= 50
                    game_map[self.y + j][self.x + k].taken = True
        return x, y


    def find_best_enemy(self, enemys, game_map):
        enemy_to_prio = None
        if enemys:
            soak_protection = 1000000000
            for enemy in enemys:
                if (abs(self.x - enemy.x) + abs(self.y - enemy.y) <= self.optimal_range * 2):
                    if (game_map[enemy.y][enemy.x].protection_score < soak_protection):
                        soak_protection = game_map[enemy.y][enemy.x].protection_score
                        enemy_to_prio = enemy
        return enemy_to_prio

    def perform_move(self, enemys, game_map):
        x, y = self.find_best_cover(enemys, game_map)
        enemy = self.find_best_enemy(enemys, game_map)
        print(f"{self.cooldown}", file=sys.stderr, flush=True)            
        if enemy != None and self.cooldown == 0:
            print(f"{self.agent_id}; MOVE {x} {y}; SHOOT {enemy.agent_id}")
        else:
            print(f"{self.agent_id}; MOVE {x} {y}")
        self.remove_protection_score(game_map, x, y)    

def calculate_squeres_of_the_game_map(game_map):
    for y in range(g_height):
        for x in range(g_width):
            if (game_map[y][x].tile_type != 0):
                continue
            if (x - 1 >= 0 and y - 1 >= 0):
                if (game_map[y - 1][x - 1].tile_type != 0):
                    game_map[y][x].protection_score += game_map[y - 1][x - 1].tile_type * (y) * (x)
            if (x + 1 < g_width and y - 1 >= 0):
                if (game_map[y - 1][x + 1].tile_type != 0):
                    game_map[y][x].protection_score += game_map[y - 1][x + 1].tile_type * (y) * (g_width - x)
            if (x - 1 >= 0 and y + 1 < g_height):
                if (game_map[y + 1][x - 1].tile_type != 0):
                    game_map[y][x].protection_score += game_map[y + 1][x - 1].tile_type * (g_height - y) * (x)
            if (x + 1 < g_width and y + 1 < g_height):
                if (game_map[y + 1][x + 1].tile_type != 0):
                    game_map[y][x].protection_score += game_map[y + 1][x + 1].tile_type * (g_height - y) * (g_width - x)
            if (x - 1 >= 0):
                if (game_map[y][x - 1].tile_type != 0):
                    coef = y
                    if (x < g_height):
                        coef = x
                    triangle = ((((coef - 1) * coef) / 2) + ((g_height - coef - 1)*(g_height - coef)) / 2) * game_map[y][x - 1].tile_type
                    game_map[y][x].protection_score += game_map[y][x - 1].tile_type * (x) * (g_height) - triangle
            if (x + 1 < g_width):
                if (game_map[y][x + 1].tile_type != 0):
                    coef = y
                    if (g_width - x < g_height):
                        coef = g_width - x
                    triangle = ((((coef - 1) * coef) / 2) + ((g_height - coef - 1)*(g_height - coef)) / 2) * game_map[y][x - 1].tile_type
                    game_map[y][x].protection_score += game_map[y][x + 1].tile_type * (g_width - x) * (g_height)  - triangle
            if (y - 1 >= 0):
                if (game_map[y - 1][x].tile_type != 0):
                    coef = x
                    if (y < g_width):
                        coef = y
                    triangle = ((((coef - 1) * coef) / 2) + ((g_width - coef - 1)*(g_width - coef)) / 2) * game_map[y - 1][x].tile_type
                    game_map[y][x].protection_score += game_map[y - 1][x].tile_type * (g_width) * (y) - triangle
            if (y + 1 < g_height):
                if (game_map[y + 1][x].tile_type != 0):
                    coef = x
                    if (g_height - y < g_width):
                        coef = g_height - y
                    triangle = ((((coef - 1) * coef) / 2) + ((g_width - coef - 1)*(g_width - coef)) / 2) * game_map[y + 1][x].tile_type
                    game_map[y][x].protection_score += game_map[y + 1][x].tile_type * (g_width) * (g_height - y) - triangle




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
throws = [(2, 2), (g_width - 3, 2), (2, g_height - 3), (g_width - 3, g_height - 3)]
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
        game_map[y][x].x = y
        # not good way to check it
        # if (tile_type != 0):
        #     if (y - 1 >= 0):
        #         game_map[y - 1][x].protection_score += tile_type
        #     if (y + 1 < height):
        #         game_map[y + 1][x].protection_score += tile_type
        #     if (x - 1 >= 0):
        #         game_map[y][x - 1].protection_score += tile_type
        #     if (x - 1 < width):
        #         game_map[y][x + 1].protection_score += tile_type

# game loop
calculate_squeres_of_the_game_map(game_map)
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

    if enemy_agents:
        sorted_agents = sorted(enemy_agents, key=lambda agent: agent.wetness, reverse=True)
        for agent in my_agents:
            agent.perform_move(sorted_agents, game_map)
        # Write an action using print
        # To debug: print("Debug messages...", file=sys.stderr, flush=True)


        # One line per agent: <agentId>;<action1;action2;...> actions are "MOVE x y | SHOOT id | THROW x y | HUNKER_DOWN | MESSAGE text"
        
        #print("")
