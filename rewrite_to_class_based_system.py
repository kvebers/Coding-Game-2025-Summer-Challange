import sys
import math
from collections import deque
import time

# Win the water fight by controlling the most territory, or out-soak your opponent!

C_DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
g_blocked_postions = []


def manhatan_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)

class Map():
    def __init__(self, width, height):
        self.game_map = [[Tiles(0, 0, 0) for _ in range(width)] for _ in range(height)]
        self.width = width
        self.height = height

    def valid_tile(self, x, y):
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        if self.game_map[y][x].tile_type != 0:
            return False
        if (x, y) in g_blocked_postions:
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

    def execute_command(self):
        print(self.command_to_execute)

    def append_message(self, time):
        message = "Unknown"
        self.command_to_execute += f";MESSAGE {message} {time:2f} ms"

    def find_closest_enemy(self, enemys, game):
        enemy_to_return = None
        current_man_dist = 1000
        for enemy in enemys:
            man_dist = manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y)
            if (man_dist < current_man_dist):
                enemy_to_return = enemy
                current_man_dist = man_dist
        return enemy_to_return

class Sniper(Agent):
    def __init__(self, agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs):
        super().__init__(agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs)

    def append_message(self, time):
        message = "Sniper"
        self.command_to_execute += f";MESSAGE {message} {time:.2f} ms"


    def estimate_attack_pattern(self, enemys, game):
        enemy = self.find_closest_enemy(enemys, game)
        if enemy != None and self.cooldown == 0 and manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y) <= self.optimal_range * 2:
            self.command_to_execute += f"; SHOOT {enemy.agent_id}"
        else:
            self.command_to_execute += f"; HUNKER_DOWN"

    def retreat(self, enemy, game):
        previous_distance = manhatan_distance(self.x, self.y, enemy.x, enemy.y)
        previous_pos = (self.x, self.y)
        for dx, dy in C_DIRECTIONS:
            nx, ny = self.x + dx, self.y + dy
            if (0 <= nx < game.width and 0 <= ny < game.height):
                if (game.game_map[ny][nx].tile_type == 0):
                    new = manhatan_distance(nx, ny, enemy.x, enemy.y)
                    if (new > previous_distance):
                        previous_pos = (nx, ny)
                        previous_distance = new
        return previous_pos


    def calculate_movement(self, enemys, game):
        enemy = self.find_closest_enemy(enemys, game)
        if enemy == None:
            self.command_to_execute += f"{self.agent_id}; MOVE {self.x} {self.y}"
        elif (manhatan_distance(self.x, self.y, enemy.x, enemy.y) > enemy.optimal_range * 2 + 2):
            (x, y) = game.bfs(self.x, self.y, enemy.x, enemy.y)
            self.new_x = x
            self.new_y = y
            g_blocked_postions.append((x, y))
            self.command_to_execute += f"{self.agent_id}; MOVE {x} {y}"
        else:
            (x, y) = self.retreat(enemy, game)
            self.command_to_execute += f"{self.agent_id}; MOVE {x} {y}"

class Bomber(Agent):
    def __init__(self, agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs):
        super().__init__(agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs)

    def append_message(self, time):
        message = "Bomber"
        self.command_to_execute += f";MESSAGE {message} {time:.2f} ms"

    def estimate_attack_pattern(self, enemys, game):
        enemy = self.find_closest_enemy(enemys, game)
        if enemy != None and self.cooldown == 0 and manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y) <= self.optimal_range * 2:
            self.command_to_execute += f"; SHOOT {enemy.agent_id}"
        else:
            self.command_to_execute += f"; HUNKER_DOWN"

    def calculate_movement(self, enemys, game):
        self.command_to_execute += f"{self.agent_id}; MOVE {game.width // 2} {game.height // 2}"

class RifleMan(Agent):
    def __init__(self, agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs):
        super().__init__(agent_id, player, shoot_cooldown, optimal_range, soaking_power, splash_bombs)

    def append_message(self, time):
        message = "RifleMan"
        self.command_to_execute += f";MESSAGE {message} {time:.2f} ms"

    def calculate_movement(self, enemys, game):
        self.command_to_execute += f"{self.agent_id}; MOVE {game.width // 2} {game.height // 2}"

    def estimate_attack_pattern(self, enemys, game):
        enemy = self.find_closest_enemy(enemys, game)
        if enemy != None and self.cooldown == 0 and manhatan_distance(self.new_x, self.new_y, enemy.x, enemy.y) <= self.optimal_range * 2:
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

# game loop
while True:
    agent_count = int(input())  # Total number of agents still in the game
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
    for agent_id, agent in agents.items():
        if (agent.player == my_id):
            my_agents.append(agent)
        else:
            enemy_agents.append(agent)
    my_agent_count = int(input())  # Number of alive agents controlled by you
    g_blocked_postions.clear()
    for i in range(my_agent_count):
        start_time = time.time()
        my_agents[i].calculate_movement(enemy_agents, game)
        my_agents[i].estimate_attack_pattern(enemy_agents, game)
        end_time = time.time()
        delta_time = (end_time - start_time)*1000
        my_agents[i].append_message(delta_time)
        my_agents[i].execute_command()
        # Write an action using print
        # To debug: print("Debug messages...", file=sys.stderr, flush=True)


        # One line per agent: <agentId>;<action1;action2;...> actions are "MOVE x y | SHOOT id | THROW x y | HUNKER_DOWN | MESSAGE text"
