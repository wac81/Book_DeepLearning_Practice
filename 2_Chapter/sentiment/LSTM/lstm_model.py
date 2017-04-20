# -*- coding: utf-8 -*-
"""
lstm模型
"""
from keras.utils import np_utils
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM


def lstm_train(dic, x, y, maxlen):
    print('Build model...')
    model = Sequential()
    model.add(Embedding(input_dim=len(dic) + 1, output_dim=256, input_length=maxlen))
    model.add(LSTM(128))  # try using a GRU instead, for fun
    model.add(Dropout(0.5))
    model.add(Dense(3))
    model.add(Activation('sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='adam', class_mode="binary")
    model.fit(x, y, batch_size=32, nb_epoch=10, show_accuracy=True)  # 训练时间为若干个小时
    return model


def lstm_test(model, xt, yt):
    classes = model.predict_classes(xt)
    acc = np_utils.accuracy(classes, yt)
    print('Test accuracy:', acc)
