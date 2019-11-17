#! python 3
# simulateGame.py - simulate online games of 2048.
# Verify that browser's driver is located in the same directory.
# driver can be downloaded from
# https://sites.google.com/a/chromium.org/chromedriver/downloads

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
import numpy as np
import itertools

import time

url2048 = 'https://play2048.co/'


class Session:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.get(url2048)
        self.current_grid = self.get_tiles_grid()

    def end_session(self):
        """closes browser."""
        self.driver.close()

    def restart_game(self):
        restart_btn = self.driver.find_element('class name', 'restart-button')
        restart_btn.click()
        self.update_grid()

    def right(self):
        """Move right."""
        action = ActionChains(self.driver)
        action.key_down(Keys.ARROW_RIGHT)
        action.perform()
        self.update_grid()

    def left(self):
        """Move left."""
        action = ActionChains(self.driver)
        action.key_down(Keys.ARROW_LEFT)
        action.perform()
        self.update_grid()

    def up(self):
        """Move up."""
        action = ActionChains(self.driver)
        action.key_down(Keys.ARROW_UP)
        action.perform()
        self.update_grid()

    def down(self):
        """Move down."""
        action = ActionChains(self.driver)
        action.key_down(Keys.ARROW_DOWN)
        action.perform()
        self.update_grid()

    def get_board(self):
        """Returns a list of web elements of 'tiles-state' on board"""
        container = self.driver.find_element('class name', 'tile-container')
        return container.find_elements('xpath', '*')

    def get_tiles_grid(self):
        """Returns np.array with values of tiles."""
        tiles_grid = np.array([[0 for _ in range(4)] for _ in range(4)])
        board = self.get_board()
        for tile in board:
            tile_desc = tile.get_attribute('class').split(' tile-')
            position = (int(tile_desc[2].split('-')[1]) - 1,
                        int(tile_desc[2].split('-')[2]) - 1)
            tile_value = int(tile_desc[1])
            tiles_grid[position] = tile_value
        return np.transpose(tiles_grid)

    def update_grid(self):
        self.current_grid = self.get_tiles_grid()

    def did_move(self, previous_board_state):
        """Returns bool if a move had been done.

        previous_board_state: list of web elements.
        """
        return previous_board_state != self.get_board()

    def get_score(self):
        """Returns the score of the current game."""
        score = self.driver.find_element('class name', 'score-container')
        return int(score.text.split()[0])
        pass

    def get_highest_tile(self):
        """Returns value of highest tile on board."""
        board = self.get_board()
        tiles = [int(tile.text) for tile in board if tile]
        return max(tiles)

    def get_highest_tile_position(self, tile_value):  # TODO: this
        """Returns position of first tile that has value of tile_value.

        tile_value: int.
        returns: tuple.
        """
        tiles_grid = self.get_tiles_grid()
        indices = np.where(tiles_grid == tile_value)
        return list(zip(indices[0], indices[1]))[0]

    def is_low_tile_blocked(self):  # TODO: this
        """Is there a tile to the right of/below a higher value tile.

        Given a strategy of moving tiles rightward and downward.
        Returns: bool.
        """
        flag = False
        tiles_grid = self.get_tiles_grid()
        for i, j in itertools.product(range(1, 4), range(1, 4)):
            tile = tiles_grid[i, j]
            if tile == 0:
                continue
            if tile < tiles_grid[i-1, j] or tile < tiles_grid[i, j-1]:
                flag = True
                break
        return flag

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
            current_board = self.get_board()
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
                current_board = self.get_board()
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
            current_board = self.get_board()
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
            current_board = self.get_board()
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
            current_board = self.get_board()
            for i in range(4):
                moves[i]()
                if self.did_move(current_board):
                    moves_count += 1
                    break
        return (self.get_score(),
                self.get_highest_tile(),
                moves_count)

    def r_a_d_t_with_block_flag_game(self):
        """Play a game.

        Moves strategy: Try to move based on the following
        priority: right, down, up, left, but if 'block' flag
        is on, switch between down and up.
        Returns: (Score, Highest tile, Number of moves)
        """
        moves_flag_off = [self.right, self.down, self.up, self.left]
        moves_flag_on = [self.right, self.up, self.down, self.left]
        flag = False
        moves_count = 0
        while not (self.is_game_over() or self.is_win()):
            current_board = self.get_board()
            moves = moves_flag_on if flag else moves_flag_off
            for i in range(4):
                moves[i]()
                if self.did_move(current_board):
                    moves_count += 1
                    flag = self.is_low_tile_blocked()
                    break
        return (self.get_score(),
                self.get_highest_tile(),
                moves_count)
        pass


def move_row(row):
    """rearrange row, based on game rules."""
    temp = [x for x in row if x != 0]
    zeros = len(row) - len(temp)
    i = 1
    while i < len(temp):
        if temp[-i] == temp[-i - 1]:
            temp[-i] = temp[-i] * 2
            del temp[-i - 1]
            zeros += 1
        i += 1
    return [0] * zeros + temp


def get_board_if_move(cur_grid, direction):
    'Return board grid if moved in direction (without added tile).'
    grid = np.copy(cur_grid)

    if direction == 'down':
        for i in range(4):
            rearranged_col = move_row(grid[:, i])
            grid[:, i] = rearranged_col

    elif direction == 'up':
        for i in range(4):
            rearranged_col = move_row(np.flip(grid[:, i]))
            rearranged_col.reverse()
            grid[:, i] = rearranged_col

    elif direction == 'left':
        for i in range(4):
            rearranged_row = move_row(np.flip(grid[i, :]))
            rearranged_row.reverse()
            grid[i, :] = rearranged_row

    elif direction == 'right':
        for i in range(4):
            rearranged_row = move_row(grid[i, :])
            grid[i, :] = rearranged_row

    return grid


def get_max_tile(grid):
    """Returns max tile value and a list of positions."""
    value = np.amax(grid)
    row, col = np.where(grid == value)
    max_coor = list(zip(row, col))
    return value, max_coor


def are_neighbors(tiles_pos):
    """Gets a list of positions, returns True if a couple are neighbors."""
    for i, pos in enumerate(tiles_pos):
        for j in range(i + 1, len(tiles_pos)):
            if ((pos[0] == tiles_pos[j][0] and
                 abs(pos[1] - tiles_pos[j][1]) == 1) or
                    (pos[1] == tiles_pos[j][1] and
                     abs(pos[0] - tiles_pos[j][0]) == 1)):
                return True
    return False


def is_higher_or_equal_max_value(grid1, grid2):
    """Compares max value of 2 grids.

    Returns 1 if grid2 is bigger, else 0.
    """
    max_value_1 = get_max_tile(grid1)[0]
    max_value_2 = get_max_tile(grid2)[0]
    if max_value_2 > max_value_1:
        return True
    return False


def get_if_moved_grids(curr_grid):
    """Returns possible next step grids in a dict."""
    directions = ['right', 'left', 'up', 'down']
    if_moved = dict()
    for direction in directions:
        if_moved[direction] = get_board_if_move(curr_grid, direction)
    return if_moved


def greedy_random_game(session):
    """Play a game.

    Strategy: First check if can increase highest tile.
    Else, choose a random move.

    :param session: Session object.
    :return: (Score, Highest tile, Number of moves)
    """
    moves = {'right': session.right, 'left': session.left,
             'up': session.up, 'down': session.down}

    moves_count = 0
    attempts = 7
    while not (session.is_game_over() or session.is_win()) and attempts > 0:
        try:
            # check if exists a move to increase highest tile.
            possible_grids = get_if_moved_grids(session.current_grid)
            higher_tile_possible = []
            if is_higher_or_equal_max_value(session.current_grid,
                                            possible_grids['right']):
                higher_tile_possible += ['right', 'left']
            if is_higher_or_equal_max_value(session.current_grid,
                                            possible_grids['up']):
                higher_tile_possible += ['up', 'down']
            # if can get higher tile, randomly choose direction which
            # increases tile
            if higher_tile_possible:
                move = np.random.choice(higher_tile_possible)
                moves[move]()
                moves_count += 1

            else:
                directions = list(moves.keys())
                np.random.shuffle(directions)
                current_board = session.get_board()
                for i in range(4):
                    moves[directions[i]]()
                    if session.did_move(current_board):
                        moves_count += 1
                        break
            # time.sleep(0.05)
            attempts = 7
        except StaleElementReferenceException:
            attempts -= 1
    max_tile, _ = get_max_tile(session.current_grid)
    return (session.get_score(),
            max_tile,
            moves_count)


def greedy_rtnl_game(session):
    """Play a game.

    Moves strategy: If possible get higher top tile
    (right before up or down), else move right, else,
    randomly pick between up or down.
    Move left only if can't move any other way.
    Returns: (Score, Highest tile, Number of moves)
    """
    moves = {'up': session.up, 'down': session.down}
    moves_count = 0
    attempts = 8
    while not (session.is_game_over() or session.is_win()) and attempts > 0:
        try:
            # check if exists a move to increase highest tile.
            possible_grids = get_if_moved_grids(session.current_grid)
            higher_tile_possible = []
            if is_higher_or_equal_max_value(session.current_grid,
                                            possible_grids['right']):
                higher_tile_possible += ['right']
            if is_higher_or_equal_max_value(session.current_grid,
                                            possible_grids['up']):
                higher_tile_possible += ['up', 'down']
            if higher_tile_possible:
                if 'right' in higher_tile_possible:
                    session.right()
                else:
                    move = np.random.choice(higher_tile_possible)
                    moves[move]()
                moves_count += 1
            else:
                current_board = session.get_board()
                session.right()
                if session.did_move(current_board):
                    moves_count += 1
                else:
                    directions = list(moves.keys())
                    np.random.shuffle(directions)
                    for i in range(3):
                        try:
                            moves[directions[i]]()
                            if session.did_move(current_board):
                                moves_count += 1
                                break
                        except IndexError:
                            session.left()
                            if session.did_move(current_board):
                                moves_count += 1
            # time.sleep(0.05)
            attempts = 8
        except StaleElementReferenceException:
            attempts -= 1
    max_tile, _ = get_max_tile(session.current_grid)
    return (session.get_score(),
            max_tile,
            moves_count)

# class Board(Session):
#     def __init__(self):
#         self.board = super().get_board()
#
#     def get_tiles_grid(self):
#         pass
#
#     def get_highest_tile(self):
#         pass
#
#     def get_highest_tile_position(self, tile_value):
#         pass

    # def ge


def main():
    ns = Session()

    print(greedy_rtnl_game(ns))
    # for _ in range(3):
    #     ns.left()
    #     ns.right()
    #     ns.up()
    #     print(ns.get_tiles_grid())
    #     print('-------------------')
        # print(ns.r_a_d_t_with_block_flag_game())
        # ns.restart_game()
        # print(ns.get_highest_tile_position(tile_value=ns.get_highest_tile()))
    # ns.end_session()
    # for _ in range(5): # ns.end_session()


if __name__ == '__main__':
    main()

