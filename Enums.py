from enum import Enum


class People(Enum):
    Captain = 0
    Duke = 1
    Assasin = 2
    Contessa = 3
    Ambassador = 4


class StartTurnActions(Enum):
    Asasinate = 0
    Income = 1
    ForeignTrade = 2
    Steal = 3
    Exchange = 4
    DukeRiches = 5
    Coup = 6

    # card/s, coins


StartTurnActions_requirements = {
    StartTurnActions.Income: (None, 0),
    StartTurnActions.ForeignTrade: (None, 0),
    StartTurnActions.Steal: (People.Captain, 0),
    StartTurnActions.Exchange: (People.Ambassador, 0),
    StartTurnActions.DukeRiches: (People.Duke, 0),
    StartTurnActions.Coup: (None, 7),
    StartTurnActions.Asasinate: (People.Assasin, 3)
}


class CounterActions(Enum):
    NoAction = 0
    Challenge = 1
    BlockAssasinate = 2
    BlockForeignTrade = 3
    BlockSteal = 4




CounterActions_requirements = {
    CounterActions.NoAction: [],
    CounterActions.Challenge: [],
    CounterActions.BlockAssasinate: [People.Contessa],
    CounterActions.BlockForeignTrade: [People.Duke],
    CounterActions.BlockSteal: [People.Ambassador, People.Captain]
}

PossibleCounterActions = {
    StartTurnActions.Income: [CounterActions.NoAction],
    StartTurnActions.ForeignTrade: [CounterActions.NoAction, CounterActions.BlockForeignTrade],
    StartTurnActions.Steal: [CounterActions.NoAction, CounterActions.BlockSteal, CounterActions.Challenge],
    StartTurnActions.Exchange: [CounterActions.NoAction, CounterActions.Challenge],
    StartTurnActions.DukeRiches: [CounterActions.NoAction, CounterActions.Challenge],
    StartTurnActions.Coup: [CounterActions.NoAction],
    StartTurnActions.Asasinate: [CounterActions.NoAction, CounterActions.BlockAssasinate, CounterActions.Challenge]
}

ChallengableCounterActions = [
    CounterActions.BlockForeignTrade,
    CounterActions.BlockSteal,
    CounterActions.BlockAssasinate
]

AllPeople = {People.Duke, People.Captain, People.Contessa, People.Ambassador, People.Assasin}
