import random

from Enums import StartTurnActions, StartTurnActions_requirements, CounterActions, PossibleCounterActions, People


def get_number_input():
    while True:
        num = input()
        if num.isdigit():
            return int(num)
        print("Illegal number")


def get_option(accepted_list):
    while True:
        option = get_number_input()
        if option in accepted_list:
            return option
        print("Illegal option try again")


class GamePlayer(object):
    def __init__(self, player_num):
        self.player_num = player_num
        self.hand = None
        self.coins = None
        self.dead = None

    def kill(self, person, game):
        game.print("{} Killing {}".format(self.player_num, person.name))
        self.hand.remove(person)
        self.dead.append(person)
        if len(self.hand) == 0:
            game.remove_player(self)

    def reset(self, coins):
        self.coins = coins
        self.hand = []
        self.dead = []

    def get_possible_actions(self):
        return [x.value for x in StartTurnActions if StartTurnActions_requirements[x][1] <= self.coins]

    @staticmethod
    def get_possible_counter_actions(action):
        return [x.value for x in PossibleCounterActions[action]]

    def draw_card(self, game):
        self.hand.append(game.deck.draw())

    def get_action(self, game):
        raise NotImplementedError()

    def get_counter_action(self, game, action):
        raise NotImplementedError()

    def get_counter_challenge(self, game, counter_action):
        raise NotImplementedError()

    def choose_remove_card(self, game, possible, replace=True):
        raise NotImplementedError()

    def choose_and_kill(self, game):
        raise NotImplementedError()

    def pick_victim(self, game):
        raise NotImplementedError()

    def died(self, game):
        raise NotImplementedError()

    def win(self, game):
        raise NotImplementedError()


class GamePlayerHuman(GamePlayer):
    def __str__(self):
        return "HUMAN"

    def get_action(self, game):
        print("Player {} Choose action:".format(self.player_num))
        for x in StartTurnActions.__iter__():
            print(x.value, ": ", x.name)

        acceptable_actions = self.get_possible_actions()
        act = get_option(acceptable_actions)
        return StartTurnActions(act)

    def get_counter_action(self, game, action):
        print("Player {} Choose Counter action".format(self.player_num))
        for x in CounterActions.__iter__():
            print(x.value, ": ", x.name)
        op = get_option([x.value for x in PossibleCounterActions])
        return CounterActions(op)

    def get_counter_challenge(self, game, counter_action):
        print("Player {} do you want to challenge?".format(self.player_num))
        print("0: No")
        print("1: Yes")
        challenge = get_option([0, 1])
        return challenge == 1

    def choose_and_kill(self, game):
        print("Player {} choose person to put back".format(self.player_num))
        op = get_option(self.hand)
        person = People(op)
        self.kill(person, game)
        return person

    def choose_remove_card(self, game, possible, replace=True):
        print("Player {} choose person to put back".format(self.player_num))
        possible_cards = set(self.hand).intersection(possible)
        op = get_option(possible_cards)
        person = People(op)
        self.hand.remove(person)
        game.deck.put_back(person)
        if replace:
            new_person = game.deck.draw()
            self.hand.append(new_person)
            print("Got", new_person)

    def pick_victim(self, game):
        print("Choose Victim")
        return game.players[get_option(list(range(game.num_players)))]

    def died(self, game):
        pass

    def win(self, game):
        pass


class GamePlayerCPU(GamePlayer):
    def __str__(self):
        return "CPU" + str(self.player_num)

    def get_action(self, game):
        if self.coins >= 10:
            return StartTurnActions.Coup
        while True:
            act = random.randint(0, 6)
            if act in self.get_possible_actions():
                return StartTurnActions(act)

    def get_counter_action(self, game, action):
        possible = self.get_possible_counter_actions(action)
        return CounterActions(random.choice(possible))

    def get_counter_challenge(self, game, counter_action):
        return random.random() > 0.5

    def choose_remove_card(self, game, possible, replace=True):
        card = list(set(self.hand).intersection(possible))[0]
        self.hand.remove(card)
        game.deck.put_back(card)
        game.print("Swapped out {}".format(card.name))
        if replace:
            new_card = game.deck.draw()
            self.hand.append(new_card)
            game.print("Swapped in {}".format(new_card.name))

    def choose_and_kill(self, game):
        if self.hand:
            self.kill(self.hand[0], game)

    def pick_victim(self, game):
        while True:
            victim = random.choice(game.players)
            if victim not in game.dead_players and victim != self:
                return victim

    def died(self, game):
        pass

    def win(self, game):
        pass

