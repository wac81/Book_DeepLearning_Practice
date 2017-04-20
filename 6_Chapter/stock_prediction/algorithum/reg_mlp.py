from keras.models import Sequential
from keras.layers.core import Dense, Activation
from keras.layers.recurrent import LSTM

def reg_mlp(input_dimension):
    out = input_dimension * 2 + 1
    model = Sequential()
    model.add(Dense(input_dim=input_dimension, output_dim=out))
    model.add(Activation('softplus'))
    model.add(Dense(input_dim=out, output_dim=out))
    model.add(Activation('softplus'))
    model.add(Dense(input_dim=out, output_dim=input_dimension))
    model.add(Activation('softplus'))
    model.add(Dense(input_dim=input_dimension, output_dim=1))
    model.add(Activation('linear'))
    model.compile(optimizer='adam',
                  loss='mse',
                  metrics=['accuracy'])
    return model