#coding=utf8
import jieba
import remove_NOTneed_word as remove
title_words = jieba.lcut(u'10.1元购家电！iPhone6s-Plus仅4488，海尔热水器699~10亿优惠券狂撒，国庆福利快接着→')
temp = ''

temp,d = remove.delNOTNeedWords(u'10.1元购家电！iPhone6s-Plus仅4488，海尔热水器699~10亿优惠券狂撒，国庆福利快接着→')
# for x in title_words:
#     print x.encode('utf8')
#     temp = temp + x + u'/'
print temp


