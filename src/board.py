class BoardManager:
    """Holds the 8x8 board array and the move-generation rules.

    Extracted as-is from the original CheckersGameGUI (create_board,
    is_player_piece, get_piece_moves, make_move) — no logic changed,
    just moved out into its own file.
    """

    def __init__(self):
        self.board = self.create_board()

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

    def is_player_piece(self, piece, player):
        return (piece in (1, 3)) if player == 1 else (piece in (2, 4))

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

    def make_move(self, move, turn, red_captures, white_captures):
        (r1, c1), (r2, c2) = move[0], move[1]
        piece = self.board[r1][c1]

        self.board[r1][c1] = 0
        self.board[r2][c2] = piece

        if len(move) == 3:
            cr, cc = move[2]
            captured = self.board[cr][cc]
            self.board[cr][cc] = 0

            if turn == 1:
                red_captures.append(captured)
            else:
                white_captures.append(captured)

        if piece == 1 and r2 == 0:
            self.board[r2][c2] = 3
        elif piece == 2 and r2 == 7:
            self.board[r2][c2] = 4