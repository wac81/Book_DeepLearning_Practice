# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from collections import Counter
import re
import jieba
import jieba.posseg
import jieba.analyse
import numpy as np
from models.RTE_MODEL.textual_entailment import *
from models.SYNTACTIC_CLF.syn_parsing import cal_syn

np.random.seed(12345)


######################################################
# 数字的集合，可以用 pattern.findall() 找到所有的数词
nomal_number_pattern = re.compile(r'(([0-9]+[,.百千万亿\s]?)+)')
chs_number_pattern = re.compile(r'([一二三四五六七八九十]+[百千万亿零个\s]?)+')

# 度量单位的集合
measure_tags = {
    "time":     [
        u'年', u'月', u'日', u'时', u'分',
        u'秒', u'点'
    ],
    "quantity": [
        u'个', u'头', u'块', u'件', u'打',
        u'双', u'袋', u'瓶', u'箱', u'桶',
        u'碗', u'床', u'本', u'台', u'辆',
        u'只'
    ],
    "money":    [
        u'元', u'角', u'分'
    ],
    "distance": [
        u'千米', u'米', u'厘米', u'分米', u'毫米',
        u'微米', u'纳米', u'公里', u'km', u'm',
        u'cm', u'dm', u'mm', u'um', u'nm',
        u'光年'
    ]
}

# 回应语预设
just_response = {
    "agree": [
        u"好的", u"没问题", u"OK",
    ],
    "disagree": [
        u"不行哦～", u"不可以哦～",
    ],
    "yes": [

    ],
    "no": [

    ]
}


#####################################################
# functional
def get_top_word(typeWord, num):
    """
    get top word from typeWord
    取出 list 或 string 中出现 频率 最多的单词
    :param typeWord:  words labeled by "tar" in wordClassific
    :param num: how many top words we will get
    :return:
    """
    if len(typeWord) > 0:
        wordCounts = Counter(typeWord)

        # count how many times the "some word" showed in typeWord
        # get the word with highest frequency
        #
        # e.g.
        # >>> Counter('abcdeabcdabcaba').most_common(3)
        # [('a', 5), ('b', 4), ('c', 3)]

        return wordCounts.most_common(num)[0][0]
    else:
        return None


def get_sentence_from_prefix_word(word, sentence, is_word_in=True):
    """
    返回所有 sentence 中两个 “。”/“.”中间包含 word 的句子组成的 list
    :param word:
    :param sentence:
    :param is_word_in:
    :return: list of sentences
    """
    if word not in sentence:
        return []
    temp_list = sentence.split(word)
    ans_s_1 = []
    ans_s_2 = []
    for i, sub_sent in enumerate(temp_list):
        if i+1 == len(temp_list):
            break
        if is_word_in:
            temp = sub_sent.split(u'。')[-1].strip(' ') + word + temp_list[i+1].split(u'。')[0].strip(' ') + u'。'
        else:
            temp = sub_sent.split(u'。')[-1].strip(' ') + temp_list[i + 1].split(u'。')[0].strip(' ') + u'。'
        temp = temp.strip('\n').strip('\r').strip()
        if len(temp) > 50:
            continue
        if pseg.lcut(temp)[0].flag == u'x' or pseg.lcut(temp)[0].flag == u'w':
            temp = temp[1:]
        ans_s_1.append(temp) if len(sub_sent.split(u'。')[-1]) == 0 else ans_s_2.append(temp)

    if len(ans_s_1) == 0:
        return ans_s_2
    else:
        return ans_s_1


def get_sentence_from_inner_word(word, sentence):
    """

    :param word:
    :param sentence:
    :return:
    """
    sof = u'。'
    sentence = sentence.replace(u'\n', sof)
    if word not in sentence:
        return []
    temp_list = sentence.split(sof)
    ans_s = []
    for i, sub_sent in enumerate(temp_list):
        if word in sub_sent:
            sub_sent = sub_sent.strip('\n').strip('\r').strip(' ')
            if len(sub_sent) == 0:
                continue
            ans_s.append(sub_sent)
    return ans_s


def rte_filter(ans_s, question):
    """

    :param ans_s: 备选答案的列表
    :param question:   所问的问题
    :return:
    """
    ans_s = cal_rte(ans_s, question)
    temp_list = []
    for sent, score in ans_s:
        if score[0] > 0:
            temp_list.append(sent)
    ans_s = temp_list
    del temp_list
    if len(ans_s) == 0:
        return []
    return ans_s


def syn_filter(ans_s, question):
    ans_s = cal_syn(ans_s)
    temp_list = []
    for sent, score in ans_s:
        if score[0] > 0:
            temp_list.append(sent)
    ans_s = temp_list
    del temp_list
    if len(ans_s) == 0:
        return []
    return ans_s


##################################################
# 疑问句 for iknow2
def tezhi_classify(question, flag, text, verbose=0):
    """
    特指问句：
    针对 人/地点/实体/数量/时间 提取相关的关键词
    :param question:
    :param flag:
    :param text:
    :return:
    """
    words = jieba.posseg.cut(text)  # 切词

    timeWord = []  # 时间词, label = time
    locWord = []  # 地点词, label = where
    numWord = []  # 数量词, label = num
    humWord = []  # 人物词, label = who
    neWord = []
    # defWord = []  # 定义，临时不用

    preFlag = 'n'  # 前驱,标记时间词
    preWord = ''  # 前驱词

    if "时间" == flag.split('_')[-1]:    # time
        word_dict = Counter(jieba.cut(text))
        temp_cnt = 0
        most_freq_word = u""
        for i in measure_tags["time"]:
            if word_dict[i] > temp_cnt:
                temp_cnt = word_dict[i]
                most_freq_word = i
        ans_s = get_sentence_from_inner_word(most_freq_word, text)
        num_s = []
        for i in ans_s:
            temp_list = nomal_number_pattern.findall(i)
            for j in temp_list:
                j = j[0]
                if j + most_freq_word in i:
                    num_s.append(j)
        if len(num_s) == 0:
            return None
        most_num = Counter(num_s).most_common(1)[0][0]
        ans_s_temp = []
        for i in ans_s:
            if len(i) > 20:
                continue
            if most_num + most_freq_word in i:
                ans_s_temp.append(i)
        if len(ans_s_temp) == 0:
            return most_num + most_freq_word
        return ans_s_temp[np.random.randint(len(ans_s_temp))]

    elif "数量" == flag.split('_')[-1]:    # num
        word_dict = Counter(jieba.cut(text))
        temp_cnt = 0
        most_freq_word = u""
        most_freq_tag = u""
        for tag in measure_tags:
            if tag == "time":
                continue
            for i in measure_tags[tag]:
                if word_dict[i] > temp_cnt:
                    temp_cnt = word_dict[i]
                    most_freq_word = i
                    most_freq_tag = tag
        print("问题识别： ", most_freq_tag)
        ans_s = get_sentence_from_inner_word(most_freq_word, text)
        num_s = []
        for i in ans_s:
            temp_list = nomal_number_pattern.findall(i)
            for j in temp_list:
                j = j[0]
                if j + most_freq_word in i:
                    num_s.append(j)
        if len(num_s) == 0:
            return None
        most_num = Counter(num_s).most_common(1)[0][0]
        ans_s_temp = []
        for i in ans_s:
            if len(i) > 140:
                continue
            if most_num + most_freq_word in i:
                ans_s_temp.append(i)
        if len(ans_s_temp) == 0:
            return most_num + most_freq_word
        return ans_s_temp[np.random.randint(len(ans_s_temp))]

    elif "人" == flag.split('_')[-1]:     # who
        for i in words:
            if i.flag == 'nr' and i.word not in question:  # 人名
                humWord.append(i.word)
        return get_top_word(humWord, 1)

    elif "地点" == flag.split('_')[-1]:    # where
        for i in words:
            if (i.flag.startswith('ns') or i.flag.startswith('s')) and i.word not in question:  # location
                locWord.append(i.word)
        return get_top_word(locWord, 1)

    elif "实体" == flag.split('_')[-1]:    # what
        # new
        # for i in words:
        #     if i.flag in [u"nr", u"nz", u"nl", u"ng", u"n"] and i.word not in question:
        #         neWord.append(i.word)
        # return get_top_word(neWord, 1)

        # old
        en = jieba.analyse.textrank(text, topK=4, allowPOS=[u"nr", u"nz", u"nl", u"ng", u"n"])
        for i in en:
            en_flag = pseg.lcut(i)[0].flag
            is_flag = False
            if i not in question and en_flag[:2] in [u"nr", u"nz", u"nl", u"ng"]:
                return i
        for i in en:
            en_flag = pseg.lcut(i)[0].flag
            is_flag = False
            if i not in question and u"n" in en_flag:
                return i
        return None

    elif "原因" == flag.split('_')[-1]:
        prefix_ans = {
            u"因为",
            u"由于",
            u"所以",
            u"结果",
            u"由",
            u"多半是",
            u"因"
        }
        ans_s = []
        for i in prefix_ans:
            ans_s += get_sentence_from_prefix_word(i, text)

        if ans_s is None:
            return None
        ans_s = syn_filter(ans_s, question)

        if len(ans_s) != 0:
            ans = ans_s[np.random.randint(len(ans_s))]
        else:
            return None
        if len(ans) == 0:
            return None
        return ans

    elif "意见" == flag.split('_')[-1]:
        q_temp = u""
        question_word = [
            u"怎么样", u"怎样", u"咋样"
        ]
        for i in question_word:
            if i in question:
                q_temp = question[:question.index(i)]
                break

        w_f_list = pseg.lcut(q_temp)
        ans_s = get_sentence_from_prefix_word(q_temp, text)
        if ans_s is not None and len(ans_s) != 0:
            ans_s = syn_filter(ans_s, question)
            if verbose >= 2:
                print("意见 ans: \n", "\n".join(ans_s))
            min_len = 100
            ans_temp = u""
            for s in ans_s:
                if len(s) < min_len:
                    ans_temp = s
                    min_len = len(s)
            if len(ans_temp) > 0:
                return ans_temp

        ans_s = []
        search_list = []
        for w, f in w_f_list:
            if u"n" in f:
                search_list.append(w)

        for i in search_list:
            ans_s += get_sentence_from_prefix_word(i, text)

        if ans_s is None:
            return None
        ans_s = syn_filter(ans_s, question)
        if verbose >= 2:
            print("意见 ans: \n", "\n".join(ans_s))

        if len(ans_s) != 0:
            min_len = 100
            ans_temp = u""
            for s in ans_s:
                if len(s) < min_len:
                    ans_temp = s
                    min_len = len(s)
            if len(ans_temp) > 0:
                ans = ans_temp
            else:
                ans = ans_s[np.random.randint(len(ans_s))]
        else:
            return None
        if len(ans) == 0:
            return None
        return ans

    elif "方式" == flag.split('_')[-1]:
        # 表中单词不被包含
        prefix_ans_1 = {
            u"总之",
            u"总体",
            u"总的",
            u"总结一下",
            u"总结",
            u"一句话",
            u"归根结底"
        }
        # 表中单词被包含
        prefix_ans_2 = {
            u"建议",
            u"试试",
            u"只要",
            u"我觉得",
            u"→",
            u"->"
        }
        ans_s = []
        for i in prefix_ans_1:
            ans_s += get_sentence_from_prefix_word(i, text, is_word_in=False)
        for i in prefix_ans_2:
            ans_s += get_sentence_from_prefix_word(i, text)

        if ans_s is None:
            return None
        ans_s = syn_filter(ans_s, question)
        # ans_s = cal_rte(ans_s, question)
        # temp_list = []
        # for sent, score in ans_s:
        #     if score[0] > 0:
        #         temp_list.append(sent)
        # ans_s = temp_list
        # del temp_list
        # if len(ans_s) == 0:
        #     return None

        if len(ans_s) != 0:
            ans = ans_s[np.random.randint(len(ans_s))]
        else:
            return None

        if len(ans) == 0:
            return None
        return ans

    else:
        return None
