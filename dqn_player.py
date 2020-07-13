from Enums import StartTurnActions, People, CounterActions
from players import GamePlayer, GamePlayerCPU
import random
from collections import deque
from enum import Enum
from functools import reduce

import matplotlib.pyplot as plt

import numpy as np
from keras import Sequential
from keras.optimizers import Adam
from keras.utils import to_categorical
from tqdm import tqdm

from keras.layers import Input, Dense
from keras.models import Model


class DQN(object):
    def __init__(self, num_actions, num_states):
        self.num_actions = num_actions
        self.num_states = num_states
        self.replay_memory = deque(maxlen=200)

        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learn_rate = 0.01
        self.tau = 1
        self.batch_size = 32

        self.model = self.set_up_models()
        self.target_model = self.set_up_models()

    def set_up_models(self):
        model = Sequential()
        model.add(Dense(16, input_dim=self.num_states, activation='relu'))
        model.add(Dense(32, activation='relu'))
        model.add(Dense(self.num_actions))
        model.compile(loss="mean_squared_error", optimizer=Adam(lr=self.learn_rate))
        return model

    def remember(self, state, action, reward, new_state, done):
        self.replay_memory.append((state, action, reward, new_state, done))

    def replay(self):
        if len(self.replay_memory) < self.batch_size:
            return
        samples = random.sample(self.replay_memory, self.batch_size)
        for s, a, r, ns, done in samples:
            target = self.target_model.predict(s)
            if done:
                target[0][a] = r
            else:
                Q_future = max(self.target_model.predict(ns)[0])
                target[0][a] = r + Q_future * self.gamma
            self.model.fit(s, target, epochs=1, verbose=0)

    def target_train(self):
        weights = self.model.get_weights()
        target_weigts = self.target_model.get_weights()
        for i in range(len(target_weigts)):
            target_weigts[i] = weights[i] * self.tau + target_weigts[i] * (1 - self.tau)
        self.target_model.set_weights(target_weigts)

    def act(self, state):
        self.epsilon *= self.epsilon_decay
        self.epsilon = max(self.epsilon_min, self.epsilon)
        if np.random.random() < self.epsilon:
            return np.random.randint(0, self.num_actions)
        return np.argmax(self.model.predict(state)[0])


class ActionDQNWrapper(object):
    def __init__(self, num_actions, size_states, debug_file_name=None):
        self.last_action = None
        self.last_action_legal = None
        self.last_state = None
        self.dqn_agent = DQN(num_actions, size_states)

        self.debug_action_legal_file = None
        if debug_file_name:
            self.debug_action_legal_file = open(debug_file_name,'w+')

    def reset(self):
        self.last_action = None
        self.last_action_legal = None
        self.last_state = None

    def get_action(self, state_emb, possible_actions):
        if self.last_state is not None:
            reward = 0 if self.last_action_legal else -1
            self.dqn_agent.remember(self.last_state, self.last_action, reward, state_emb, False)
        self.last_action = self.dqn_agent.act(state_emb)
        self.last_state = state_emb
        self.last_action_legal = self.last_action in possible_actions
        if self.debug_action_legal_file:
            self.debug_action_legal_file.write(str(self.last_action_legal) + '\n')
        return self.last_action

    def end_game(self, state_emb, reward):
        if self.last_state is not None:
            self.dqn_agent.remember(self.last_state, self.last_action, reward, state_emb, True)
        self.dqn_agent.replay()
        self.dqn_agent.target_train()


class GamePlayerDQN(GamePlayerCPU):
    def __str__(self):
        return "DQN" + str(self.player_num)

    def __init__(self, player_num, num_players=3):
        super().__init__(player_num)
        self.num_actions = len(list(StartTurnActions))
        self.num_counter_actions = len(list(CounterActions))
        self.num_coin_states = 13
        self.card_states = (1 + len(list(People)))
        self.tot_coins_states = num_players * self.num_coin_states
        self.tot_card_states = self.card_states * (num_players + 1) * 2
        self.dqn_agent_start = ActionDQNWrapper(self.num_actions, self.tot_coins_states + self.tot_card_states,
                                                debug_file_name='debug/start.txt')
        self.dqn_agent_counter = ActionDQNWrapper(self.num_counter_actions, self.num_actions + self.tot_card_states +
                                                  self.tot_coins_states, debug_file_name='debug/counter.txt')

    def reset(self, coins):
        super().reset(coins)
        self.dqn_agent_start.reset()
        self.dqn_agent_counter.reset()

    def get_state_embedding(self, state):
        coins, cards = state
        state_coins = to_categorical(coins, num_classes=self.num_coin_states).reshape(-1)
        state_cards = to_categorical(cards, num_classes=self.card_states).reshape(-1)
        return np.concatenate((state_coins, state_cards)).reshape(1, -1)

    def get_action(self, game):
        if self.coins >= 10:
            return StartTurnActions.Coup
        state = self.get_state_embedding(game.get_game_state(self))
        possible_actions = self.get_possible_actions()
        action = self.dqn_agent_start.get_action(state, possible_actions)
        if action in possible_actions:
            return StartTurnActions(action)
        else:
            possible = self.get_possible_actions()
            return StartTurnActions(random.choice(possible))

    def end_game(self, game, reward):
        state = self.get_state_embedding(game.get_game_state(self))
        def_action_emb = to_categorical([CounterActions.NoAction.value], num_classes=self.num_actions).reshape(-1)
        self.dqn_agent_start.end_game(state, reward)
        self.dqn_agent_counter.end_game(def_action_emb, reward)

    def died(self, game):
        self.end_game(game, -1)

    def win(self, game):
        self.end_game(game, 1)

    def get_counter_action(self, game, action):
        state = self.get_state_embedding(game.get_game_state(self)).reshape(-1)
        action_emb = to_categorical([action.value], num_classes=self.num_actions).reshape(-1)
        counter_action_state = np.concatenate((state, action_emb)).reshape(1, -1)
        possible = self.get_possible_counter_actions(action)
        counter_act = self.dqn_agent_counter.get_action(counter_action_state, possible)
        if counter_act in possible:
            return CounterActions(counter_act)
        else:
            possible = self.get_possible_counter_actions(action)
            return CounterActions(random.choice(possible))

    #
    # def get_counter_challenge(self, game, counter_action):
    #     pass
    #
    # def choose_remove_card(self, game, possible, replace=True):
    #     pass
    #
    # def choose_and_kill(self, game):
    #     pass
    #
    # def pick_victim(self, game):
    #     pass
