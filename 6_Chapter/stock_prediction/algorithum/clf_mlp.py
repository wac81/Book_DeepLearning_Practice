# classification for mlp
from keras.models import Sequential
from keras.layers.core import Dense, Activation, Dropout
import keras

from keras.models import Sequential
from keras.layers.core import Dense, Activation

def clf_model(input_dime):
    out = input_dime * 2 + 1
    model = Sequential()
    model.add(Dense(input_dim=input_dime, output_dim=out))
    model.add(Activation('tanh'))
    model.add(Dense(input_dim=out, output_dim=input_dime))
    model.add(Activation('tanh'))
    model.add(Dense(input_dim=input_dime, output_dim=2))
    model.add(Activation('sigmoid'))
    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])
    return model
