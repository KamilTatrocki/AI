import pygame
import sys
import random

WIDTH, HEIGHT = 320, 320
SZ = 40
WHITE_COLOR = (255, 255, 255)
BLACK_COLOR = (0, 0, 0)
GRAY_COLOR = (191, 191, 191)
HIGHLIGHT_FROM = (127, 15, 15)
HIGHLIGHT_TO = (0, 191, 0, 76)

EDGE_L = 0x8080808080808080
EDGE_R = 0x0101010101010101

class Game:
    def __init__(self, white=0xffff, black=0xffff000000000000, won=False, player=0):
        self.white = white
        self.black = black
        self.won = won
        self.player = player

def pop_count(x):
    return bin(x).count('1')

def score(game):
    if game.won:
        return (1 if game.player == 1 else -1) * 2048
    return pop_count(game.white) - pop_count(game.black)

def get_next_moves(game):
    if game.won:
        return []
    
    moves = []
    if game.player == 0:
        for i in range(64):
            k = 1 << i
            if game.white & k:
                if k & EDGE_L: idxs = [7, 8]
                elif k & EDGE_R: idxs = [8, 9]
                else: idxs = [7, 8, 9]
                
                for step in idxs:
                    k_prime = k << step
                    if k_prime <= 0xFFFFFFFFFFFFFFFF and not (game.white & k_prime):
                        if step == 8 and (game.black & k_prime):
                            continue
                        new_won = k >= (1 << 48)
                        new_white = (game.white ^ k) | k_prime
                        new_black = game.black & ~k_prime
                        moves.append(Game(new_white, new_black, new_won, 1))
    else:
        for i in range(64):
            k = 1 << i
            if game.black & k:
                if k & EDGE_L: idxs = [8, 9]
                elif k & EDGE_R: idxs = [7, 8]
                else: idxs = [7, 8, 9]
                
                for step in idxs:
                    k_prime = k >> step
                    if k_prime > 0 and not (game.black & k_prime):
                        if step == 8 and (game.white & k_prime):
                            continue
                        new_won = k < (1 << 16)
                        new_black = (game.black ^ k) | k_prime
                        new_white = game.white & ~k_prime
                        moves.append(Game(new_white, new_black, new_won, 0))
    return moves

def minimax(game, depth, alpha, beta, maximizing):
    if depth == 0 or game.won:
        return score(game)
    
    moves = get_next_moves(game)
    if not moves:
        return score(game)
    
    if maximizing:
        max_eval = float('-inf')
        for move in moves:
            eval = minimax(move, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            eval = minimax(move, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def best_move(moves):
    if not moves: return None
    random.shuffle(moves)
    scored_moves = []
    for m in moves:
        s = minimax(m, 3, float('-inf'), float('inf'), m.player == 0)
        scored_moves.append((s, m))
    
    if moves[0].player == 1:
        return min(scored_moves, key=lambda x: x[0])[1]
    else:
        return max(scored_moves, key=lambda x: x[0])[1]

def card(x, y):
    return 8 * (7 - y) + x

def uncard(i):
    y, x = divmod(i, 8)
    return x, 7 - y

def get_moves_from(pos, game):
    x, y = pos
    valid = []
    k_start = 1 << card(x, y)
    if not (game.white & k_start): return []
    
    for dx in [-1, 0, 1]:
        nx, ny = x + dx, y - 1
        if 0 <= nx < 8 and 0 <= ny < 8:
            k_end = 1 << card(nx, ny)
            if not (game.white & k_end):
                if dx == 0 and (game.black & k_end):
                    continue
                valid.append((nx, ny))
    return valid

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT + 40))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)
    
    game = Game()
    selected = None
    busy = False
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    game = Game()
                    selected = None

            if event.type == pygame.MOUSEBUTTONDOWN and not busy and not game.won:
                mx, my = pygame.mouse.get_pos()
                if my < HEIGHT:
                    tx, ty = mx // SZ, my // SZ
                    if game.player == 0:
                        if selected:
                            moves = get_moves_from(selected, game)
                            if (tx, ty) in moves:
                                k_old = 1 << card(*selected)
                                k_new = 1 << card(tx, ty)
                                game.white = (game.white ^ k_old) | k_new
                                game.black &= ~k_new
                                game.won = ty == 0
                                game.player = 1
                                selected = None
                                busy = True
                            else:
                                selected = None
                        
                        if not game.won and (game.white & (1 << card(tx, ty))):
                            selected = (tx, ty)

        if busy and not game.won and game.player == 1:
            moves = get_next_moves(game)
            if moves:
                game = best_move(moves)
            busy = False

        screen.fill(BLACK_COLOR)
        for y in range(8):
            for x in range(8):
                rect = (x * SZ, y * SZ, SZ, SZ)
                color = WHITE_COLOR if (x + y) % 2 == 0 else GRAY_COLOR
                pygame.draw.rect(screen, color, rect)
        
        if selected:
            pygame.draw.rect(screen, HIGHLIGHT_FROM, (selected[0]*SZ, selected[1]*SZ, SZ, SZ), 3)
            for mx, my in get_moves_from(selected, game):
                s = pygame.Surface((SZ, SZ), pygame.SRCALPHA)
                s.fill(HIGHLIGHT_TO)
                screen.blit(s, (mx*SZ, my*SZ))

        for i in range(64):
            x, y = uncard(i)
            center = (x * SZ + SZ // 2, y * SZ + SZ // 2)
            if game.white & (1 << i):
                pygame.draw.circle(screen, WHITE_COLOR, center, 15)
                pygame.draw.circle(screen, BLACK_COLOR, center, 16, 1)
            elif game.black & (1 << i):
                pygame.draw.circle(screen, BLACK_COLOR, center, 16)

        msg = f"{'White' if game.player == 0 else 'Black'} to move"
        if game.won:
            msg = f"{'White' if game.player == 1 else 'Black'} wins!"
        
        text = font.render(msg, True, WHITE_COLOR)
        screen.blit(text, (10, HEIGHT + 10))
        
        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()