import sys
import math
import os
import cv2
import pygame

pygame.init()
pygame.mixer.init()

# Visual Constants
BOARD_WIDTH, BOARD_HEIGHT = 600, 600
TOP_PANEL_HEIGHT = 80
BOTTOM_PANEL_HEIGHT = 80
TOTAL_WIDTH = BOARD_WIDTH  # 600px wide
TOTAL_HEIGHT = TOP_PANEL_HEIGHT + BOARD_HEIGHT + BOTTOM_PANEL_HEIGHT  # 760px high

# Frame Offset Adjustments
BOARD_PADDING = 12
PLAYABLE_WIDTH = BOARD_WIDTH - (BOARD_PADDING * 2)
PLAYABLE_HEIGHT = BOARD_HEIGHT - (BOARD_PADDING * 2)

ROWS, COLS = 8, 8
SQUARE_SIZE_X = PLAYABLE_WIDTH / COLS
SQUARE_SIZE_Y = PLAYABLE_HEIGHT / COLS

# Game Settings: 5 Minutes Total Bank per Player
INITIAL_TIME_LIMIT = 300  

# Colors
RED = (200, 50, 50)
BROWN = (120, 60, 20)  # Player 2 border & crown color
WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
BLUE = (50, 120, 200)
GREEN = (40, 160, 60)
HIGHLIGHT = (255, 255, 100)
PANEL_BG = (45, 45, 45)
TEXT_WHITE = (255, 255, 255)
OVERLAY_BG = (0, 0, 0, 180)

WIN = pygame.display.set_mode((TOTAL_WIDTH, TOTAL_HEIGHT))
pygame.display.set_caption("Suicide Checkers - Custom Face Pieces")
FONT_UI = pygame.font.SysFont("arial", 15, bold=True)
FONT_TIMER = pygame.font.SysFont("arial", 18, bold=True)
FONT_START_BTN = pygame.font.SysFont("arial", 22, bold=True)

# Load Board Image
BOARD_IMAGE_PATH = r"C:\Users\JULIUS\Documents\AMAD\res\783506429_1933456907335283_8118661620158224966_n.png"

try:
    raw_board_img = pygame.image.load(BOARD_IMAGE_PATH)
    BOARD_IMG = pygame.transform.smoothscale(raw_board_img, (BOARD_WIDTH, BOARD_HEIGHT))
except Exception as e:
    print(f"Warning: Could not load board image ({e}).")
    BOARD_IMG = None

# --- LOAD AUDIO FILES ---
BACKGROUND_MUSIC_PATH = r"C:\Users\JULIUS\Documents\AMAD\res\L's theme A.mp3"
KILL_SINGLE_PATH = r"C:\Users\JULIUS\Documents\AMAD\res\faaah.mp3"
KILL_DOUBLE_PATH = r"C:\Users\JULIUS\Documents\AMAD\res\announcer_kill_double_01.mp3"
KILL_TRIPLE_PATH = r"C:\Users\JULIUS\Documents\AMAD\res\announcer_kill_triple_01.mp3"

MUSIC_LOADED = False
SOUND_SINGLE = None
SOUND_DOUBLE = None
SOUND_TRIPLE = None

if os.path.exists(BACKGROUND_MUSIC_PATH):
    try:
        pygame.mixer.music.load(BACKGROUND_MUSIC_PATH)
        MUSIC_LOADED = True
    except Exception as e:
        print(f"Warning: Could not load music ({e}).")

if os.path.exists(KILL_SINGLE_PATH):
    try:
        SOUND_SINGLE = pygame.mixer.Sound(KILL_SINGLE_PATH)
    except Exception as e:
        print(f"Warning: Could not load single kill SFX ({e}).")

if os.path.exists(KILL_DOUBLE_PATH):
    try:
        SOUND_DOUBLE = pygame.mixer.Sound(KILL_DOUBLE_PATH)
    except Exception as e:
        print(f"Warning: Could not load double kill SFX ({e}).")

if os.path.exists(KILL_TRIPLE_PATH):
    try:
        SOUND_TRIPLE = pygame.mixer.Sound(KILL_TRIPLE_PATH)
    except Exception as e:
        print(f"Warning: Could not load triple kill SFX ({e}).")


def capture_player_face(player_name, diameter):
    """Opens webcam, crops face WITHOUT drawing boxes on the captured image."""
    cap = cv2.VideoCapture(0)

    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
    except Exception:
        face_cascade = None

    cropped_face_surface = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = []
        if face_cascade and not face_cascade.empty():
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        display_frame = frame.copy()
        cv2.putText(display_frame, f"{player_name}: Press SPACE to Snap Photo!", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Capture Player Face", display_frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 32:
            if len(faces) > 0:
                x, y, w, h = faces[0]
                face_img = frame[y:y+h, x:x+w]
            else:
                h_f, w_f, _ = frame.shape
                sz = min(h_f, w_f)
                cy, cx = h_f // 2, w_f // 2
                face_img = frame[cy - sz//2: cy + sz//2, cx - sz//2: cx + sz//2]

            face_img = cv2.resize(face_img, (diameter, diameter))
            face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)

            raw_surface = pygame.image.frombuffer(face_rgb.tobytes(), (diameter, diameter), "RGB")

            mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255, 255), (diameter // 2, diameter // 2), diameter // 2)

            cropped_face_surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            cropped_face_surface.blit(raw_surface, (0, 0))
            cropped_face_surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            break

    cap.release()
    cv2.destroyAllWindows()
    return cropped_face_surface


class CheckersGameGUI:
    def __init__(self):
        self.p1_face_tex = None
        self.p2_face_tex = None
        self.reset_game()

    def reset_game(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        self.board = self.create_board()
        self.turn = 1  # 1 = Red, 2 = White/Brown
        self.selected_piece = None
        self.valid_moves = []
        self.is_forced = False
        self.chain_piece = None
        self.turn_capture_count = 0  # Tracks captures during current turn

        self.game_started = False
        self.music_playing = False

        self.red_captures = []
        self.white_captures = []

        self.player_clocks = {
            1: INITIAL_TIME_LIMIT * 1000,
            2: INITIAL_TIME_LIMIT * 1000
        }
        self.last_tick_time = pygame.time.get_ticks()

        self.update_legal_moves()

    def create_board(self):
        board = [[0] * 8 for _ in range(8)]
        for r in range(3):
            for c in range(8):
                if (r + c) % 2 == 0:
                    board[r][c] = 2
        for r in range(5, 8):
            for c in range(8):
                if (r + c) % 2 == 0:
                    board[r][c] = 1
        return board

    def start_photo_capture(self):
        piece_diameter = int(SQUARE_SIZE_X - 16)
        self.p1_face_tex = capture_player_face("PLAYER 1 (RED)", piece_diameter)
        self.p2_face_tex = capture_player_face("PLAYER 2 (BROWN)", piece_diameter)
        self.game_started = True
        self.last_tick_time = pygame.time.get_ticks()

    def get_square_center(self, r, c):
        cx = BOARD_PADDING + (c * SQUARE_SIZE_X) + (SQUARE_SIZE_X / 2)
        cy = TOP_PANEL_HEIGHT + BOARD_PADDING + (r * SQUARE_SIZE_Y) + (SQUARE_SIZE_Y / 2)
        return int(cx), int(cy)

    def play_capture_sound(self):
        """Plays sound effect based on sequence of captures in current turn."""
        self.turn_capture_count += 1
        if self.turn_capture_count == 1:
            if SOUND_SINGLE:
                SOUND_SINGLE.play()
        elif self.turn_capture_count == 2:
            if SOUND_DOUBLE:
                SOUND_DOUBLE.play()
        else:
            if SOUND_TRIPLE:
                SOUND_TRIPLE.play()

    def update_audio_logic(self):
        if not MUSIC_LOADED or not self.game_started:
            return

        p1_under_1min = self.player_clocks[1] <= 60000
        p2_under_1min = self.player_clocks[2] <= 60000

        both_under_1min = p1_under_1min and p2_under_1min
        current_turn_under_1min = (self.turn == 1 and p1_under_1min) or (self.turn == 2 and p2_under_1min)

        should_play = both_under_1min or current_turn_under_1min

        if should_play:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)
            elif self.music_playing and pygame.mixer.music.get_busy():
                pygame.mixer.music.unpause()
            self.music_playing = True
        else:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()

    def update_timer(self):
        if not self.game_started:
            self.last_tick_time = pygame.time.get_ticks()
            return

        current_time = pygame.time.get_ticks()
        delta_time = current_time - self.last_tick_time
        self.last_tick_time = current_time

        if self.player_clocks[self.turn] > 0:
            self.player_clocks[self.turn] -= delta_time
            if self.player_clocks[self.turn] < 0:
                self.player_clocks[self.turn] = 0

        self.update_audio_logic()

    def format_time(self, ms):
        total_seconds = int((ms + 999) // 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def draw_panels(self):
        pygame.draw.rect(WIN, PANEL_BG, (0, 0, TOTAL_WIDTH, TOP_PANEL_HEIGHT))
        pygame.draw.rect(WIN, PANEL_BG, (0, TOP_PANEL_HEIGHT + BOARD_HEIGHT, TOTAL_WIDTH, BOTTOM_PANEL_HEIGHT))

        pygame.draw.line(WIN, BLACK, (0, TOP_PANEL_HEIGHT), (TOTAL_WIDTH, TOP_PANEL_HEIGHT), 3)
        pygame.draw.line(WIN, BLACK, (0, TOP_PANEL_HEIGHT + BOARD_HEIGHT), (TOTAL_WIDTH, TOP_PANEL_HEIGHT + BOARD_HEIGHT), 3)

        p2_txt = FONT_UI.render("BROWN SIDE TAKEN:", True, TEXT_WHITE)
        p1_txt = FONT_UI.render("RED SIDE TAKEN:", True, TEXT_WHITE)
        WIN.blit(p2_txt, (15, 10))
        WIN.blit(p1_txt, (15, TOP_PANEL_HEIGHT + BOARD_HEIGHT + 10))

        # Taken Pieces
        for idx, p in enumerate(self.white_captures):
            x = 20 + (idx * 28)
            y = 45
            color = RED if p in (1, 3) else BROWN
            pygame.draw.circle(WIN, color, (x, y), 11)
            pygame.draw.circle(WIN, BLACK, (x, y), 11, 1)

        for idx, p in enumerate(self.red_captures):
            x = 20 + (idx * 28)
            y = TOP_PANEL_HEIGHT + BOARD_HEIGHT + 45
            color = RED if p in (1, 3) else BROWN
            pygame.draw.circle(WIN, color, (x, y), 11)
            pygame.draw.circle(WIN, BLACK, (x, y), 11, 1)

        # Timers
        w_time_str = self.format_time(self.player_clocks[2])
        r_time_str = self.format_time(self.player_clocks[1])

        w_color = RED if self.player_clocks[2] <= 60000 else (HIGHLIGHT if self.turn == 2 else TEXT_WHITE)
        r_color = RED if self.player_clocks[1] <= 60000 else (HIGHLIGHT if self.turn == 1 else TEXT_WHITE)

        w_timer_txt = FONT_TIMER.render(f"{w_time_str}", True, w_color)
        WIN.blit(w_timer_txt, (350, 25))

        r_timer_txt = FONT_TIMER.render(f"{r_time_str}", True, r_color)
        WIN.blit(r_timer_txt, (350, TOP_PANEL_HEIGHT + BOARD_HEIGHT + 25))

        # New Game Button
        self.btn_new_game = pygame.draw.rect(WIN, RED, (470, TOP_PANEL_HEIGHT + BOARD_HEIGHT + 20, 110, 35), border_radius=5)
        ng_txt = FONT_UI.render("New Game", True, TEXT_WHITE)
        WIN.blit(ng_txt, (485, TOP_PANEL_HEIGHT + BOARD_HEIGHT + 29))

    def draw_board(self):
        if BOARD_IMG:
            WIN.blit(BOARD_IMG, (0, TOP_PANEL_HEIGHT))

    def draw_crown(self, cx, cy, radius, crown_color):
        top_y = cy - radius - 2
        crown_width = 22
        crown_height = 14

        points = [
            (cx - crown_width // 2, top_y),
            (cx - crown_width // 2, top_y - crown_height),
            (cx - crown_width // 4, top_y - (crown_height // 2)),
            (cx, top_y - crown_height - 3),
            (cx + crown_width // 4, top_y - (crown_height // 2)),
            (cx + crown_width // 2, top_y - crown_height),
            (cx + crown_width // 2, top_y)
        ]

        pygame.draw.polygon(WIN, crown_color, points)
        pygame.draw.polygon(WIN, BLACK, points, 1)

    def draw_pieces(self):
        movable_piece_positions = set(m[0] for m in self.valid_moves)

        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) / 2
        core_glow = (255, 255, int(100 + 155 * pulse))
        mid_aura = (255, int(200 + 55 * pulse), 0)
        outer_aura = (255, int(150 + 80 * pulse), 0)

        for r in range(ROWS):
            for c in range(COLS):
                piece = self.board[r][c]
                if piece != 0:
                    cx, cy = self.get_square_center(r, c)
                    radius = int(SQUARE_SIZE_X // 2 - 8)

                    p_owner = 1 if piece in (1, 3) else 2
                    is_active_player = (p_owner == self.turn)
                    can_move = (r, c) in movable_piece_positions

                    base_border_color = RED if p_owner == 1 else BROWN

                    if p_owner == 1 and self.p1_face_tex:
                        rect = self.p1_face_tex.get_rect(center=(cx, cy))
                        WIN.blit(self.p1_face_tex, rect)
                    elif p_owner == 2 and self.p2_face_tex:
                        rect = self.p2_face_tex.get_rect(center=(cx, cy))
                        WIN.blit(self.p2_face_tex, rect)
                    else:
                        pygame.draw.circle(WIN, base_border_color, (cx, cy), radius)

                    if is_active_player and can_move:
                        pygame.draw.circle(WIN, outer_aura, (cx, cy), radius + 5, 2)
                        pygame.draw.circle(WIN, mid_aura, (cx, cy), radius + 3, 3)
                        pygame.draw.circle(WIN, core_glow, (cx, cy), radius, 4)
                        pygame.draw.circle(WIN, WHITE, (cx, cy), radius - 3, 1)
                    else:
                        pygame.draw.circle(WIN, base_border_color, (cx, cy), radius, 5)
                        pygame.draw.circle(WIN, BLACK, (cx, cy), radius + 1, 1)

                    if piece in (3, 4):
                        crown_col = core_glow if (is_active_player and can_move) else base_border_color
                        self.draw_crown(cx, cy, radius, crown_col)

    def draw_highlights(self):
        if self.selected_piece:
            sr, sc = self.selected_piece
            sx = int(BOARD_PADDING + (sc * SQUARE_SIZE_X))
            sy = int(TOP_PANEL_HEIGHT + BOARD_PADDING + (sr * SQUARE_SIZE_Y))
            pygame.draw.rect(WIN, HIGHLIGHT, (sx, sy, int(SQUARE_SIZE_X), int(SQUARE_SIZE_Y)), 4)

            for m in self.valid_moves:
                if m[0] == self.selected_piece:
                    er, ec = m[1]
                    cx, cy = self.get_square_center(er, ec)
                    pygame.draw.circle(WIN, BLUE, (cx, cy), int(SQUARE_SIZE_X // 6))

    def draw_start_overlay(self):
        if not self.game_started:
            overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
            overlay.fill(OVERLAY_BG)
            WIN.blit(overlay, (0, TOP_PANEL_HEIGHT))

            btn_w, btn_h = 240, 50
            btn_x = (TOTAL_WIDTH - btn_w) // 2
            btn_y = TOP_PANEL_HEIGHT + (BOARD_HEIGHT - btn_h) // 2

            self.btn_start = pygame.draw.rect(WIN, GREEN, (btn_x, btn_y, btn_w, btn_h), border_radius=10)
            pygame.draw.rect(WIN, TEXT_WHITE, (btn_x, btn_y, btn_w, btn_h), width=2, border_radius=10)

            btn_txt = FONT_START_BTN.render("TAKE PHOTOS & START", True, TEXT_WHITE)
            txt_rect = btn_txt.get_rect(center=self.btn_start.center)
            WIN.blit(btn_txt, txt_rect)

    def is_player_piece(self, piece, player):
        return (piece in (1, 3)) if player == 1 else (piece in (2, 4))

    def update_legal_moves(self):
        jumps, regular_moves = [], []
        if self.chain_piece:
            r, c = self.chain_piece
            p_jumps, _ = self.get_piece_moves(r, c)
            jumps.extend(p_jumps)
        else:
            for r in range(8):
                for c in range(8):
                    if self.is_player_piece(self.board[r][c], self.turn):
                        p_jumps, p_moves = self.get_piece_moves(r, c)
                        jumps.extend(p_jumps)
                        regular_moves.extend(p_moves)

        if jumps:
            self.valid_moves, self.is_forced = jumps, True
        else:
            self.valid_moves, self.is_forced = regular_moves, False

    def get_piece_moves(self, r, c):
        piece = self.board[r][c]
        player = 1 if piece in (1, 3) else 2
        is_king = piece in (3, 4)

        forward = -1 if player == 1 else 1
        jumps, moves = [], []

        all_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        forward_dirs = [(forward, -1), (forward, 1)]

        if is_king:
            for dr, dc in all_dirs:
                mid_piece_pos = None
                step = 1
                while True:
                    tr, tc = r + (dr * step), c + (dc * step)
                    if not (0 <= tr < 8 and 0 <= tc < 8):
                        break
                    
                    target_piece = self.board[tr][tc]

                    if mid_piece_pos is None:
                        if target_piece == 0:
                            moves.append(((r, c), (tr, tc)))
                        elif not self.is_player_piece(target_piece, player):
                            mid_piece_pos = (tr, tc)
                        else:
                            break
                    else:
                        if target_piece == 0:
                            jumps.append(((r, c), (tr, tc), mid_piece_pos))
                        else:
                            break
                    step += 1
        else:
            for dr, dc in all_dirs:
                mid_r, mid_c = r + dr, c + dc
                land_r, land_c = r + (2 * dr), c + (2 * dc)
                if 0 <= land_r < 8 and 0 <= land_c < 8:
                    mid_piece = self.board[mid_r][mid_c]
                    land_piece = self.board[land_r][land_c]
                    if (
                        mid_piece != 0
                        and not self.is_player_piece(mid_piece, player)
                        and land_piece == 0
                    ):
                        jumps.append(((r, c), (land_r, land_c), (mid_r, mid_c)))

            for dr, dc in forward_dirs:
                tr, tc = r + dr, c + dc
                if 0 <= tr < 8 and 0 <= tc < 8 and self.board[tr][tc] == 0:
                    moves.append(((r, c), (tr, tc)))

        return jumps, moves

    def handle_click(self, pos):
        x, y = pos

        if self.btn_new_game.collidepoint(pos):
            self.reset_game()
            return

        if not self.game_started:
            if hasattr(self, 'btn_start') and self.btn_start.collidepoint(pos):
                self.start_photo_capture()
            return

        board_top = TOP_PANEL_HEIGHT + BOARD_PADDING
        board_bottom = TOP_PANEL_HEIGHT + BOARD_HEIGHT - BOARD_PADDING
        board_left = BOARD_PADDING
        board_right = BOARD_WIDTH - BOARD_PADDING

        if board_top <= y < board_bottom and board_left <= x < board_right:
            col = int((x - board_left) // SQUARE_SIZE_X)
            row = int((y - board_top) // SQUARE_SIZE_Y)

            if self.selected_piece:
                move_found = next(
                    (
                        m
                        for m in self.valid_moves
                        if m[0] == self.selected_piece and m[1] == (row, col)
                    ),
                    None,
                )

                if move_found:
                    is_capture = len(move_found) == 3
                    self.make_move(move_found)
                    land_pos = move_found[1]

                    if is_capture:
                        self.play_capture_sound()
                        add_jumps, _ = self.get_piece_moves(land_pos[0], land_pos[1])
                        if add_jumps:
                            self.chain_piece = land_pos
                            self.selected_piece = land_pos
                            self.update_legal_moves()
                            return

                    self.turn_capture_count = 0
                    self.chain_piece = None
                    self.selected_piece = None
                    self.turn = 2 if self.turn == 1 else 1
                    self.update_legal_moves()
                    return

            if not self.chain_piece and self.is_player_piece(self.board[row][col], self.turn):
                if not self.is_forced or any(m[0] == (row, col) for m in self.valid_moves):
                    self.selected_piece = (row, col)

    def make_move(self, move):
        (r1, c1), (r2, c2) = move[0], move[1]
        piece = self.board[r1][c1]

        self.board[r1][c1] = 0
        self.board[r2][c2] = piece

        if len(move) == 3:
            cr, cc = move[2]
            captured = self.board[cr][cc]
            self.board[cr][cc] = 0

            if self.turn == 1:
                self.red_captures.append(captured)
            else:
                self.white_captures.append(captured)

        if piece == 1 and r2 == 0:
            self.board[r2][c2] = 3
        elif piece == 2 and r2 == 7:
            self.board[r2][c2] = 4

    def check_winner(self):
        if self.player_clocks[1] <= 0:
            return "BROWN WINS! (RED ran out of time)"
        if self.player_clocks[2] <= 0:
            return "RED WINS! (BROWN ran out of time)"

        p1_pieces = sum(row.count(1) + row.count(3) for row in self.board)
        p2_pieces = sum(row.count(2) + row.count(4) for row in self.board)

        if p1_pieces == 0:
            return "RED WINS! (Ran out of pieces)"
        if p2_pieces == 0:
            return "BROWN WINS! (Ran out of pieces)"
        if not self.valid_moves:
            winner = "RED" if self.turn == 1 else "BROWN"
            return f"{winner} WINS! (No legal moves left)"

        return None


def main():
    game = CheckersGameGUI()
    clock = pygame.time.Clock()

    while True:
        clock.tick(60)

        winner = game.check_winner()
        if not winner:
            game.update_timer()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_click(pygame.mouse.get_pos())

        game.draw_board()
        game.draw_highlights()
        game.draw_pieces()
        game.draw_panels()
        game.draw_start_overlay()

        turn_str = "RED" if game.turn == 1 else "BROWN"
        status_str = (
            " | MULTI-TAKE!"
            if game.chain_piece
            else (" | FORCED JUMP!" if game.is_forced else "")
        )

        if winner:
            pygame.display.set_caption(f"GAME OVER: {winner}")
        elif not game.game_started:
            pygame.display.set_caption("Suicide Checkers - Take Photos to Start")
        else:
            pygame.display.set_caption(f"Suicide Checkers - Turn: {turn_str}{status_str}")

        pygame.display.flip()


if __name__ == "__main__":
    main()