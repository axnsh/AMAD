import sys
import pygame

from src.game import CheckersGameGUI
from src.settings import WIN


def main():
    game = CheckersGameGUI()
    clock = pygame.time.Clock()

    while True:
        clock.tick(60)

        winner = game.check_winner()
        if not winner:
            game.update_timer()
        else:
            game.play_celebration_sound()

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

        if winner:
            game.draw_winner_popup(WIN, winner)

        turn_str = "RED" if game.turn == 1 else "BROWN"
        status_str = (
            " | MULTI-TAKE!"
            if game.chain_piece
            else (" | FORCED JUMP!" if game.is_forced else "")
        )

        if winner:
            pygame.display.set_caption(f"GAME OVER: {winner}")
        elif not game.game_started:
            pygame.display.set_caption("AMAD - Take Photos to Start")
        else:
            pygame.display.set_caption(f"AMAD - Turn: {turn_str}{status_str}")

        pygame.display.flip()


if __name__ == "__main__":
    main()