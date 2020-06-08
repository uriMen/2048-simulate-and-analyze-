#! python 3
# evolving_algorithm.py - using evolving algorithm to solve
# the game 2048.
# Verify that browser's driver is located in the same directory.
# driver can be downloaded from
# https://sites.google.com/a/chromium.org/chromedriver/downloads

import time
import math

import numpy as np
import pandas as pd
from selenium.common.exceptions import StaleElementReferenceException

from simulateGame import (Session, Board, get_potential_moves_score,
                          get_number_of_zeros, get_max_tile,
                          get_distance_from_lower_right_corner,
                          get_distance_from_right_wall)

# to show all columns of DataFrame
# when printing in pycharm console
desired_width = 320
max_cols = 10
pd.set_option("display.max_columns", max_cols)
pd.set_option('display.width', desired_width)

# Constant variables
POPULATION_SIZE = 5
WEIGHT_CONST = 0.5
MUTATION_RATE = 0.05
MUTATION_CHANGE = 0.2
EDGES_SIZE = 1
MAX_GENERATION = 1

# # Genomes attribution:
# # Weights for use of Evolving Algorithms to evaluate moves.
# weights = ['w_highest tile',
#            'w_score',
#            'w_number of zeros',
#            'w_potential two step score',
#            'w_distance from right',
#            'w_distance from corner']
# # additional attribute for easier management.
# cols = weights + ['generation', 'max tile', 'final score']


def initialize_genomes_df():
    """Returns a DataFrame with first generation genomes"""
    # Genomes attribution:
    # Weights for use of Evolving Algorithms to evaluate moves.
    weights = ['w_highest tile',
               'w_score',
               'w_number of zeros',
               'w_potential two step score',
               'w_distance from right',
               'w_distance from corner']
    # additional attribute for easier management.
    cols = weights + ['generation', 'max tile', 'final score']
    # Store genomes in a pd.DataFrame
    genomes = pd.DataFrame(columns=cols)
    # Initialize genome population with random weights
    generation = 1
    for _ in range(POPULATION_SIZE):
        rand_weights = list(np.random.rand(len(weights)) - WEIGHT_CONST)
        genomes.loc[len(genomes)] = rand_weights + [generation, None, None]
    return genomes


def evaluate_move(poss_move):
    """Gets a Board obj and evaluate params.

    returns: dict.
    """
    # ******Now only with log2() on some features*******
    evaluated_params = dict()
    poss_move.add_children()
    next_step_score = sorted(get_potential_moves_score(poss_move),
                             key=lambda x: x[1], reverse=True)
    max_tile, max_coor = get_max_tile(poss_move.grid)

    w_score = poss_move.score
    evaluated_params['w_score'] = math.log2(w_score) if w_score != 0 else 0
    w_potential_score = poss_move.score + next_step_score[0][1]
    evaluated_params['w_potential two step score'] = math.log2(
        w_potential_score) if w_potential_score != 0 else 0
    evaluated_params['w_number of zeros'] = get_number_of_zeros(poss_move.grid)
    evaluated_params['w_highest tile'] = math.log2(max_tile)
    evaluated_params['w_distance from right'] = get_distance_from_right_wall(
        max_coor)
    evaluated_params[
        'w_distance from corner'] = get_distance_from_lower_right_corner(
        max_coor)

    return evaluated_params


def breed(genome_a, genome_b):
    """Return a third genome created out of 2 given genomes.

    :param genome_a: pd.Series.
    :param genome_b: pd.Series.
    :return pd.Series.
    """
    # Method: for each 'weight' field (w_) randomly choose that field
    # between the 2 given genomes.
    # Randomly mutate.
    child_genome = pd.Series()
    for i in genome_a.columns:
        if 'w_' in i:
            options = [genome_a.iloc[0][i], genome_b.iloc[0][i]]
            child_genome[i] = options[np.random.randint(2)]
            # Mutation step
            if np.random.random() < MUTATION_RATE:
                child_genome[i] += MUTATION_CHANGE * (
                        2 * np.random.random() - 1)
        else:
            child_genome[i] = None
    return child_genome


def evolve(generation, genomes_df):
    """Create next generation of genomes.

    :param generation: int. current generation.
    :param genomes_df: DataFrame of genomes.
    :return DataFrame.
    """
    next_gen = pd.DataFrame(columns=genomes_df.columns)
    # filter genomes of generation
    curr_gen = genomes_df.loc[genomes_df['generation'] == generation].copy()
    # sort by highest tile and final score
    curr_gen.sort_values(['max tile', 'final score'],
                         ascending=[False, False], inplace=True)
    # top (EDGES_SIZE) automatically advanced to next generation
    next_gen = next_gen.append(curr_gen.iloc[:EDGES_SIZE, :7],
                               ignore_index=True, sort=False)
    # last (EDGES_SIZE) are dropped
    curr_gen.drop(index=curr_gen.iloc[-EDGES_SIZE:].index, inplace=True)
    # Randomly choose 2 different parent genomes to breed
    # to populate rest of generation
    for _ in range(POPULATION_SIZE - EDGES_SIZE):
        parent_1, parent_2 = select_parents(curr_gen)
        child = breed(parent_1, parent_2)
        next_gen.loc[len(next_gen)] = child
    next_gen['generation'] = generation + 1
    return next_gen


def select_parents(genomes_df):
    """Select 2 genomes to breed using Accept & Reject"""
    max_score = genomes_df['final score'].max()
    while True:
        parent_1 = genomes_df.sample(1)
        if np.random.randint(max_score) < parent_1.iloc[0]['final score']:
            break
    while True:
        parent_2 = genomes_df.sample(1)
        if np.random.randint(max_score) < parent_2.iloc[0]['final score']:
            break

    return parent_1, parent_2


def play_game(session, genome):
    """Simulate a game based on given genome.

    Returns max_tile and final_score in a tuple.
    """

    moves = {'up': session.up, 'down': session.down,
             'left': session.left, 'right': session.right}
    attempts = 9
    while not (session.is_game_over() or session.is_win()) and attempts > 0:
        try:
            moves_params = {'right': dict(), 'left': dict(),
                            'up': dict(), 'down': dict()}
            curr_board = Board(session.current_grid)
            curr_board.add_children()
            # get parameters for each possible move
            for child in curr_board.children:
                moves_params[child.direction] = evaluate_move(child)
            # evaluate moves score based on genome
            move_score = dict()
            for direction, params in moves_params.items():
                score = 0
                for param, value in params.items():
                    score += value * genome[param]
                move_score[direction] = score

            # make a move based on calculated score
            sorted_moves = sorted(move_score, key=move_score.get, reverse=True)
            for move in sorted_moves:
                moves[move]()
                if session.did_move_2(curr_board.grid):
                    break

            attempts = 9
        except StaleElementReferenceException:
            attempts -= 1

    max_tile, _ = get_max_tile(session.current_grid)
    final_score = session.get_score()

    return max_tile, final_score


def main_process(generation, genomes_df):
    """Play games and add new generations of genomes.

    :param generation: int. Which generation to start from.
    :param genomes_df: pd.DataFrame. A table of genomes to play by.
    :return: pd.DataFrame. A table with additional genomes
    generations.
    """
    ns = Session()
    # genomes_df = initialize_genomes_df()
    # generation = 1
    while generation <= MAX_GENERATION:
        attempts = 7
        for i in genomes_df.index:
            while attempts > 0:
                try:
                    if genomes_df.at[i, 'generation'] == generation:
                        max_tile, final_score = play_game(ns,
                                                          genomes_df.iloc[i])
                        genomes_df.at[i, 'max tile'] = max_tile
                        genomes_df.at[i, 'final score'] = final_score
                        ns.restart_game()
                        attempts = 7
                        print(f'generation: {generation}, game: {i+1}')
                        break
                    else:
                        break
                except StaleElementReferenceException:
                    attempts -= 1

        next_generation = evolve(generation, genomes_df)
        genomes_df = genomes_df.append(next_generation, ignore_index=True)
        generation += 1

    ns.end_session()
    return genomes_df


if __name__ == '__main__':

    genomes = initialize_genomes_df()
    print(main_process(1, genomes))
    # gene_df = pd.read_csv('genomes_20_in_gen_with_log2_only - Copy.csv')
    # gen = evolve(141, gene_df)
