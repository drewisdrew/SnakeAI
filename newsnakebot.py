import pygame, sys, random, heapq
from collections import deque
from math import floor

# !!! SET TO FALSE FOR PLAYER MOVEMENT !!!
pathfinding = True

pygame.init()
screen = pygame.display.set_mode((900, 900))
clock = pygame.time.Clock()
pygame.display.set_caption("Snake Bot AI") if pathfinding else pygame.display.set_caption("Snake Player")

# initialization stuff
def reset_game():
    global snake, snake_set, di, score, timer, dead, caught, target, path, apple
    snake = [random.randint(0, 399)]
    snake_set = set(snake)
    di = 1 if snake[0] > 199 else 4
    score = 3
    timer = 0
    dead = False
    caught = True
    target = None
    path = []
    apple = -1

reset_game()

# this creates the map
grid = []
x, y = 40, 40
for _ in range(400):
    grid.append(pygame.Rect((x, y, 39, 39)))
    if x < 800:
        x += 41
    else:
        x = 40
        y += 41

def get_neighbors(tile):
    # this gets the neighboring tiles
    neighbors = []
    hort = tile % 20
    if hort != 19: neighbors.append(tile + 1)
    if hort != 0:  neighbors.append(tile - 1)
    if tile + 20 <= 399: neighbors.append(tile + 20)
    if tile - 20 >= 0:   neighbors.append(tile - 20)
    return neighbors

def flood_fill(start, obstacles):
    # this checks if the place is safe and has space for the snake
    if start in obstacles:
        return 0
    visited = {start}
    queue = deque([start])
    
    while queue:
        curr = queue.popleft()
        for nxt in get_neighbors(curr):
            # Crucial: Check AND add to visited before appending to prevent duplicate loops
            if nxt not in visited and nxt not in obstacles:
                visited.add(nxt)
                queue.append(nxt)
    return len(visited)

def find_path(start, goal, obstacles):
    # A* pathfinding
    if start == goal:
        return [start]
        
    avert, ahort = goal // 20, goal % 20
    start_vert, start_hort = start // 20, start % 20
    h = abs(avert - start_vert) + abs(ahort - start_hort)
    
    open_heap = []
    # Heap stores (f_score, g_score, current_node)
    heapq.heappush(open_heap, (h, 0, start))
    
    came_from = {}
    g_score = {start: 0}
    closed_set = set() # Prevents Heap explosions
    
    while open_heap:
        f, g, current = heapq.heappop(open_heap)
        
        if current in closed_set:
            continue
        closed_set.add(current)
        
        if current == goal:
            p = []
            while current in came_from:
                p.append(current)
                current = came_from[current]
            p.append(start)
            p.reverse()
            return p
            
        for neighbor in get_neighbors(current):
            if neighbor in obstacles and neighbor != goal:
                continue
            if neighbor in closed_set:
                continue
                
            tentative_g = g + 1
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                nvert, nhort = neighbor // 20, neighbor % 20
                h_dist = abs(avert - nvert) + abs(ahort - nhort)
                heapq.heappush(open_heap, (tentative_g + h_dist, tentative_g, neighbor))
                
    return []

def predict_virtual_safety(real_path):
    # simulates future to make sure snake doesn't trap itself
    if not real_path or len(real_path) < 2:
        return False

    virtual_snake = snake.copy()
    
    for step in real_path[1:]:
        virtual_snake.append(step)
        if len(virtual_snake) > score:
            virtual_snake.pop(0)

    virtual_set = set(virtual_snake)
    escape_path = find_path(virtual_snake[-1], virtual_snake[0], virtual_set)
    return len(escape_path) > 0

def recalculate_path():
    # chooses the safest route (apple -> stall -> OH SHIT OH FUCK I'M GONNA DIE GOD PLEASE HELP ME)
    head = snake[-1]
    tail = snake[0]
    
    # 1. Aggressive Mode: Safely path to apple
    apple_path = find_path(head, apple, snake_set)
    if apple_path and len(apple_path) > 1:
        if predict_virtual_safety(apple_path):
            return apple_path
            
    # 2. Survival Mode: Stall by taking a long path to the tail.
    sim_obstacles = snake_set.copy()
    if len(snake) >= score:
        sim_obstacles.discard(tail)

    next_tail = snake[1] if len(snake) > 1 else tail
    
    best_stall_move = None
    max_dist = -1
    
    for n in get_neighbors(head):
        if n not in sim_obstacles:
            # check if tail is reachable
            p_to_tail = find_path(n, next_tail, sim_obstacles)
            if p_to_tail:
                dist = len(p_to_tail)
                if dist > max_dist:
                    max_dist = dist
                    best_stall_move = n
                    
    if best_stall_move is not None:
        return [head, best_stall_move]

    # 3. OSOFIGDGPHM mode AKA Panic Mode: No path to tail exists at all. 
    # Grab the neighbor with the most flood-fill space as a last resort.
    best_neighbor = None
    max_space = -1
    for n in get_neighbors(head):
        if n not in sim_obstacles:
            space = flood_fill(n, sim_obstacles)
            if space > max_space:
                max_space = space
                best_neighbor = n
                
    if best_neighbor is not None:
        return [head, best_neighbor]
        
    return []

# game loop
if pathfinding:
    running = True
    prun = False
else:
    prun = True
    running = False
while running:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


    # wincon check
    # this will never happen idfk why i added ts
    if len(snake) >= 400:
        print("Bot Won!")
        dead = True

    # spawn apple
    if caught and not dead:
        while caught:
            apple = random.randint(0, 399)
            if apple not in snake_set:
                caught = False
                score += 1
                target = apple
                path = []

    # ai pathfinding execution
    # this has annihilated my sanity
    if pathfinding and timer % 10 == 0 and not dead:
        # Recalculate if the path is empty OR if we've reached the final step
        if len(path) <= 1:
            path = recalculate_path()

        if len(path) > 1:
            next_tile = path[1]
            
            current_obstacles = snake_set.copy()
            if len(snake) >= score:
                current_obstacles.discard(snake[0])
            
            if next_tile not in current_obstacles:
                snake.append(next_tile)
                snake_set.add(next_tile)
                path.pop(0)
            else:
                path = recalculate_path()
                if len(path) > 1:
                    next_tile = path[1]
                    if next_tile not in current_obstacles:
                        snake.append(next_tile)
                        snake_set.add(next_tile)
                        path.pop(0)
                    else:
                        dead = True
                else:
                    dead = True
        else:
            dead = True

        # trims the tail
        if not dead and len(snake) > score:
            tail = snake.pop(0)
            snake_set.discard(tail)
            
        if snake[-1] == apple:
            caught = True
            path = []

    # Rendering 
    screen.fill((0, 0, 0))
    pygame.display.set_caption(f"Snake Bot AI | Point: {score}") if pathfinding else pygame.display.set_caption(f"Snake Bot AI | Point: {score}")

    for i, quad in enumerate(grid):
        if i == apple:
            pygame.draw.rect(screen, (205, 0, 0), quad)
        elif i in snake_set:
            if dead:
                pygame.draw.rect(screen, (255, 50, 50), quad)
            elif i == snake[-1]:
                pygame.draw.rect(screen, (0, 205, 185), quad)
            elif len(snake) > 1 and i == snake[-2]:
                pygame.draw.rect(screen, (0, 205, 135), quad)
            else:
                pygame.draw.rect(screen, (0, 205, 0), quad)
        else:
            pygame.draw.rect(screen, (105, 105, 105), quad)

    pygame.display.flip()

    if dead:
        pygame.time.delay(3000 - score) # Pause so you can see how it died
        reset_game()

    timer += 1
    clock.tick(600) if pathfinding else clock.tick(60)

while prun:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            prun = False
            break
        if event.type == pygame.KEYDOWN:
            
            if event.key == pygame.K_w and di not in (1, 4) and not buffer: di, buffer = 1, True
            elif event.key == pygame.K_d and di not in (2, 3) and not buffer: di, buffer = 2, True
            elif event.key == pygame.K_a and di not in (2, 3) and not buffer: di, buffer = 3, True
            elif event.key == pygame.K_s and di not in (1, 4) and not buffer: di, buffer = 4, True

    if not prun: break

    # Wait one second to start so the player can react
    if timer == 1:
        clock.tick(1)

    # Spawn apple safely
    if caught:
        while caught:
            apple = random.randint(0, 399)
            if apple not in snake_set:
                caught = False
                score += 1
                target = apple

    # Movement happens every 10 frames (6 steps per second at 60 FPS)
    if timer % 10 == 0:
        buffer = False
        head = snake[-1]
        if di == 1:
            if head < 20: dead = True
            next_tile = head - 20
        elif di == 2:
            if (head + 1) % 20 == 0: dead = True
            next_tile = head + 1
        elif di == 3:
            if head % 20 == 0: dead = True
            next_tile = head - 1
        else:
            if head >= 380: dead = True
            next_tile = head + 20

        if not dead:
            if next_tile in snake_set:
                dead = True
            else:
                snake.append(next_tile)
                snake_set.add(next_tile)

                # Trim the tail
                if len(snake) > score:
                    tail = snake.pop(0)
                    snake_set.discard(tail)

    if snake[-1] == apple:
        caught = True

    # Rendering
    screen.fill((0, 0, 0))
    for i, quad in enumerate(grid): 
        if i == apple:
            pygame.draw.rect(screen, (205, 0, 0), quad)
        elif i in snake_set:
            if i == snake[-1]:
                pygame.draw.rect(screen, (0, 205, 185), quad)
            elif len(snake) > 1 and i == snake[-2]:
                pygame.draw.rect(screen, (0, 205, 135), quad)
            else:
                pygame.draw.rect(screen, (0, 205, 0), quad)
        else:
            pygame.draw.rect(screen, (105, 105, 105), quad)

    pygame.display.flip()

    # Handle death by resetting instead of locking up the app
    if dead:
        pygame.time.delay(1500) 
        reset_game()

    timer += 1
    clock.tick(60)

pygame.quit()
sys.exit()