# -*- coding:utf-8 -*-
from __future__ import print_function
import numpy as np
import os
import sys
import jieba
import time
import jieba.posseg as pseg
import codecs
import multiprocessing
import json
# from gensim.models import Word2Vec,Phrases
from gensim import models,corpora
import logging
# auto_brand = codecs.open("Automotive_Brand.txt", encoding='utf-8').read()

sys.path.append("../../")
sys.path.append("../../langconv/")
sys.path.append("../../parser/")
# import xmlparser
from xmlparser import *
from langconv import *

# logger = logging.getLogger(program)
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
logging.root.setLevel(level=logging.INFO)
# logger.info("running %s" % ' '.join(sys.argv))


def delNOTNeedWords(content,customstopwords=None):
    # words = jieba.lcut(content)
    if customstopwords == None:
        customstopwords = "stopwords.txt"
    import os
    if os.path.exists(customstopwords):
        stop_words = codecs.open(customstopwords, encoding='UTF-8').read().split(u'\n')
        customstopwords = stop_words

    result=''
    return_words = []
    # for w in words:
    #     if w not in stopwords:
    #         result += w.encode('utf-8')  # +"/"+str(w.flag)+" "  #去停用词
    words = pseg.lcut(content)

    for word, flag in words:
        # print word.encode('utf-8')
        tempword = word.encode('utf-8').strip(' ')
        if (word not in customstopwords and len(tempword)>0 and flag in [u'n',u'nr',u'ns',u'nt',u'nz',u'ng',u't',u'tg',u'f',u'v',u'vd',u'vn',u'vf',u'vx',u'vi',u'vl',u'vg', u'a',u'an',u'ag',u'al',u'm',u'mq',u'o',u'x']):
            # and flag[0] in [u'n', u'f', u'a', u'z']):
            # ["/x","/zg","/uj","/ul","/e","/d","/uz","/y"]): #去停用词和其他词性，比如非名词动词等
            result += tempword # +"/"+str(w.flag)+" "  #去停用词
            return_words.append(tempword)
    return result,return_words


def get_save_wikitext(wiki_filename,text_filename):
    output = open(text_filename, 'w')
    wiki = corpora.WikiCorpus(wiki_filename, lemmatize=False, dictionary={})
    for text in wiki.get_texts():
        # text = delNOTNeedWords(text,"../../stopwords.txt")[1]
        output.write(" ".join(text) + "\n")
        i = i + 1
        if (i % 10000 == 0):
            logging.info("Saved " + str(i) + " articles")
    output.close()

def load_save_word2vec_model(line_words, model_filename):
    # 模型参数
    feature_size = 500
    content_window = 5
    freq_min_count = 3
    # threads_num = 4
    negative = 3   #best采样使用hierarchical softmax方法(负采样，对常见词有利)，不使用negative sampling方法(对罕见词有利)。
    iter = 20

    print("word2vec...")
    tic = time.time()
    if os.path.isfile(model_filename):
        model = models.Word2Vec.load(model_filename)
        print(model.vocab)
        print("Loaded word2vec model")
    else:
        bigram_transformer = models.Phrases(line_words)
        model = models.Word2Vec(bigram_transformer[line_words], size=feature_size, window=content_window, iter=iter, min_count=freq_min_count,negative=negative, workers=multiprocessing.cpu_count())
        toc = time.time()
        print("Word2vec completed! Elapsed time is %s." % (toc-tic))
        model.save(model_filename)
        # model.save_word2vec_format(save_model2, binary=False)
        print("Word2vec Saved!")
    return model

if __name__ == '__main__':

    limit = -1 #该属性决定取wiki文件text tag前多少条，-1为所有
    wiki_filename = './zhwiki-20160203-pages-articles-multistream.xml.bz2'
    wiki_text = './wiki_text.txt'
    wikimodel_filename = './word2vec_wiki.model'
    s_list = []

    get_save_wikitext(wiki_filename,wiki_text)


    for i,text in enumerate(open(wiki_text, 'r')):
        s_list.append(delNOTNeedWords(text,"../../stopwords.txt")[1])
        print(i)

        if i==limit: #取前limit条,-1为所有
            break

    #计算模型
    model = load_save_word2vec_model(s_list,wikimodel_filename)

    #计算相似单词，命令行输入
    while 1:
        print("请输入想测试的单词： ", end='\b')
        t_word = sys.stdin.readline()
        if "quit" in t_word:
            break
        try:
            results = model.most_similar([t_word.decode('utf-8').strip('\n').strip('\r').strip(' ')],topn=30)
        except:
            continue
        for t_w, t_sim in results:
            print(t_w, " ", t_sim)