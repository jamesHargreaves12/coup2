import random
import sys
from collections import Counter
from enum import Enum

from tqdm import tqdm
import matplotlib.pyplot as plt
from Enums import CounterActions, StartTurnActions_requirements, AllPeople, CounterActions_requirements, People, \
    StartTurnActions, ChallengableCounterActions
from analysis import aggrgate_wins
from dqn_player import GamePlayerDQN
from players import GamePlayerCPU, GamePlayerHuman, GamePlayer


class Deck(object):
    def __init__(self):
        self.deck = []
        for p in People:
            self.deck.append(p)
            self.deck.append(p)
            self.deck.append(p)
        random.shuffle(self.deck)

    def draw(self):
        return self.deck.pop(0)

    def put_back(self, person):
        self.deck.append(person)


class Game(object):
    def __init__(self, num_players, players=None, print_debug=True):
        self.num_players = num_players
        if players:
            self.players = players
        else:
            self.players = [GamePlayerCPU(i) for i in range(num_players)]
            self.players[0] = GamePlayerDQN(0, self.num_players)

        self.print_debug = print_debug
        self.deck = None
        self.dead_players = None
        self.game_end = False
        self.turn_index = None
        self.winner = None

    def reset(self):
        self.winner = None
        self.deck = Deck()
        self.dead_players = []
        self.game_end = False
        self.turn_index = random.randint(0, self.num_players-1)
        for pl in self.players:
            pl.reset(coins=2)
            pl.draw_card(self)
            pl.draw_card(self)
        for pl in self.players:
            self.print("{} has {} and {}".format(pl, pl.hand[0].name, pl.hand[1].name))
        self.print("*" * 20)

    def print(self, txt):
        if self.print_debug:
            print(txt)

    def get_game_state(self, cur_player: GamePlayer):
        cards = []
        coins = []
        for offset in range(1, len(self.players)):
            player = self.players[(cur_player.player_num + offset) % len(self.players)]
            player_state = [-1] * (2 - len(player.dead)) + [x.value for x in player.dead]
            cards.extend(player_state)
            coins.append(player.coins)
        coins.append(cur_player.coins)
        cards.extend([x.value for x in cur_player.dead] + [-1] * (2 - len(cur_player.dead)))
        cards.extend([x.value for x in cur_player.hand] + [-1] * (2 - len(cur_player.hand)))
        return coins, cards

    def print_game_state(self):
        output = "***** "
        for player in self.players:
            output += "({},{})".format(player.coins, [x.name for x in player.hand])
        self.print(output)

    def remove_player(self, player: GamePlayer):
        player.died(self)
        self.dead_players.append(player)
        if len(self.dead_players) == self.num_players - 1:
            self.winner = set(self.players).difference(self.dead_players).pop()
            self.winner.win(self)
            self.print("Winner {}".format(player))
            self.game_end = True

    def get_counter_action(self, action):
        for offset in range(1, len(self.players)):
            player = self.players[(self.turn_index + offset) % len(self.players)]
            if player in self.dead_players:
                continue
            ca = player.get_counter_action(self, action)
            if ca != CounterActions.NoAction:
                return ca, player
        return CounterActions.NoAction, None

    def get_challenge_count_action(self, counter_action, ca_player: GamePlayer):
        for offset in range(1, len(self.players)):
            player = self.players[(ca_player.player_num + offset) % len(self.players)]
            if player in self.dead_players:
                continue
            challenge = player.get_counter_challenge(game, counter_action)
            if challenge:
                return player
        return None

    def resolve_challenge(self, required_people, player: GamePlayer, challenger: GamePlayer):
        if any(x in player.hand for x in required_people):
            self.print("Challenge unsuccessful")
            challenger.choose_and_kill(self)
            player.choose_remove_card(self, required_people, replace=True)
            return False
        else:
            self.print("Challenge Successful")
            player.choose_and_kill(self)
            return True

    def play_turn(self):
        current_player = self.players[self.turn_index]
        action = current_player.get_action(self)
        self.print("Player {} selects {}".format(current_player, action.name))
        who = -1
        if action in [StartTurnActions.Steal, StartTurnActions.Asasinate, StartTurnActions.Coup]:
            who = current_player.pick_victim(self)
            self.print("@ {}".format(who))

        ca, ca_player = self.get_counter_action(action)
        if ca != CounterActions.NoAction:
            self.print("Counter Actions {} by {}".format(ca.name, ca_player))
        action_continues = True
        if ca in ChallengableCounterActions:
            challenger = self.get_challenge_count_action(ca, ca_player)
            if challenger:
                self.print("Challenge by {}".format(challenger))
                required_people = CounterActions_requirements[ca]
                required_people = required_people if required_people else AllPeople
                success = self.resolve_challenge(required_people, ca_player, challenger)
                action_continues = success
            else:
                # These are all block events so action doesn't continue 
                action_continues = False
        elif ca == CounterActions.Challenge:
            requirements = StartTurnActions_requirements[action][0]
            required_people = [requirements] if requirements is not None else AllPeople
            success = self.resolve_challenge(required_people, current_player, ca_player)
            action_continues = not success
        else:
            # NoAction selected by all players
            pass

        if action_continues:
            if action == StartTurnActions.Income:
                current_player.coins += 1
            elif action == StartTurnActions.ForeignTrade:
                current_player.coins += 2
            elif action == StartTurnActions.DukeRiches:
                current_player.coins += 3
            elif action == StartTurnActions.Asasinate:
                who.choose_and_kill(self)
            elif action == StartTurnActions.Steal:
                steal_amt = min(2, who.coins)
                current_player.coins += steal_amt
                who.coins -= steal_amt
            elif action == StartTurnActions.Coup:
                who.choose_and_kill(self)
            else:
                current_player.draw_card(self)
                current_player.draw_card(self)
                self.print("New Hand {}".format(" ".join([x.name for x in current_player.hand])))
                current_player.choose_remove_card(self, possible=AllPeople, replace=False)
                current_player.choose_remove_card(self, possible=AllPeople, replace=False)
        self.turn_index = (self.turn_index + 1) % len(self.players)
        while self.players[self.turn_index] in self.dead_players:
            self.turn_index = (self.turn_index + 1) % len(self.players)
        self.print_game_state()


if __name__ == "__main__":
    num_players = 2
    average_size = 30
    episodes = 1000
    for _ in range(1):
        for num_ai in range(0, num_players):
            print("Playing with {} AIs".format(num_ai))
            players = [GamePlayerCPU(i) for i in range(num_players)]
            for i in range(num_ai):
                players[i] = GamePlayerDQN(i, num_players)

            winners = []
            game = Game(num_players, players=players, print_debug=True)
            for i in tqdm(range(episodes)):
                game.reset()
                while not game.game_end:
                    game.play_turn()
                winners.append(game.winner.player_num)
            agg_res = aggrgate_wins(winners, average_size=average_size)
            print(sum(agg_res))
            plt.plot(agg_res, label=num_ai)

        plt.legend(loc='best')
        plt.ylim((0, average_size))
        plt.show()
