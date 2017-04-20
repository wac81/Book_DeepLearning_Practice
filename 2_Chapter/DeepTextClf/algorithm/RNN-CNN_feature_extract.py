# -*- coding:utf-8 -*-
import os
os.environ['KERAS_BACKEND'] = "theano"
# os.environ['THEANO_FLAGS'] = "device=cpu"
from keras.models import Sequential
from keras.layers.core import Dense, Activation
from keras.layers.recurrent import LSTM
from keras.layers.wrappers import TimeDistributed, Bidirectional
from keras.layers import Flatten,Lambda,K
from keras.layers.embeddings import Embedding
from keras.layers.pooling import MaxPooling2D, GlobalMaxPooling2D,MaxPooling1D
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.layers import Merge,Dropout
from keras.datasets import imdb
import numpy as np
# from keras.utils import plot_model
from keras.utils.visualize_util import plot

from keras.preprocessing import sequence

def text_feature_extract_model1(embedding_size=128, hidden_size=256):
    '''
    this is a model use normal Bi-LSTM and maxpooling extract feature

    examples:
这个货很好，很流畅 [  1.62172219e-05]
这个东西真好吃， [  1.65377696e-05]
服务太糟糕,味道差 [ 1.]
你他妈的是个傻逼 [ 1.]
这个贴花的款式好看 [  1.76498161e-05]
看着不错，生产日期也是新的是16年12月份的，就是有点小贵 [  1.59666997e-05]
一股淡淡的腥味。每次喝完都会吃一口白糖 [ 1.]
还没喝，不过，看着应该不错哟 [  1.52662833e-05]
用来看电视还是不错的，就是有些大打字不习惯，要是可以换输入法就好了！ [ 1.]
嗯，中间出了点小问题已经联系苹果客服解决了，打游戏也没有卡顿，总体来讲还不错吧！ [  1.52281245e-05]
下软件下的多的时候死了一回机，强制重启之后就恢复了。 [ 1.]
东西用着还可以很流畅！ [  1.59881820e-05]


    :return:
    '''
    model = Sequential()
    model.add(Embedding(input_dim=max_features,
                        output_dim=embedding_size,
                        input_length=max_seq))
    model.add(Bidirectional(LSTM(hidden_size, return_sequences=True)))
    model.add(TimeDistributed(Dense(embedding_size/2)))
    model.add(Activation('softplus'))
    model.add(MaxPooling1D(5))
    model.add(Flatten())
    # model.add(Dense(2048, activation='softplus'))
    # model.add(Dropout(0.2))
    model.add(Dense(1, activation='sigmoid'))

    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    model.summary()
    plot(model, to_file="text_feature_extract_model1.png", show_shapes=True)
    return model

if __name__ == "__main__":
    #prepare y 1 negtive 0 postive
    y = []

    txt_path = '../data/corpus/reviews/'

    with open(txt_path+'1_point.txt', 'rb') as fp:
        lines = fp.readlines()

    len_temp_lines = len(lines)
    for i in range(len(lines)):
        y.append(1)

    with open(txt_path+'5_point.txt', 'rb') as fp:
        lines += fp.readlines()

    for i in range(len(lines[len_temp_lines:])):
        y.append(0)

    def create_dict():
        dict = open(txt_path+'1_point.txt', 'rb').read()
        # dict += open(txt_path + '2_point.txt', 'rb').read()
        dict += open(txt_path+'5_point.txt', 'rb').read()
        dict_list = set(list(dict.decode('utf8')))
        dicts = {}
        for i, d in enumerate(dict_list):
            dicts[d] = i
        return dicts

    def create_X(lines):
        len_seq = []
        dicts = create_dict()
        sequences = []
        for line in lines:
            if line == '\n':
                continue
            line = line.strip()
            l = list(line.decode('utf8'))
            sequence = [dicts[char] for char in l]
            len_seq.append(len(sequence))
            sequences.append(sequence)
        return sequences, len_seq, dicts


    X_sequences, len_seq, dicts = create_X(lines)

    max_seq = max(len_seq)/2
    print 'max_seq:', max_seq


    max_features = len(dicts) + 1
    print 'max_features:', max_features

    data_X = pad_sequences(X_sequences, maxlen=max_seq)

    label2ind = {'postive':0, 'negitive':1}

    embedding_size = 128
    hidden_size = 256


    model = text_feature_extract_model1(embedding_size = embedding_size, hidden_size=hidden_size)
    # model.fit([data_X,data_X], y, validation_split=0.2, batch_size=128, nb_epoch=2, verbose=1)
    model.fit(data_X, y, validation_split=0.1, batch_size=256, nb_epoch=6, verbose=1)


    '''
    save model
    '''
    model_json = model.to_json()
    with open("rcnn_model_20w_1.json", "w") as json_file:
        json_file.write(model_json)
    # serialize weights to HDF5  checkpoint 已经存储了weight，这里不做操作
    model.save_weights("rcnn_model_20w_1.h5")
    print("Saved model to disk")


    '''
    load model
    '''
    from keras.models import model_from_json

    # model = model_from_json(json_string)
    model = model_from_json(open("rcnn_model_20w_1.json", "rb").read())
    model.load_weights("rcnn_model_20w_1.h5")
    print("Loaded model to disk")


    test = ["这个货很好，很流畅","这个东西真好吃，",
            "服务太糟糕,味道差","你他妈的是个傻逼",
            "这个贴花的款式好看",
            "看着不错，生产日期也是新的是16年12月份的，就是有点小贵",
            "一股淡淡的腥味.每次喝完都会吃一口白糖",
            "还没喝，不过，看着应该不错哟",
            "用来看电视还是不错的，就是有些大打字不习惯，要是可以换输入法就好了！",
            "嗯，中间出了点小问题已经联系苹果客服解决了，打游戏也没有卡顿，总体来讲还不错吧！",
            "下软件下的多的时候死了一回机，强制重启之后就恢复了",
            "东西用着还可以很流畅！"]
    test_sequences = []
    for line in test:
        l = list(line.decode('utf8'))
        sequence = [dicts[char] for char in l]
        test_sequences.append(sequence)

    test_data = pad_sequences(test_sequences, maxlen=max_seq)
    result = model.predict(test_data)
    for i,_ in enumerate(test):
        print _, result[i]
