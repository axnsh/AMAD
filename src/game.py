import os
import sys
import math
import pygame

from src.settings import (
    BOARD_WIDTH, BOARD_HEIGHT, TOP_PANEL_HEIGHT, BOTTOM_PANEL_HEIGHT,
    TOTAL_WIDTH, TOTAL_HEIGHT, BOARD_PADDING, PLAYABLE_WIDTH, PLAYABLE_HEIGHT,
    ROWS, COLS, SQUARE_SIZE_X, SQUARE_SIZE_Y, INITIAL_TIME_LIMIT,
    RED, BROWN, WHITE, BLACK, BLUE, GREEN, HIGHLIGHT, PANEL_BG, TEXT_WHITE,
    OVERLAY_BG, GOLD,
    WIN, FONT_UI, FONT_TIMER, FONT_START_BTN, FONT_POPUP_TITLE, FONT_POPUP_BTN,
    BOARD_IMG, MUSIC_LOADED, SOUND_SINGLE, SOUND_DOUBLE, SOUND_TRIPLE, SOUND_CELEBRATE,
    get_asset_path
)
from src.board import BoardManager
from src.camera import capture_player_face


class CheckersGameGUI:
    def __init__(self):
        self.bm = BoardManager()
        self.p1_face_tex = None
        self.p2_face_tex = None
        self.cat_img = None

        # Load Laughing Cat Image for End-Game Popup
        cat_img_path = get_asset_path("cat_laugh.png")
        if os.path.exists(cat_img_path):
            try:
                self.cat_img = pygame.image.load(cat_img_path).convert_alpha()
                self.cat_img = pygame.transform.smoothscale(self.cat_img, (110, 110))
            except Exception as e:
                print(f"Warning: Could not load cat image ({e})")

        self.reset_game()

    def reset_game(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        if SOUND_CELEBRATE:
            SOUND_CELEBRATE.stop()

        self.bm.board = self.bm.create_board()
        self.turn = 1  # 1 = Red, 2 = White/Brown
        self.selected_piece = None
        self.valid_moves = []
        self.is_forced = False
        self.chain_piece = None
        self.turn_capture_count = 0  # Tracks captures during current turn

        self.game_started = False
        self.music_playing = False
        self.celebration_playing = False

        self.red_captures = []
        self.white_captures = []

        self.popup_btn_new_game = None
        self.popup_btn_exit_game = None

        self.player_clocks = {
            1: INITIAL_TIME_LIMIT * 1000,
            2: INITIAL_TIME_LIMIT * 1000
        }
        self.last_tick_time = pygame.time.get_ticks()

        self.update_legal_moves()

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

    def play_celebration_sound(self):
        """Starts the looping victory theme once, on the winning frame."""
        if not self.celebration_playing and SOUND_CELEBRATE:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            SOUND_CELEBRATE.play(loops=-1)
            self.celebration_playing = True
            self.music_playing = False

    def update_audio_logic(self):
        if not MUSIC_LOADED or not self.game_started:
            return

        p1_under_1min = self.player_clocks[1] <= 60000
        p2_under_1min = self.player_clocks[2] <= 60000

        current_turn_under_1min = (self.turn == 1 and p1_under_1min) or (self.turn == 2 and p2_under_1min)

        should_play = current_turn_under_1min

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

        # New Game Button (Bottom Panel)
        self.btn_panel_new_game = pygame.draw.rect(WIN, RED, (470, TOP_PANEL_HEIGHT + BOARD_HEIGHT + 20, 110, 35), border_radius=5)
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
                piece = self.bm.board[r][c]
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

    def draw_winner_popup(self, screen, winner_str=""):
        screen_w, screen_h = screen.get_size()

        # Overlay background
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        screen.blit(overlay, (0, 0))

        # Compact box dimensions
        box_w, box_h = 440, 260
        box_x = (screen_w - box_w) // 2
        box_y = (screen_h - box_h) // 2

        pygame.draw.rect(screen, (30, 30, 30), (box_x, box_y, box_w, box_h), border_radius=14)
        pygame.draw.rect(screen, (255, 215, 0), (box_x, box_y, box_w, box_h), width=3, border_radius=14)

        font_title = pygame.font.SysFont("arial", 24, bold=True)
        font_sub = pygame.font.SysFont("arial", 15, bold=True)
        font_sarcasm = pygame.font.SysFont("arial", 16, bold=True)

        t_surf = font_title.render("CONGRATULATIONS!", True, (255, 215, 0))
        s_surf = font_sub.render(winner_str, True, (245, 245, 245))
        sarcasm_surf = font_sarcasm.render("You're so good at losing! Congrats!", True, (255, 120, 120))

        screen.blit(t_surf, (box_x + (box_w - t_surf.get_width()) // 2, box_y + 16))
        screen.blit(s_surf, (box_x + (box_w - s_surf.get_width()) // 2, box_y + 44))
        screen.blit(sarcasm_surf, (box_x + (box_w - sarcasm_surf.get_width()) // 2, box_y + 66))

        # Cat Image
        if self.cat_img:
            cat_x = box_x + (box_w - self.cat_img.get_width()) // 2
            screen.blit(self.cat_img, (cat_x, box_y + 92))

        # Popup Action Buttons (Closer together & higher up)
        btn_w, btn_h = 140, 38
        spacing = 16  # Gap between buttons
        btn_y = box_y + 208  # Shifted higher up inside the popup

        total_buttons_w = (btn_w * 2) + spacing
        start_x = box_x + (box_w - total_buttons_w) // 2

        self.popup_btn_new_game = pygame.Rect(start_x, btn_y, btn_w, btn_h)
        self.popup_btn_exit_game = pygame.Rect(start_x + btn_w + spacing, btn_y, btn_w, btn_h)

        mx, my = pygame.mouse.get_pos()
        ng_color = (40, 167, 69) if self.popup_btn_new_game.collidepoint(mx, my) else (30, 126, 52)
        ex_color = (220, 53, 69) if self.popup_btn_exit_game.collidepoint(mx, my) else (167, 29, 42)

        pygame.draw.rect(screen, ng_color, self.popup_btn_new_game, border_radius=8)
        pygame.draw.rect(screen, ex_color, self.popup_btn_exit_game, border_radius=8)

        font_btn = pygame.font.SysFont("arial", 15, bold=True)
        ng_lbl = font_btn.render("NEW GAME", True, (255, 255, 255))
        ex_lbl = font_btn.render("EXIT GAME", True, (255, 255, 255))

        screen.blit(ng_lbl, (self.popup_btn_new_game.x + (btn_w - ng_lbl.get_width()) // 2, self.popup_btn_new_game.y + 10))
        screen.blit(ex_lbl, (self.popup_btn_exit_game.x + (btn_w - ex_lbl.get_width()) // 2, self.popup_btn_exit_game.y + 10))
        
    def update_legal_moves(self):
        jumps, regular_moves = [], []
        if self.chain_piece:
            r, c = self.chain_piece
            p_jumps, _ = self.bm.get_piece_moves(r, c)
            jumps.extend(p_jumps)
        else:
            for r in range(8):
                for c in range(8):
                    if self.bm.is_player_piece(self.bm.board[r][c], self.turn):
                        p_jumps, p_moves = self.bm.get_piece_moves(r, c)
                        jumps.extend(p_jumps)
                        regular_moves.extend(p_moves)

        if jumps:
            self.valid_moves, self.is_forced = jumps, True
        else:
            self.valid_moves, self.is_forced = regular_moves, False

    def handle_click(self, pos):
        x, y = pos

        # Check popup interactions if game is over
        winner = self.check_winner()
        if winner:
            if self.popup_btn_new_game and self.popup_btn_new_game.collidepoint(pos):
                self.reset_game()
            elif self.popup_btn_exit_game and self.popup_btn_exit_game.collidepoint(pos):
                if SOUND_CELEBRATE:
                    SOUND_CELEBRATE.stop()
                pygame.quit()
                sys.exit()
            return

        # Check panel New Game button
        if hasattr(self, 'btn_panel_new_game') and self.btn_panel_new_game.collidepoint(pos):
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
                    self.bm.make_move(move_found, self.turn, self.red_captures, self.white_captures)
                    land_pos = move_found[1]

                    if is_capture:
                        self.play_capture_sound()
                        add_jumps, _ = self.bm.get_piece_moves(land_pos[0], land_pos[1])
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

            if not self.chain_piece and self.bm.is_player_piece(self.bm.board[row][col], self.turn):
                if not self.is_forced or any(m[0] == (row, col) for m in self.valid_moves):
                    self.selected_piece = (row, col)

    def check_winner(self):
        if self.player_clocks[1] <= 0:
            return "BROWN WINS! (RED ran out of time)"
        if self.player_clocks[2] <= 0:
            return "RED WINS! (BROWN ran out of time)"

        p1_pieces = sum(row.count(1) + row.count(3) for row in self.bm.board)
        p2_pieces = sum(row.count(2) + row.count(4) for row in self.bm.board)

        if p1_pieces == 0:
            return "RED WINS! (Ran out of pieces)"
        if p2_pieces == 0:
            return "BROWN WINS! (Ran out of pieces)"
        if not self.valid_moves:
            winner = "RED" if self.turn == 1 else "BROWN"
            return f"{winner} WINS! (No legal moves left)"

        return None