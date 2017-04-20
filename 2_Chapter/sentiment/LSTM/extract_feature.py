# coding: utf-8
"""
数据进行特征提取
"""
import jieba.posseg as psg
import codecs
import numpy as np
import pandas as pd
import jieba
from keras.preprocessing import sequence

# 载入停用此表
stopwords = codecs.open('./data/chinese_stopword.txt', encoding='UTF-8').read().split('\n')

MAX_LENGTH = 150
CLASS_NUM = 3  # 默认分类数


def extract_lstm_train(file_name, tag_num=CLASS_NUM, col_tag=0, col_content=1, length=MAX_LENGTH):
    """
    抽取lstm的特征
    :param file_name: 文件
    :param tag_num: 分类数目
    :param col_tag: 标签在xlsx中的位置
    :param col_content: 内容在xlsx中的位置
    :param length: 每段话表示的最大长度,超过会截取,不够长会用0补齐
    :return:
    """
    contents = pd.read_excel(file_name, header=None)
    cw = lambda x: [word.encode('utf-8') for word in jieba.cut(x) if word not in stopwords and word.strip() != '']
    contents['words'] = contents[col_content].apply(cw)

    d2v_train = contents['words']
    w = []  # 将所有词语整合在一起
    for i in d2v_train:
        w.extend(i)
    dictionary = pd.DataFrame(pd.Series(w).value_counts())
    dictionary['id'] = list(range(1, len(dictionary) + 1))
    # 将词与id对应
    get_sent = lambda x: list(dictionary['id'][x])
    contents['sent'] = contents['words'].apply(get_sent)  # 速度太慢,统计每个词出现的次数
    print("Pad sequences (samples x time)")
    contents['sent'] = list(sequence.pad_sequences(contents['sent'], maxlen=length))
    x = np.array(list(contents['sent']))  # 训练集
    y = np.zeros((len(list(contents[col_tag])), tag_num))
    for i in range(len(list(contents[col_tag]))):
        for j in range(tag_num):
            if contents[col_tag][i] == j:
                y[i][j] = 1
    return dictionary, x, y, length


def extract_lstm_test(dictionary, file_name, tag_num=CLASS_NUM, col_tag=0, col_content=1, length=MAX_LENGTH):
    contents = pd.read_excel(file_name, header=None)
    cw = lambda x: [word.encode('utf-8') for word in jieba.cut(x) if word not in stopwords and word.strip() != '' and word.encode('utf-8') in dictionary.index]
    contents['words'] = contents[col_content].apply(cw)
    get_sent = lambda x: list(dictionary['id'][x])
    contents['sent'] = contents['words'].apply(get_sent)  # 速度太慢,统计每个词出现的次数
    print("Pad sequences (samples x time)")
    contents['sent'] = list(sequence.pad_sequences(contents['sent'], maxlen=length))
    x = np.array(list(contents['sent']))  # 训练集
    y = np.zeros((len(list(contents[col_tag])), tag_num))
    for i in range(len(list(contents[col_tag]))):
        for j in range(tag_num):
            if contents[col_tag][i] == j:
                y[i][j] = 1
    return x, y


# dictionary model 特征抽取


def word_vector(pair, posdict, negdict, inverse, adv):
    """
    将word转化为向量
    :param pair: 词对,(word, flag)
    :param posdict: positive 词库
    :param negdict: negtive词库
    :param inverse: inverse词库
    :param adv: adv 词库
    :return:
    """
    word_vec = np.zeros(9)
    if pair.word in posdict:
        word_vec[0] = 1
    if pair.word in negdict:
        word_vec[1] = 1
    if pair.word in inverse:
        word_vec[2] = 1
    if pair.word in adv:
        word_vec[3] = 1
    if pair.flag == 'n':
        word_vec[4] = 1
    if pair.flag == 'v':
        word_vec[5] = 1
    if pair.flag == 'a':
        word_vec[6] = 1
    if pair.flag == 'd':
        word_vec[7] = 1
    if pair.flag == 'x':
        word_vec[8] = 1
    return word_vec


def review2matrix(review, posdict, negdict, inverse, adv):  # 将一句话表示为词的矩阵
    """
    将一句话表示为词的矩阵
    """
    matrix = []
    for pair in review:
        word_vec = word_vector(pair, posdict, negdict, inverse, adv)
        matrix.append(word_vec)
    return matrix


def reviews2matrix(reviews, posdict, negdict, inverse, adv):  # 将所有review表示为词的矩阵
    """
    将所有的句子全部表示为词的矩阵
    """
    reviews_matrix = []
    for review in reviews:
        matrix = review2matrix(review, posdict, negdict, inverse, adv)
        reviews_matrix.append(matrix)
    return reviews_matrix


def matrix2vec(matrix):
    """
    将句子表示为词向量的和
    """
    sent_train_x = []
    for review_matrix in matrix:
        sum_vec = np.zeros(9)
        for vec in review_matrix:
            sum_vec += vec
        sent_train_x.append(list(sum_vec))
    return sent_train_x


def extract_dictionary_feature(file_name, col_tag=0, col_content=1):
    # 载入词表
    adv = codecs.open('./data/vocabulary/adv.txt', 'rb', encoding='utf-8').read().split('\n')
    inverse = codecs.open('./data/vocabulary/inverse.txt', 'rb', encoding='utf-8').read().split('\n')
    negdict = codecs.open('./data/vocabulary/negdict.txt', 'rb', encoding='utf-8').read().split('\n')
    posdict = codecs.open('./data/vocabulary/posdict.txt', 'rb', encoding='utf-8').read().split('\n')

    contents = pd.read_excel(file_name, header=None)

    print 'cut words...'
    cw = lambda x: [pair for pair in psg.lcut(x) if pair.word not in stopwords]
    contents['pairs'] = contents[col_content].apply(cw)
    matrix = reviews2matrix(list(contents['pairs']), posdict, negdict, inverse, adv)
    x = matrix2vec(matrix)
    y = list(contents[col_tag])
    return x, y
