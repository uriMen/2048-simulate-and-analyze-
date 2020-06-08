#! python 3
# collectData.py - Get data of 2048 game using simulations
# from simulateGame.

import os

import pandas as pd
import numpy as np
import datetime

import simulateGame

start_time = datetime.datetime.now()
ns = simulateGame.Session()
strategies = [('tr', ns.total_random_game),
              ('fp', ns.fixed_path_game),
              ('nlr', ns.no_left_random_game),
              ('rtnl', ns.right_trend_no_left_game),
              ('radt', ns.right_and_down_trend_game)]
              # ('greedy_random', simulateGame.greedy_random_game)]
with open('2_step_score_greedy_no_left.txt', 'w') as file:
    for i in range(30):
        # strategy_type, strategy = strategies[np.random.randint(5)]
        # score, highest_tile, moves_count = strategy()
        score, highest_tile, moves_count = simulateGame.two_step_score_greedy_no_left_game(ns)
        # file.write(f'{strategy_type},{score},{highest_tile},{moves_count}\n')
        file.write(f'2ssgnl,{score},{highest_tile},{moves_count}\n')
        ns.restart_game()
        print(f'game {i+1}')
end_time = datetime.datetime.now()
print(f'Time duration {end_time - start_time}')
ns.end_session()
