# -*-coding:utf-8 -*-
from __future__ import print_function, division
import os
import codecs
import numpy as np
from numpy.random import shuffle
import jieba.posseg as pseg
from sklearn import svm
from sklearn.externals import joblib


if __name__ == "__main__":
    stop_word_path = "../../dictionary/"
    train_corpus = "../../Corpus/RTE/textual_entailment.txt"
else:
    stop_word_path = "./dictionary/"
    train_corpus = "./Corpus/RTE/textual_entailment.txt"


class RTEFeatureExtractor(object):
    """
    This builds a bag of words for both the text and the hypothesis after
    throwing away some stopwords, then calculates overlap and difference.
    """
    def __init__(self, rtepair, stop=True, lemmatize=False):
        """
        :param rtepair: a ``RTEPair`` from which features should be extracted, (txt, hyp)
        :param stop: if ``True``, stopwords are thrown away.
        :type stop: bool
        """
        global stop_word_path
        self.stop = stop
        self.stopwords = codecs.open(stop_word_path + 'stopwords.txt', encoding='UTF-8').read()
        self.negwords = set([u"不", u"不是", u"不对", u"没", u"没有", u"失败", u"拒绝", u"否定", u"否认"])

        text_words = pseg.lcut(rtepair[0])
        hyp_words = pseg.lcut(rtepair[1])
        self.text_words = set()
        self.hyp_words = set()

        # 针对特殊标记做正则表达式替换
        pass

        # 使用 wordnet 实现同义词的替换
        if lemmatize:
            pass

        # 去停用词
        for word, flag in text_words:
            if word not in self.stopwords:
                self.text_words.add((word, flag))

        for word, flag in hyp_words:
            if word not in self.stopwords:
                self.hyp_words.add((word, flag))

        # 集合操作
        self._overlap = self.hyp_words & self.text_words        # hyp 和 text共有
        self._hyp_extra = self.hyp_words - self.text_words      # hyp有 text没有
        self._txt_extra = self.text_words - self.hyp_words      # text有 hyp没有

    def overlap(self, toktype, debug=False):
        """
        Compute the overlap between text and hypothesis.

        :param toktype: distinguish Named Entities from ordinary words
        :type toktype: 'ne' or 'word'
        """
        ne_overlap = set(word_flag for word_flag in self._overlap if ne(word_flag))
        if toktype == 'ne':
            if debug:
                print("ne overlap", ne_overlap)
            return ne_overlap
        elif toktype == 'word':
            if debug:
                print("word overlap", self._overlap - ne_overlap)
            return self._overlap - ne_overlap
        else:
            raise ValueError("Type not recognized:'%s'" % toktype)

    def hyp_extra(self, toktype, debug=True):
        """
        Compute the extraneous material in the hypothesis.

        :param toktype: distinguish Named Entities from ordinary words
        :type toktype: 'ne' or 'word'
        """
        ne_extra = set(word_flag for word_flag in self._hyp_extra if ne(word_flag))
        if toktype == 'ne':
            return ne_extra
        elif toktype == 'word':
            return self._hyp_extra - ne_extra
        else:
            raise ValueError("Type not recognized: '%s'" % toktype)


def ne(word_flag):
    """
    判断 word_flag 是否为设定的实体词
    :param word_flag: (word, flag)
    :return: True or False
    """
    entity_set = {
        u't',   # 时间
        u'n', u'nr', u'ns', u'nt', u'nz',   # 名词
        u'i',   # 成语
        u'z', u'zg'    # 状态词
    }
    for entity_flag in entity_set:
        if word_flag[1].startswith(entity_flag):
            return True
    return False


def rte_features(rtepair):
    """
    RTE class function
    :param rtepair: (txt, hyp)
    :return:
    """
    extractor = RTEFeatureExtractor(rtepair)
    features = dict()
    # features['alwayson'] = True
    features['word_overlap'] = len(extractor.overlap('word'))               # hyp 与 text 中重复的 word
    features['word_hyp_extra'] = len(extractor.hyp_extra('word'))           # hyp 有 但 text 中没有的 word
    features['ne_overlap'] = len(extractor.overlap('ne'))                   # hyp 与 text 中重复的 ne
    features['ne_hyp_extra'] = len(extractor.hyp_extra('ne'))               # hyp 有 但 text 中没有的 ne
    features['neg_txt'] = len(extractor.negwords & extractor.text_words)    # text 中的 否定词
    features['neg_hyp'] = len(extractor.negwords & extractor.hyp_words)     # hyp 中的 否定词

    features_list = []
    for k in features:
        features_list.append(features[k])

    return features_list


def parse_corpus(test_proportion):
    """
    解析文本文档
    :param test_proportion: 测试集所占的比例
    :return: (pair, label) for train and test
    """
    global train_corpus
    corpus = []
    txt = ""
    hyp = ""
    with open(train_corpus) as fp:
        line_list = fp.readlines()
        for line in line_list:
            line = line.strip('\n').strip('\r').strip(' ')
            if len(line) == 0:
                continue
            if ':' in line:
                flag, content = line.split(':')
                if flag == 'H':
                    hyp = content
                elif flag == 'T':
                    txt = content
                elif flag == 'label':
                    corpus.append(((txt, hyp), float(content)))
    cut_index = int(len(corpus) * (1 - test_proportion))
    corpus_arr = np.array(corpus)
    shuffle(corpus_arr)

    train = corpus_arr[0:cut_index]
    test = corpus_arr[cut_index:]
    return train, test


def doc_vectorize(txt, hyp, features=rte_features):
    """
    在预测阶段对被预测的对象的向量化
    :param txt:
    :param hyp:
    :param features:
    :return:
    """
    X_l = []
    X_l.append(features((txt, hyp)))
    X = np.array(X_l)
    return X


def rte_classifier(features=rte_features):
    """
    Classify RTEPairs
    根据从语料中提取的特征训练一个分类器
    :param features:
    """
    test_proportion = 0.2
    train, test = parse_corpus(test_proportion)

    # Train up a classifier.
    print('Training classifier...')
    clf = svm.SVC()
    X_l = []
    y_l = []
    for i in train:
        X_l.append(features(i[0]))
        y_l.append(i[1])
    X = np.array(X_l)
    y = np.array(y_l)
    clf.fit(X, y)

    # Run the classifier on the test data.
    print('Testing classifier...')
    X_l = []
    y_l = []
    for i in test:
        X_l.append(features(i[0]))
        y_l.append(i[1])
    X_t = np.array(X_l)
    y_t = np.array(y_l)
    test_label = clf.predict(X_t)
    cnt = 0
    for i in (test_label - y_t):
        if i == 0:
            cnt += 1
    acc = cnt / len(test_label)
    print('Accuracy: %6.4f' % acc)

    # Return the classifier
    return clf


def save_clf(clf, pkl_name):
    """

    :param clf:
    :param pkl_name:
    :return:
    """
    path = "/".join(pkl_name.split('/')[:-1])
    if not os.path.exists(path):
        os.mkdir(path)
    joblib.dump(clf, pkl_name)


def load_clf(pkl_name):
    """

    :param pkl_name:
    :return:
    """
    clf = joblib.load(pkl_name)
    return clf


#################################################
def train():
    """
    运行程序训练并保存模型
    注意：函数中的路径名均为相对路径，所以训练需要运行当前文件，模型名更改后，需要对应改变 cal_rte 中的模型名称
    :return:
    """
    clf = rte_classifier()
    print("clf dump: ", clf)
    pkl_name = "./rte_clf/svm_clf.pkl"
    save_clf(clf, pkl_name)
    print("save clf in %s" % pkl_name)
    print("loading clf...")
    clf_load = load_clf(pkl_name)
    print("clf load: ", clf_load)


def cal_rte(doc_list, q):
    """
    计算两段文本之间的蕴含关系
    注意：如果需要移动该模块，请带着“大写字母一同移动”，并更改 load_clf 中的地址
    :param doc_list:
    :param q:
    :return:
    """
    output = []

    # 以下地址相对被运行的文件
    clf = load_clf("./models/RTE_MODEL/rte_clf/svm_clf.pkl")
    for doc in doc_list:
        X = doc_vectorize(doc.lower(), q.lower())   # text
        y = clf.predict(X)          # score
        output.append((doc, y))
    return output


if __name__ == '__main__':
    train()


