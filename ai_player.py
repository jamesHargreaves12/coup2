import random

from Enums import StartTurnActions, CounterActions, PossibleCounterActions
from players import GamePlayer, GamePlayerCPU
from keras.layers import Input, Dense
from keras.models import Model


def get_value_model(input_size, out_size):
    inputs = Input(shape=(input_size,), name='inputs')
    hd_1 = Dense(64, activation='relu')(inputs)
    hd_2 = Dense(64, activation='relu')(hd_1)
    outputs = Dense(out_size, activation='linear')(hd_2)
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer='rmsprop',
                  loss='mean_squared_error',
                  metrics=['accuracy'])


class GamePlayerAIPlayer(GamePlayerCPU):
    def __init__(self, player_num, hand, coins):
        super().__init__(player_num, hand, coins)


