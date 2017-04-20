# -*- coding:utf-8 -*-
"""
情感词的加载
"""
import re
import time
import codecs
import math
import jieba.posseg as pseg
from collections import namedtuple


##########################################################################################
# 情感词典的加载
##########################################################################################
if __name__ == "__main__":
    dict_path = "../dictionary/"
else:
    dict_path = "./util/sentiment/dictionary/"

Pair = namedtuple("Pair", ["word", "flag"])

def get_words_set():
    # 获得基本关键词集合
    f_set_neg_prefix = set(codecs.open(dict_path + 'neg_prefix.txt','r','utf-8').read().strip(u'\ufeff').strip().split(','))
    f_set_very_prefix = set(codecs.open(dict_path + 'very_prefix.txt','r','utf-8').read().strip(u'\ufeff').strip().split(','))
    f_set_adv = set(codecs.open(dict_path + 'pi_adv_prefix.txt','r','utf-8').read().strip(u'\ufeff').strip().split(','))
    f_set_verb = set(codecs.open(dict_path + 'pi_verb.txt','r','utf-8').read().strip(u'\ufeff').strip().split(','))
    f_set_double_none_prefix = set(codecs.open(dict_path + 'double_none_prefix.txt','r','utf-8').read().strip(u'\ufeff').strip().split(','))

    # 获取情感词集合
    f_set_negative_word = set()
    for line in codecs.open(dict_path + 'negative.txt','r','utf-8').readlines():
        if line.strip() != '':
            f_set_negative_word.add(line.strip())

    f_set_positive_word = set()
    for line in codecs.open(dict_path + 'positive.txt','r','utf-8').readlines():
        if line.strip() != '':
            f_set_positive_word.add(line.strip())

    # 获得位置无关的情感值词典
    f_set_PI_word = {u'挑选', u'筹备', u'挑一', u'挑两', u'挑几'}
    for curradv in f_set_adv:
        for currverb in f_set_verb:
            f_set_PI_word.add(curradv + currverb)
    output_set = {
        "neg_prefix": f_set_neg_prefix,
        "very_prefix": f_set_very_prefix,
        "neg_words": f_set_negative_word,
        "pos_words":  f_set_positive_word,
        "PI_words": f_set_PI_word,
        "double_none_prefix": f_set_double_none_prefix
    }
    return output_set


output = get_words_set()
set_neg_prefix = output["neg_prefix"]
set_very_prefix = output["very_prefix"]
set_negative_word = output["neg_words"]
set_positive_word = output["pos_words"]
set_PI_word = output["PI_words"]
double_none_prefix = output["double_none_prefix"]


def get_sentiment_dict():
    # 获得带有情感分值的词典
    dict_word_score = {}        # dict(key=word, value=sentiment_value)
    dict_negword_score = {}
    dict_posword_score = {}
    for line in codecs.open(dict_path + 'opinion_word.txt','r','utf-8').readlines():
        if line.strip() != '':
            currList = line.split(',')
            currWord = currList[0]
            currScore = float(currList[1])
            if (currScore > 0.0 or currScore < 0.0) and currWord not in dict_word_score.keys():
                div = 1.0
                if currScore > 0.0:
                    div = 2.2
                dict_word_score[currWord] = currScore / div
            if (currScore > 0.0) and currWord not in dict_posword_score.keys():
                dict_posword_score[currWord] = currScore / 2.2
            if (currScore < 0.0) and currWord not in dict_negword_score.keys():
                dict_negword_score[currWord] = currScore

    # 为前面的正负情感词集合赋予情感值
    lostCount = 0
    for currWord in set_negative_word:
        if currWord not in dict_word_score.keys() and currWord.endswith(u'的') == False and currWord != u'东西':
            lostCount+=1
            #print currWord
            dict_word_score[currWord] = -0.1
    for currWord in set_positive_word:
        if currWord not in dict_word_score.keys() and currWord.endswith(u'的') == False:
            lostCount+=1
            #print currWord
            dict_word_score[currWord] = 0.1
    print 'initial done.'
    return dict_word_score, dict_negword_score, dict_posword_score

dict_word_score, dict_negword_score, dict_posword_score = get_sentiment_dict()


##########################################################################################
# 情感值计算函数
##########################################################################################
def segment_sentences(sentence):
    """
    为了避免句子过长导致情感值偏激
    :param sentence:
    :return:
    """
    end_symbols = [u"。", u"!", u"?", u"？", u"！", u"\t", u"\n"]
    sentences_list = []
    temp = [sentence]
    for sym in end_symbols:
        sentences_list = []
        for sent in temp:
            sentences_list += sent.split(sym)
        temp = sentences_list
    return sentences_list


def get_sentiment_single(input_text):
    """
    统计情感词来获得情感值
    :param input_text:
    :return:
    """
    content_list = segment_sentences(input_text)
    sentiment_acc_score_list = []
    posi_score_list = []
    nega_score_list = []
    pi_score_list = []
    for content in content_list:
        sentiment_acc_score = 0.0
        posi_score = 0.0
        nega_score = 0.0
        pi_score = 0.0
        pi_score = get_pi_score(content)
        for curr_word in dict_word_score.keys():
            if curr_word in content:
                word_count = content.count(curr_word)

                # 对否定前缀的处理
                for curr_neg_prefix in set_neg_prefix:
                    word_count -= content.count(curr_neg_prefix + curr_word)

                # 出现了程度修饰词情感值加倍
                for curr_very_prefix in set_very_prefix:
                    word_count += content.count(curr_very_prefix + curr_word)

                if word_count == 1:
                    sentiment_acc_score += dict_word_score[curr_word]
                    if dict_word_score[curr_word] > 0.0:
                        posi_score += dict_word_score[curr_word]
                    elif dict_word_score[curr_word] < 0.0:
                        nega_score += dict_word_score[curr_word]
                elif word_count > 1:
                    # 对同一个情感词出现了多次的情况进行权衡
                    sentiment_acc_score += dict_word_score[curr_word] + \
                                           dict_word_score[curr_word] * math.log(word_count - 0.9)
                    if dict_word_score[curr_word] > 0.0:
                        posi_score += dict_word_score[curr_word] + \
                                      dict_word_score[curr_word] * math.log(word_count - 0.9)
                    elif dict_word_score[curr_word] < 0.0:
                        nega_score += dict_word_score[curr_word] + \
                                      dict_word_score[curr_word] * math.log(word_count - 0.9)

        sentiment_acc_score_list.append(sentiment_acc_score)
        posi_score_list.append(posi_score)
        nega_score_list.append(nega_score)
        pi_score_list.append(pi_score)

    sentiment_acc_score = sum(sentiment_acc_score_list) / float(len(sentiment_acc_score_list))
    posi_score = sum(posi_score_list) / float(len(posi_score_list))
    nega_score = sum(nega_score_list) / float(len(nega_score_list))
    pi_score = sum(pi_score_list) / float(len(pi_score_list))

    return sentiment_acc_score, posi_score, nega_score, pi_score



def do_adj(s_w, t_w, t_w_pair, exclude_set, curr_index, sentence):
    """
    形容词会同化被形容的内容,如:善意的谎言
    :param s_w:
    :param t_w:
    :param t_w_pair:
    :param exclude_set:
    :param curr_index:
    :param sentence:
    :return:
    """
    score = dict_word_score[s_w] / 10000.
    if s_w not in exclude_set:
        exclude_set[s_w] = [1, [curr_index]]
    else:
        exclude_set[s_w][0] += 1
        exclude_set[s_w][1].append(curr_index)
    return score


def do_verb(s_w, t_w, t_w_pair, exclude_set, curr_index, sentence):
    """
    谓宾关系会改变原有的情感倾向,如:"消灭敌人"/"鼓励恶意的行为"/"赞同鬼子的意见"
    :param s_w:
    :param t_w:
    :param t_w_pair:
    :param exclude_set:
    :param curr_index:
    :param sentence:
    :return:
    """
    score = 0
    if t_w_pair.word in dict_word_score.keys():
        score_1 = prefix_process(curr_index, sentence, score=dict_word_score[t_w_pair.word])
        score_2 = prefix_process(curr_index, sentence, score=dict_word_score[s_w])
        flag = 1 if score_1 * score_2 >= 0 else -1
        score += flag * (abs(score_1) + abs(score_2))
        if t_w_pair.word not in exclude_set:
            exclude_set[t_w_pair.word] = [1, [curr_index]]
        else:
            exclude_set[t_w_pair.word][0] += 1
            exclude_set[t_w_pair.word][1].append(curr_index)
    elif t_w in dict_word_score.keys():
        score_1 = prefix_process(curr_index, sentence, score=dict_word_score[t_w])
        score_2 = prefix_process(curr_index, sentence, score=dict_word_score[s_w])

        flag = 1 if score_1 * score_2 >= 0 else -1
        score += flag * (abs(score_1) + abs(score_2))
        if t_w not in exclude_set:
            exclude_set[t_w] = [1, [curr_index]]
        else:
            exclude_set[t_w][0] += 1
            exclude_set[t_w][1].append(curr_index)
    return score


def check_symbol(sentence):
    """
    判断一句话中间是否有指定的标点符号
    :param sentence:
    :return:
    """
    symbol_list = [u"。", u"!", u"?", u"？", u"！", u"\t", u"\n", u'，', u'；', u',']
    for symbol in symbol_list:
        if symbol in sentence:
            return True
    return False


def prefix_process(curr_index, sentence, score):
    """
    对否定前缀和程度前缀的处理
    :param curr_index:  w 在 sentence 中的首字索引
    :param score:       单词的情感值
    :param sentence:    句子
    :return:
    """
    num_cnt = 5
    if curr_index - num_cnt > 0:
        seg = sentence[curr_index - num_cnt:curr_index]
    else:
        seg = sentence[0:curr_index]

    # 对否定前缀的处理
    for curr_neg_prefix in double_none_prefix:
        if seg.endswith(curr_neg_prefix):
            return 0.8 * score

    # 对否定前缀的处理
    for curr_neg_prefix in set_neg_prefix:
        if seg.endswith(curr_neg_prefix):
            temp_pair = pseg.lcut(sentence[0:curr_index])
            for i, (w, f) in enumerate(reversed(temp_pair)):
                if f.startswith(u"x"):
                    break
                elif f.startswith(u"r") or f.startswith(u"n") or f.startswith(u"m"):
                    if (len(temp_pair)-i-2) > 0 and temp_pair[len(temp_pair)-i-2].word in set_neg_prefix:
                        return 1.3 * score
            return -1.3 * score

    temp_pair = pseg.lcut(seg)
    for i, (w, f) in enumerate(reversed(temp_pair)):
        if f.startswith(u"x"):
            break
        elif f.startswith(u"r") or f.startswith(u"n") or f.startswith(u"m"):
            if temp_pair[len(temp_pair)-i-2].word in set_neg_prefix:
                return -0.6 * score

    # 出现了程度修饰词情感值加倍
    for curr_very_prefix in set_very_prefix:
        if seg.endswith(curr_very_prefix):
            return 1.3 * score
    return score


def process_n_i_a(i_point, sentiment_acc_score, curr_word, content, prefix_verb_set):
    """
    处理被判别为名词/谚语/形容词的情感词
    :param i_point:     该单词在原句中的起始index
    :param sentiment_acc_score:     当前的情感值
    :param curr_word:   当前的单词
    :param content:     原句
    :param prefix_verb_set:     排除词字典,dict(key=单词, value=[该单词被排除的次数, list(该单词被排除的索引)])
    :return:    更新后的情感值
    """
    if curr_word in prefix_verb_set.keys() and i_point in prefix_verb_set[curr_word][1]:
        return sentiment_acc_score
    temp_score = sentiment_acc_score

    # 往前看,形容词和动词对它们的影响
    de_flag = False
    for ii_point in range(1, 6, 1):
        if i_point < ii_point or (i_point - ii_point <= 0):
            continue
        temp_w = content[i_point - ii_point:i_point]
        if check_symbol(temp_w):
            break
        if temp_w.startswith(u"的"):
            de_flag = True
            continue
        temp_w_pair = pseg.lcut(temp_w)[0]
        if de_flag is True and temp_w_pair.flag.startswith(u"v"):
            if temp_w_pair.word not in dict_word_score.keys():
                continue
            temp_w_pair = Pair(temp_w_pair.word, u"a")

        # 在没有句法分析的情况下先根据词性来判断,后期最好写成规则
        if temp_w_pair.flag.startswith(u"a"):
            sentiment_acc_score += do_adj(
                s_w=curr_word, t_w=temp_w, t_w_pair=temp_w_pair,
                exclude_set=prefix_verb_set, curr_index=i_point, sentence=content)
        elif temp_w_pair.flag.startswith(u"v"):
            sentiment_acc_score += do_verb(
                s_w=curr_word, t_w=temp_w, t_w_pair=temp_w_pair,
                exclude_set=prefix_verb_set, curr_index=i_point - ii_point, sentence=content)
    # 往后看,"被"的影响
    for ii_point in range(1, 8, 1):
        if i_point + ii_point + len(curr_word) > len(content):
            continue
        temp_w = content[i_point + len(curr_word): i_point + ii_point + len(curr_word)]
        if check_symbol(temp_w):
            break
        if not temp_w.startswith(u"被"):
            break
        temp_w_pair = pseg.lcut(temp_w)[-1]

        # 排除 动词+语气词 的干扰
        if temp_w_pair.flag.startswith(u"u"):
            temp_w_pair = Pair(
                pseg.lcut(temp_w)[-2].word + pseg.lcut(temp_w)[-1].word,
                pseg.lcut(temp_w)[-2].flag
            )
        if temp_w_pair.flag.startswith(u"v"):
            sentiment_acc_score += do_verb(
                s_w=curr_word, t_w=temp_w, t_w_pair=temp_w_pair,
                exclude_set=prefix_verb_set,
                curr_index=i_point + ii_point + len(curr_word) - len(temp_w_pair.word),
                sentence=content)
    # 若情感值没有变化,则直接使用单词本身的情感值
    if temp_score == sentiment_acc_score:
        sentiment_acc_score += prefix_process(i_point, content, score=dict_word_score[curr_word])
    return sentiment_acc_score


def process_v(i_point, sentiment_acc_score, curr_word, content, prefix_verb_set):
    """
    处理被判别为动词的情感词
    :param i_point:     该单词在原句中的起始index
    :param sentiment_acc_score:     当前的情感值
    :param curr_word:   当前的单词
    :param content:     原句
    :param prefix_verb_set:     排除词字典,dict(key=单词, value=[该单词被排除的次数, list(该单词被排除的索引)])
    :return:    更新后的情感值
    """
    if curr_word in prefix_verb_set.keys() and i_point in prefix_verb_set[curr_word][1]:
        return sentiment_acc_score
    temp_score = sentiment_acc_score
    # 向后看,检查宾语
    if i_point + len(curr_word) < len(content):
        if content[i_point + len(curr_word)] == u"的":
            sentiment_acc_score = process_n_i_a(i_point, sentiment_acc_score, curr_word, content, prefix_verb_set)
            return sentiment_acc_score
    for ii_point in range(1, 6, 1):
        if i_point + ii_point + len(curr_word) > len(content):
            continue
        temp_w = content[i_point + len(curr_word): i_point + ii_point + len(curr_word)]
        if check_symbol(temp_w):
            break
        temp_w_pair = pseg.lcut(temp_w)[-1]
        if temp_w_pair.flag.startswith(u"n"):
            sentiment_acc_score += do_verb(
                s_w=curr_word, t_w=temp_w, t_w_pair=temp_w_pair,
                exclude_set=prefix_verb_set,
                curr_index=i_point + ii_point + len(curr_word) - len(temp_w_pair.word),
                sentence=content)
    # 向前看,检查"被"
    bei_flag = 0    # 0:无  1:有  2:否定,如"没有被"
    for ii_point in range(1, 20, 1):
        if i_point < ii_point or (i_point - ii_point <= 0):
            continue
        temp_w = content[i_point - ii_point: i_point]
        if check_symbol(temp_w):
            break
        temp_pair = pseg.lcut(content[0:i_point - ii_point])
        if temp_w.startswith(u"被"):
            bei_flag = 1
            for i, (w, f) in enumerate(reversed(temp_pair)):
                if f.startswith(u"x"):
                    break
                elif f.startswith(u"r") or f.startswith(u"n") or f.startswith(u"m"):
                    if temp_pair[len(temp_pair) - i - 2].word in set_neg_prefix:
                        bei_flag = 2
        for curr_neg_prefix in set_neg_prefix:
            if temp_w.startswith(curr_neg_prefix + u"被"):
                bei_flag = 2
                for i, (w, f) in enumerate(reversed(temp_pair)):
                    if f.startswith(u"x"):
                        break
                    elif f.startswith(u"r") or f.startswith(u"n") or f.startswith(u"m"):
                        if temp_pair[len(temp_pair) - i - 2].word in set_neg_prefix:
                            bei_flag = 1
        if bei_flag == 1:
            temp_w_pair = pseg.lcut(temp_w)[0]
            if temp_w_pair.flag.startswith(u"n"):
                sentiment_acc_score += do_verb(
                    s_w=curr_word, t_w=temp_w, t_w_pair=temp_w_pair,
                    exclude_set=prefix_verb_set,
                    curr_index=i_point - ii_point, sentence=content)
        elif bei_flag == 2:
            temp_w_pair = pseg.lcut(temp_w)[0]

            if temp_w_pair.flag.startswith(u"n"):
                sentiment_acc_score -= 0.5 * do_verb(
                    s_w=curr_word, t_w=temp_w, t_w_pair=temp_w_pair,
                    exclude_set=prefix_verb_set,
                    curr_index=i_point - ii_point, sentence=content)
    # 若情感值没有变化,则直接使用单词本身的情感值
    if temp_score == sentiment_acc_score:
        if bei_flag == 2:
            sentiment_acc_score -= prefix_process(i_point, content, score=dict_word_score[curr_word])
        else:
            sentiment_acc_score += prefix_process(i_point, content, score=dict_word_score[curr_word])
    return sentiment_acc_score
