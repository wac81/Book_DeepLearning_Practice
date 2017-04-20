# -*- coding: utf-8 -*-

"""main function is choseAnswer(q, JingYan, ZhiDao, ZhiHu).

说明：
使用 LSI 算法，从备选答案中选出与问题 “q” 最相近的答案,并去掉答案之间的冗余

"""
from __future__ import print_function
from __future__ import absolute_import
import codecs

import jieba
import jieba.analyse
import jieba.posseg
from gensim import corpora, models, similarities

from util.base import getAbstract

filtrationword = codecs.open("./dictionary/filtrationword.txt", encoding='UTF-8').readlines()
jieba.load_userdict('./dictionary/tagdict.txt')


def isJux(answer):
    """
    判断是否是并列关系，是，返回1.递进返回0
    :param answer:
    :return:
    """
    tag = []
    seg = jieba.posseg.cut(answer)
    for i in seg:
        if i.flag == '*':
            tag.extend((i.word, i.flag))
    if len(tag)/len(answer.split(u'。')) > 0.5:
        return 0
    else:
        return 1


def getCompress(answer):
    """
    将从 choseAnswer(q, JingYan, ZhiDao, ZhiHu)中取出的答案之中，存在并列关系的答案压缩
    :param answer:
    :return:
    """
    global filtrationword

    if answer == None:
        return None
    if isJux(answer) == 1 and len(answer) > 80:
        answer = ''.join(getAbstract.getAbstract(answer))
    for i in filtrationword:
        if i[:-1] in answer:
            answer = answer.replace(i[:-1], '')
    return answer


def choseAnswer(q, nest_list_answer):
    """
    首先取每一句的摘要
    然后使用 LSI 算法，从备选答案中选出与问题 “q” 最相近的答案
    :param q:   unicode
    :param nest_list_answer:    list(list(each_answer))
    :return:
    """
    Answer_dict = {}
    Answer_list = []
    ske_list = []

    # 去掉不合适的标点，并连接成 string “s”
    # zw:后期需要探讨是否真的需要去标点，不需要的话就把合并为text的过程都拿到外面去
    s = ''
    for list_answer in nest_list_answer:
        for i in list_answer:
            if i is not None and len(i) != 0:
                if i[len(i)-1] not in (u'。', u'.', u'!', u'！', u'？', u'?', u';', u'；', '\n'):
                    s += i+'.'
                else:
                    s += i

    # 根据标点符号分词为 list
    for x in getAbstract.SentenceCut(s):
        x = x.strip('\n').strip('\r').strip('\t').strip(' ')
        if len(x) != 0:
            Answer_list.append(x)

    if len(Answer_list) > 0:
        for i in Answer_list:
            # 从子句中取出 “关键词”
            Answer_dict[i] = getAbstract.Segmentation([i])
    else:
        return None

    # if len(Answer_list)>0:
    #     for i in Answer_list:
    #         for j in getAbstract.Segmentation(getAbstract.SentenceCut(i)):
    #             ske_list+=j
    #         Answer_dict[i]=ske_list
    #         ske_list=[]
    # else:
    #     return None

    # 将从每个子句中取出的名词，存入列表 seg_list
    seg_list = []
    for i in Answer_dict.keys():
        if len(Answer_dict[i]) > 0:
            seg_list.append(Answer_dict[i][0])

    # 使用 LSI 模型取出与问题 “q” 最相近的名词
    topic_list = jieba.cut(q)
    dictionary = corpora.Dictionary(seg_list)
    corpus = [dictionary.doc2bow(seglist) for seglist in seg_list]
    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = tfidf[corpus]
    seg_list_len = len(seg_list)
    if seg_list_len < 5:
        seg_list_len = 5
    lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=seg_list_len/5)
    corpus_lsi = lsi[corpus_tfidf]
    index = similarities.MatrixSimilarity(corpus_lsi)

    query_bow = dictionary.doc2bow(topic_list)
    query_lsi = lsi[query_bow]
    sims = index[query_lsi]
    sort_sims = sorted(enumerate(sims), key=lambda item: -item[1])

    Answer_list = []
    a = 0
    for k, v in Answer_dict.items():
        if a == 56:
            pass
        if (v is not None) and (len(v) != 0):
            for index, sim_val in sort_sims[0:5]:
                if v[0] == seg_list[index]:
                    Answer_list.append((k, sim_val))
        a += 1
        # print(a)
        # if a > 300:
        #     break
        # if len(Answer_list) > 0:
        #     for i in Answer_list:
        #         if i[0] not in q:
        #             return i

    if len(Answer_list) == 0:
        return None
    else:
        return Answer_list
