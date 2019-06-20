#! python 3
# simulateGame.py - simulate online games of 2048.

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import numpy as np

import time

url2048 = 'https://play2048.co/'


class Session:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.get(url2048)

    def end_session(self):
        """closes browser."""
        self.driver.close()

    def restart_game(self):
        restart_btn = self.driver.find_element('class name', 'restart-button')
        restart_btn.click()

    def right(self):
        """Move right."""
        action = ActionChains(self.driver)
        action.key_down(Keys.ARROW_RIGHT)
        action.perform()

    def left(self):
        """Move left."""
        action = ActionChains(self.driver)
        action.key_down(Keys.ARROW_LEFT)
        action.perform()

    def up(self):
        """Move up."""
        action = ActionChains(self.driver)
        action.key_down(Keys.ARROW_UP)
        action.perform()

    def down(self):
        """Move down."""
        action = ActionChains(self.driver)
        action.key_down(Keys.ARROW_DOWN)
        action.perform()

    def get_board_state(self):
        """Returns a list of web elements of 'tiles-state' on board"""
        board = self.driver.find_element('class name', 'tile-container')
        return board.find_elements('class name', 'tile-inner')

    def did_move(self, previous_board_state):
        """Returns bool if a move had been done.

        previous_board_state: list of web elements.
        """
        return previous_board_state != self.get_board_state()

    def get_score(self):
        """Returns the score of the current game."""
        score = self.driver.find_element('class name', 'score-container')
        return int(score.text.split()[0])
        pass

    def get_highest_tile(self):
        """Returns value of highest tile on board."""
        board = self.get_board_state()
        tiles = [int(tile.text) for tile in board if tile]
        return max(tiles)

    def is_game_over(self):
        """Returns True if game is over"""
        message = self.driver.find_element('xpath',
                                           '/html/body/div[3]/div[4]/div[1]')
        if message.get_attribute('class') == 'game-message game-over':
            return True

    def is_win(self):
        """Returns True if reached 2048"""
        message = self.driver.find_element('xpath',
                                           '/html/body/div[3]/div[4]/div[1]')
        if message.get_attribute('class') == 'game-message game-won':
            return True

    # Play games based on different strategies
    def total_random_game(self):
        """Play a game.

        Moves strategy: every move is randomly picked.
        Returns: (Score, Highest tile, Number of moves)
        """
        moves = [self.right, self.left, self.up, self.down]
        moves_count = 0
        while not (self.is_game_over() or self.is_win()):
            np.random.shuffle(moves)
            current_board = self.get_board_state()
            for i in range(4):
                moves[i]()
                if self.did_move(current_board):
                    moves_count += 1
                    break
        return (self.get_score(),
                self.get_highest_tile(),
                moves_count)

    def fixed_path_game(self):
        """Play a game.

        Moves strategy: Repeatedly move based on a fixed path.
        Returns: (Score, Highest tile, Number of moves)
        """
        path = (self.right, self.up, self.left, self.down)
        moves_count = 0
        while not (self.is_game_over() or self.is_win()):
            for i in range(4):
                current_board = self.get_board_state()
                path[i]()
                if self.did_move(current_board):
                    moves_count += 1
        return (self.get_score(),
                self.get_highest_tile(),
                moves_count)

    def no_left_random_game(self):
        """Play a game.

        Moves strategy: every move is randomly picked from
        {right, up, down}. Move left only if can't move any other way.
        Returns: (Score, Highest tile, Number of moves)
        """
        moves = [self.right, self.up, self.down]
        moves_count = 0
        while not (self.is_game_over() or self.is_win()):
            np.random.shuffle(moves)
            current_board = self.get_board_state()
            for i in range(4):
                try:
                    moves[i]()
                    if self.did_move(current_board):
                        moves_count += 1
                        break
                except IndexError:
                    self.left()
                    if self.did_move(current_board):
                        moves_count += 1
        return (self.get_score(),
                self.get_highest_tile(),
                moves_count)

    def right_trend_no_left_game(self):
        """Play a game.

        Moves strategy: If possible, move right, else, randomly pick
        between up or down.
        Move left only if can't move any other way.
        Returns: (Score, Highest tile, Number of moves)
        """
        moves = [self.up, self.down]
        moves_count = 0
        while not (self.is_game_over() or self.is_win()):
            current_board = self.get_board_state()
            self.right()
            if self.did_move(current_board):
                moves_count += 1
            else:
                np.random.shuffle(moves)
                for i in range(3):
                    try:
                        moves[i]()
                        if self.did_move(current_board):
                            moves_count += 1
                            break
                    except IndexError:
                        self.left()
                        if self.did_move(current_board):
                            moves_count += 1
        return (self.get_score(),
                self.get_highest_tile(),
                moves_count)

    def right_and_down_trend_game(self):
        """Play a game.

                Moves strategy: Try to move based on the following
                priority: right, down, up, left.
                Returns: (Score, Highest tile, Number of moves)
                """
        moves = [self.right, self.down, self.up, self.left]
        moves_count = 0
        while not (self.is_game_over() or self.is_win()):
            current_board = self.get_board_state()
            for i in range(4):
                moves[i]()
                if self.did_move(current_board):
                    moves_count += 1
                    break
        return (self.get_score(),
                self.get_highest_tile(),
                moves_count)


def main():
    ns = Session()
    for _ in range(5):
        print(ns.right_and_down_trend_game())
        ns.restart_game()
    ns.end_session()


if __name__ == '__main__':
    main()

# /html/body/div[3]/div[4]/div[1]  when 'game over'
# /html/body/div[3]/div[4]/div[1]
