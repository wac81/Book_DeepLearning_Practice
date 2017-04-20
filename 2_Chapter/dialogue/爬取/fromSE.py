# -*- coding: utf-8 -*-

"""fromSE: from search engine
主要负责爬虫部分，爬虫的内容为：
+ 百度经验
+ 百度知道
+ 知乎
+ 搜狗
"""

from __future__ import print_function
from __future__ import absolute_import
import sys
import httplib2
import urllib
import urllib2
import cookielib
import threading
import time
import ssl
import uuid
import json
from datetime import datetime
# from urllib.parse import quote
from selenium import webdriver
from lxml import etree
from pyvirtualdisplay import Display
from lxml.html.clean import clean_html, Cleaner
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as ThreadPool

from util.crawler.elastic_manage import es, es_index, es_type

# jieba.enable_parallel()
# jieba.load_userdict('tagdict.txt')


####################################
# Globals
NUM_ITEMS = 5
JingYan_ske = []
ZhiDao_ske = []
ZhiHu_ske = []
SouGou = []

#####################################
# URLs
JINGYAN = "http://jingyan.baidu.com"
ZHIDAO = 'http://zhidao.baidu.com'
ZHIHU = 'http://www.zhihu.com'
SOUGOU = "http://wenwen.sogou.com/"

# Headers
jingyanHeader = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Connection': 'keep-alive',
    'Cookie': 'BAIDUID=2C04DBAF69096E269EA69D7B1034A238:FG=1; BIDUPSID=2C04DBAF69096E269EA69D7B1034A238; PSTM=1443877754; bdshare_firstime=1443877966753; BDUSS=jdtOFVKdmVSdHZVZUN4SmpyLVpmOGxDaHh5UlhQNk1QRGNvQ2trfkZraHZxRVZXQVFBQUFBJCQAAAAAAAAAAAEAAADgefUz0rvN-87evMqzpLj8s6QAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAG8bHlZvGx5Wf; BDRCVFR[feWj1Vr5u3D]=I67x6TjHwwYf0; H_PS_PSSID=1462_17637_18240_18155_12826_18133_17001_17073_15752_12073_18018; PS_REFER=0; Hm_lvt_46c8852ae89f7d9526f0082fafa15edd=1447842345,1448432220,1448619894,1449735979; Hm_lpvt_46c8852ae89f7d9526f0082fafa15edd=1449736189',
    'Host': 'jingyan.baidu.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36'
}
zhidaoHeader = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Cookie': 'BIDUPSID=804E2ABF7C124C08FF10735DC5BCC94D; PSTM=1465906179; IK_CID_74=1; BDUSS=m5xdXF0aEpGUjRPVy1YTnhNS3g5TzFtWFdFaS1QU2hseU5GYUZQYTFnSExCSzVYQVFBQUFBJCQAAAAAAAAAAAEAAAAIXZcNendza3kyMDEwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMt3hlfLd4ZXc; IK_CID_80=4; IK_CID_1=1; BDRCVFR[S4-dAuiWMmn]=I67x6TjHwwYf0; H_PS_PSSID=20668_20674_1425_18241_20415_18134_17001_15178_11766; IK_USERVIEW=1; Hm_lvt_6859ce5aaf00fb00387e6434e4fcc925=1468562545,1468562628,1468575627,1469089370; Hm_lpvt_6859ce5aaf00fb00387e6434e4fcc925=1469089860; IK_D8173601DC25030AA555201171342B76=15; IK_CID_77=9; BAIDUID=D8173601DC25030AA555201171342B76:FG=1',
    'Host': 'zhidao.baidu.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36'
}
zhihuHeader = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Cookie': "_za=05471db7-d515-4044-8096-4188bff0512d; q_c1=46d067132d7d40c5acc203078bfb37b1|1449197895000|1443867889000; _xsrf=b43db227ff80d0761ee5020124cc7f14; cap_id=\"NGUwNDg4MGNhZGZkNGEwNjg5MzliOTgxNDFhNDE2OTY=|1449734556|07b231f0d966a20b301be1a8eb9d8c24489e80c8\"; __utmt=1; z_c0=\"QUFBQWVsSVpBQUFYQUFBQVlRSlZUZVcta0ZaX21CSnU2Yl9hUl9HRWtaM29nTF9PV2c5WGxnPT0=|1449734629|1d17eebc170e7a06d9d21f30d10563e8702b5128\"; unlock_ticket=\"QUFBQWVsSVpBQUFYQUFBQVlRSlZUZTA0YVZhZHpYYTUyUU56RWt3cVF5T21paHI5am1tbzNRPT0=|1449734629|06266970923fcfc4cd21f6c406aabee6bdf69401\"; __utma=51854390.838701320.1449734556.1449734556.1449734556.1; __utmb=51854390.8.10.1449734556; __utmc=51854390; __utmz=51854390.1449734556.1.1.utmcsr=zhihu.com|utmccn=(referral)|utmcmd=referral|utmcct=/question/38337133; __utmv=51854390.100-1|2=registration_date=20120507=1^3=entry_date=20120507=1",
    'Host': 'www.zhihu.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36'
}
SougouHeader = {
    'Host': 'wenwen.sogou.com',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Referer': 'http://wenwen.sogou.com/',
    'Cookie': 'ww_sTitle=asdfasdfasd; IPLOC=CN1100; SUID=3632C76F2A0B940A0000000057D037D5; ssuid=7628872596; sw_uuid=4682830637; CXID=170CB0E839B528B4844DC9DCD9C95905; ad=hKpMvyllll2g1RKBlllllVKyn3klllllbDth2kllllDlllllxZlll5@@@@@@@@@@; MAIN_SESSIONID=n11j392zpb3l71zt70o0lava50y.n11; ww_orig_ref="http%3A%2F%2Fwenwen.sogou.com%2Fs%2F%3Fw%3Dasdfasdfasd%26search%3D%25E6%2590%259C%25E7%25B4%25A2%25E7%25AD%2594%25E6%25A1%2588%26ch%3Dnewsy.ssda.ynr"',
    'Connection': 'keep-alive'
}


#################################
# functional
def zhprint(obj):
    """
    用于打印中文
    :param obj: unicode 编码的中文
    :return: obj 对应的中文
    """
    import re
    print(re.sub(r"\\u([a-f0-9]{4})", lambda mg: unichr(int(mg.group(1), 16)), obj.__repr__()))


def sub_insertES(content, domain, site, tC, tU, tQ, quote, question, cur_time):
    # dup check
    cur_id = uuid.uuid4().hex
    search_body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match_phrase": {
                            "content.keyword": {
                                "query": content,
                                "slop": 0
                            }
                        }
                    },
                    {
                        "term": {
                            "domain": domain
                        }
                    },
                    {
                        "term": {
                            "site": site
                        }
                    }
                ]  # end must
            }
        }
    }
    res = es.search(index=es_index, doc_type=es_type, body=search_body)
    hits_total = res["hits"]["total"]  # 0 if not found
    hits_max_score = res["hits"]["max_score"]  # None if not found
    hits_list = res["hits"]["hits"]  # [] if not found

    if hits_total == 0:
        index_body = {
            "id": cur_id,
            "tCreated": tC,
            "tUpdate": tU,
            "tQuote": tQ,
            "quote": quote,
            "domain": domain,
            "site": site,
            "question": question,
            "content": content,
        }
        es.index(index=es_index, doc_type=es_type, id=cur_id, body=index_body)
    else:
        update_body = {
            "doc": {
                "tUpdate": cur_time
            }
        }
        for hit in hits_list:
            es.update(index=es_index, doc_type=es_type, id=hit["_id"], body=update_body)


def insertES(content_list, question, cur_time, site, domain):
    """
    :param content_list:
    :param question:
    :param cur_time:  datetime or string "2017-03-09T16:03:42.816385"
    :param site:
    :param domain:
    :return:
    """
    if content_list is None or len(content_list) == 0:
        return False
    quote = 1
    tC = cur_time
    tU = cur_time
    tQ = cur_time

    for content in content_list:
        if content is None:
            continue
        if not isinstance(content, unicode):
            content = content.decode("utf-8")
        try:
            sub_insertES(content, domain, site, tC, tU, tQ, quote, question, cur_time)
        except Exception as e:
            print(e)
            try:
                sub_insertES(content.encode("utf-8"), domain, site, tC, tU, tQ, quote, question, cur_time)
            except Exception as e:
                print(e)
                print("Bad length for ES:", len(content))
                continue
    return True


##################################
# Scraper for Answers
def crawl_baidu(url):
    """
    被 getAnswerfromZhiDao 多线程调用
    :param url:
    :return:
    """
    global zhidaoHeader
    verbose = 0
    Answer = []
    http_obj = httplib2.Http()
    response, tar_page = http_obj.request(url, 'GET', headers=zhidaoHeader)

    # 判断是否做了重定向 301, 302
    if response.previous is not None:
        if response.previous['status'][0] == '3':
            url = response.previous['location']

    # baidu zhidao
    if "zhidao" in url:
        if verbose >= 1:
            print("from zhidao...")
        if len(etree.HTML(tar_page.lower()).xpath("//div[@class='bd answer']/div[@class='line content']")) != 0:
            temp = etree.HTML(tar_page.lower()).xpath("//div[@class='bd answer']/div[@class='line content']")[0]
            c1 = len(etree.HTML(tar_page.lower()).xpath("//div[@class='bd answer']/div[@class='line content']/img")) == 0
            c2 = len(etree.HTML(tar_page.lower()).xpath("//div[@class='bd answer']/div[@class='line content']/pre/img")) == 0
            if c1 and c2:
                for i in temp:
                    Answer.append("".join([x for x in i.itertext()]))
        elif len(etree.HTML(tar_page.lower()).xpath('//*[@class="bd answer answer-first    "]/div/div[2]')) != 0:
            temp = etree.HTML(tar_page.lower()).xpath('//*[@class="bd answer answer-first    "]/div/div[2]')[0]
            if len(etree.HTML(tar_page.lower()).xpath('//*[@class="bd answer answer-first    "]/div/div[2]/img')) == 0:
                for i in temp:
                    Answer.append("".join([x for x in i.itertext()]))
        elif len(etree.HTML(tar_page.lower()).xpath("//div[@class='bd answer  answer-last   ']/div[@class='line']/div[@class='line content']/div[1]/span")) != 0:
            temp = etree.HTML(tar_page.lower()).xpath("//div[@class='bd answer  answer-last   ']/div[@class='line']/div[@class='line content']/div[1]/span")
            if len(etree.HTML(tar_page.lower()).xpath("//div[@class='bd answer  answer-last   ']/div[@class='line']/div[@class='line content']/div[1]/span/img")) == 0:
                for i in temp:
                    Answer.append("".join([x for x in i.itertext()]))
        elif len(etree.HTML(tar_page.lower()).xpath("//div[@class='quality-content-detail content']")) != 0:
            temp = etree.HTML(tar_page.lower()).xpath("//div[@class='quality-content-detail content']")[0]
            if len(etree.HTML(tar_page.lower()).xpath("//div[@class='quality-content-detail content']/img")) == 0:
                Answer += [x for x in temp.itertext()]
        else:
            pass

    # 重定向到百度经验
    elif "jingyan" in url:
        if verbose >= 1:
            print("from jingyan...")
        response, tar_page = http_obj.request(url, 'GET', headers=jingyanHeader)
        if response.previous is not None:
            if response.previous['status'][0] == '3':
                url = response.previous['location']
                response, tar_page = http_obj.request(url, 'GET', headers=jingyanHeader)
        li_list = BeautifulSoup(tar_page).find('div', class_="exp-content format-exp").find('ol', class_="exp-conent-orderlist").find_all('li')
        output = ""
        for li in li_list:
            output += li.get_text()
        Answer.append(output)

    # 重定向到百度百科
    elif "wbk" in url:
        if verbose >= 1:
            print("from baike...")
        output = ""
        response, tar_page = http_obj.request(url, 'GET')
        if response.previous is not None:
            if response.previous['status'][0] == '3':
                url = response.previous['location']
                response, tar_page = http_obj.request(url, 'GET')
            output += BeautifulSoup(tar_page).find('div', class_="summary-content").find('p').get_text()
        Answer.append(output)
    return Answer


def getAnswerfromZhiDao(question, verbose):
    """
    Scrap answers from ZhiDao(百度知道 )
    :param question:
    :return:
    """
    tic = time.time()
    global zhidaoHeader
    URL = ZHIDAO + "/index?rn=10&word=" + question
    http = httplib2.Http()
    # response, content = http.request(URL, 'GET', headers=zhidaoHeader)

    # change cookie
    # 声明一个CookieJar对象实例来保存cookie
    cookie = cookielib.CookieJar()
    # 利用urllib2库的HTTPCookieProcessor对象来创建cookie处理器
    # handler = urllib2.HTTPCookieProcessor(cookie)
    # 通过handler来构建opener
    # opener = urllib2.build_opener(handler)
    # 此处的open方法同urllib2的urlopen方法，也可以传入request
    # response = opener.open(URL)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    req = urllib2.Request(URL)
    response = opener.open(req)
    zhidaoHeader['Cookie'] = response.headers.dict['set-cookie']

    try:
        response, content = http.request(URL, 'GET', headers=zhidaoHeader)
    except Exception as e:
        print(e)
        response, content = http.request(URL.decode("utf-8"), 'GET', headers=zhidaoHeader)

    search_result_list = etree.HTML(content.lower()).xpath("//div[@class='slist']/p/a")
    limit_num = 3
    urls = []
    for index in range(min(len(search_result_list), limit_num)):
        url = search_result_list[index].attrib['href']
        if "http://" not in url:
            url = ZHIDAO + url
        urls.append(url)

    pool = ThreadPool(3)
    results = pool.map(crawl_baidu, urls)
    pool.close()
    pool.join()

    Answer = []
    for i in results:
        Answer += i
    del results

    toc = time.time()
    if verbose >= 1:
        print("Elapse ZhiDao: ", toc - tic, "s")

    Answer = check_sentence_last(Answer)
    if len(Answer) < 1:
        return None
    else:
        return Answer


def get_ans_from_zd_webdriver(question):
    """
    从百度知道上面获取答案，采用模拟浏览器的方式
    :param question:
    :return:
    """
    global zhidaoHeader
    global ZHIDAO

    # invisualble
    # display = Display(visible=0, size=(800, 600))
    # display.start()

    url_q_list = ZHIDAO + "/index?rn=10&word=" + question
    driver = webdriver.Firefox()
    driver.get(url_q_list)
    content = driver.find_element_by_xpath('/html/body/div[3]/p[1]/a')

    return None


def getAnswerfromZhiHu(question, verbose):
    """
    Scrap answers from ZhiHu(知乎)
    :param question:
    :return:
    """
    global zhihuHeader
    tic = time.time()
    # search?type = content & q = 你懂不懂
    URL = ZHIHU + '/search?type=content&q=' + question
    Answer = []
    urlList = []
    http = httplib2.Http(".cache", disable_ssl_certificate_validation=True)

    try:
        response, content = http.request(URL, 'GET', headers=zhihuHeader)
    except Exception as e:
        print(e)
        response, content = http.request(URL.decode("utf-8"), 'GET', headers=zhihuHeader)

    hrefs = etree.HTML(content.lower()).xpath("//div[@class='title']/a")
    for i in hrefs:
        urlList.append(ZHIHU + i.attrib['href'])
    if len(urlList) < 3:
        return None

    # 找到“赞同数”最多的回复的index
    for i in range(0, 3):
        if "zhuanlan" not in urlList[i]:
            response, answerPage = http.request(urlList[i], 'GET')
            answerContent = etree.HTML(answerPage.lower()).xpath("//div[@class='zm-item-answer  zm-item-expanded']")
            if answerContent is None or len(answerContent) == 0:
                text_list = etree.HTML(answerPage).xpath("//div[@class='List-item']/div/div[@class='RichContent RichContent--unescapable']/div[@class='RichContent-inner']/span")
                if text_list is None or len(text_list) == 0:
                    continue
                # 知乎回答中的答案就是按照点赞数来排序的
                insert_text = text_list[0].text
                if insert_text is None or len(insert_text) == 0:
                    continue
                Answer.append(insert_text)
            else:
                flag = 0
                location = 0
                t = 0
                for j in answerContent[0].xpath("//span[@class='count']"):
                    t += 1
                    # 这里是为了取知乎中赞同数两最多的结果，因为会出现21k等表示数字的方式，故需要作出判断
                    num_str = j.text
                    if 'k' in num_str:
                        num_str = num_str.replace("k", "000")
                    elif 'm' in num_str:
                        num_str = num_str.replace('m', "000000")
                    else:
                        pass
                    count = int(num_str)
                    if count > flag:
                        flag = count
                        a = count
                        location = t-1

                # 提取标签中的文本, change by zw
                flag = 1
                if len(answerContent[0].xpath("//div[@class='zm-item-rich-text js-collapse-body']")) != 0:
                    for j in answerContent[0].xpath("//div[@class='zm-item-rich-text js-collapse-body']")[location]:
                        if flag % 2 == 0:
                            Answer.append("".join([x for x in j.itertext()]))
                        flag += 1
                elif len(answerContent[0].xpath("//div[@class='zm-item-rich-text expandable js-collapse-body']")) != 0:
                    for j in answerContent[0].xpath("//div[@class='zm-item-rich-text expandable js-collapse-body']")[location]:
                        if flag % 2 == 0:
                            Answer.append("".join([x for x in j.itertext()]))
                        flag += 1
                else:
                    continue

    toc = time.time()
    if verbose >= 1:
        print("Elapse ZhiHu: ", toc - tic, "s")
    Answer = check_sentence_last(Answer)
    if len(Answer) < 1:     # 如果答案过少，过！
        return None
    else:
        return Answer


def getAnswerfromSoGou(question, verbose):
    """

    :param question:
    :return:
    """
    global SougouHeader
    tic = time.time()
    Answer = []
    URL = SOUGOU + "/s/?w=" + question + "&search=搜索答案"
    http = httplib2.Http()

    try:
        response, content = http.request(URL, 'GET', headers=SougouHeader)
    except Exception as e:
        print(e)
        response, content = http.request(URL.decode("utf-8"), 'GET', headers=SougouHeader)

    searchPage = etree.HTML(content.lower().decode('utf-8')).xpath('//*[@id="result_list"]/div[@class="result-item"]/h3/a')
    if searchPage is not None:
        for i in searchPage[0:3]:
            url = SOUGOU + i.attrib['href']
            response, content = http.request(url, 'GET', headers=SougouHeader)
            # 判断是否做了重定向 301, 302
            if response.previous is not None:
                if response.previous['status'][0] == '3':
                    temp_header = {
                        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.84 Safari/537.36",
                        'Cookie': 'CXID=D6E7E80282DBEB623CC0BD1DBF2FB702; SUV=00E102DA7B740088577877A0ED6FB758; sw_uuid=8285128663; ssuid=1156870255; IPLOC=CN1100; ww_orig_ref="http%3A%2F%2Fwenwen.sogou.com%2F%2Fs%2F%3Fw%3D%25E7%2594%25B7%25E6%259C%258B%25E5%258F%258B"; pid=ask.smb; SNUID=081F4942383D00E5E37D23D539E2D1C9; ld=HZllllllll2gX2QvlllllVWtCB6lllllWT9uGyllllwlllll4klll5@@@@@@@@@@; LSTMV=721%2C221; LCLKINT=7472; ad=LnizVlllll2gzTMRlllllVWtCz7lllll5FJMhkllllklllll4klll5@@@@@@@@@@; SUID=CA7E323D4B6C860A576B7F830003A587; ss_pidf=1'
                    }
                    url = response.previous['location']
                    response, content = http.request(url, 'GET', headers=temp_header)
                    # 略懂社，无法正常爬取，后期还未做处理

            text = []
            # text += etree.HTML(content.lower().decode('utf-8')).xpath('//div[@class="main"]/div[@class="section "]/div[@class="replay-wrap common_answers"]/div[@class="replay-section answer_item "]/div[@class="replay-info"]/pre/table/tbody/tr/td/text()')
            text += etree.HTML(content.lower().decode('utf-8')).xpath('//div[@class="main"]/div[@class="section "]/div[@class="replay-wrap common_answers"]/div[@class="replay-section answer_item "]/div[@class="replay-info"]/pre/p/text()')
            text += etree.HTML(content.lower().decode('utf-8')).xpath('//div[@class="main"]/div[@class="section "]/div[@class="replay-wrap common_answers"]/div[@class="replay-section answer_item "]/div[@class="replay-info"]/pre/text()')
            Answer.append("\n".join(text))
    else:
        toc = time.time()
        if verbose >= 1:
            print("Elapse SoGou: ", toc - tic, "s")
        return None

    toc = time.time()
    if verbose >= 1:
        print("Elapse SoGou: ", toc - tic, "s")

    Answer = check_sentence_last(Answer)
    if len(Answer) < 1:
        return None
    return Answer


def check_sentence_last(Answer):
    max_single_length = 2000
    temp = []
    for i in Answer:
        i = i.strip('\n').strip('\t').strip(' ')
        # if u'评论' in i or u'分享' in i:
        #     continue
        if len(i) == 0:
            continue
        if len(i) > max_single_length:
            for ii in i.split("\n"):
                temp_ii = ii[:max_single_length].strip()
                if len(temp_ii) == 0:
                    continue
                temp.append(temp_ii)
        temp.append(i)
    return temp


#######################################
# Threads
class SeThreads(threading.Thread):
    def __init__(self, threadID, name, question, verbose):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.question = question
        self.verbose = verbose

    def run(self):
        """
        把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        :return:
        """
        global SoGou_ske
        global ZhiDao_ske
        global ZhiHu_ske
        if self.name == "Thread-sogou":
            try:
                SoGou_ske = getAnswerfromSoGou(self.question, self.verbose)
            except Exception as e:
                SoGou_ske = None
                print("SoGou: ", e)
        elif self.name == "Thread-zhidao":
            try:
                ZhiDao_ske = getAnswerfromZhiDao(self.question, self.verbose)
                # ZhiDao_ske = get_ans_from_zd_webdriver(self.question)
            except Exception as e:
                ZhiDao_ske = None
                print("zhidao: ", e)
        elif self.name == "Thread-zhihu":
            try:
                ZhiHu_ske = getAnswerfromZhiHu(self.question, self.verbose)
            except Exception as e:
                ZhiHu_ske = None
                print("ZhiHu: ", e)


######################################
# Main function
def fromSE(q, verbose=0, insert=True):
    tic = time.time()
    global SoGou_ske
    global ZhiDao_ske
    global ZhiHu_ske

    _ver = sys.version_info
    is_py2 = (_ver[0] == 2)  # Python 2.x?
    is_py3 = (_ver[0] == 3)  # Python 3.x?

    if isinstance(q, unicode):
        if is_py3:
            question = urllib.quote(q)
        elif is_py2:
            question = urllib.quote(q.encode('utf-8'))
        else:
            raise
    else:
        question = q

    sgThreads = SeThreads(4, "Thread-sogou", question, verbose)
    zdThreads = SeThreads(2, "Thread-zhidao", question, verbose)
    zhThreads = SeThreads(1, "Thread-zhihu", question, verbose)

    threads = []
    sgThreads.start()
    zdThreads.start()
    zhThreads.start()

    threads.append(sgThreads)
    threads.append(zdThreads)
    threads.append(zhThreads)

    for t in threads:
        t.join()

    if verbose >= 2:
        print("===========")
        print("搜狗:")
        if SoGou_ske is None:
            print("None")
        else:
            for i, c in enumerate(SoGou_ske):
                print(str(i) + "-->" + c.encode("utf-8"))

        print("===========")
        print("知道:")
        if ZhiDao_ske is None:
            print("None")
        else:
            for i, c in enumerate(ZhiDao_ske):
                print(str(i) + "-->" + c.encode("utf-8"))

        print("===========")
        print("知乎:")
        if ZhiHu_ske is None:
            print("None")
        else:
            for i, c in enumerate(ZhiHu_ske):
                print(str(i) + "-->" + c.encode("utf-8"))
        print("===========")
    toc = time.time()
    if verbose >= 1:
        print("Searching got %s s" % (toc - tic))

    nest_output = []
    if SoGou_ske is not None and (len(SoGou_ske) != 0):
        nest_output.append(SoGou_ske)
    if ZhiDao_ske is not None and (len(ZhiDao_ske) != 0):
        nest_output.append(ZhiDao_ske)
    if ZhiHu_ske is not None and (len(ZhiHu_ske) != 0):
        nest_output.append(ZhiHu_ske)

    # insert ES
    domain_name = "normal"
    cur_time = datetime.now()
    if insert:
        print("Index to Elasticsearch...")
        insertES(content_list=SoGou_ske, question=q, cur_time=cur_time, site="sogou", domain=domain_name)
        insertES(content_list=ZhiDao_ske, question=q, cur_time=cur_time, site="zhidao", domain=domain_name)
        insertES(content_list=ZhiHu_ske, question=q, cur_time=cur_time, site="zhihu", domain=domain_name)
    if verbose >= 1:
        print("fromSE completed !")
    return nest_output


def test():
    # a = ''
    # b = '一九九七年七月一日既是中萢人民共和國香港特別行政 區一個新紀元的開始 ，也標読着156年英國管治的絢統。香 港巿民一同見譪了這個歷史時刻，人人引以自豪，全港洋溢 着歡欣的氣氛。六月三十日，當午夜即將來舝，莊嚴而得體 的政權交接儀式開始舉行，揭開了香港歷史新的一頁。交接 儀式在晚上十一時三十分開始，在香港會議展覽中心新翼前 廳舉行，中英兩國都派出了儀仗隊和軍樂隊，國家主席江澤 民和查理斯王子分別致辭。在即將踏入午夜的時候，英國和 香港的旗幟徐徐降下；午夜十二時正，中國國旗和香港特別 行政區區旗升起。交接儀式在 4 000位應邀出席的嘉賓見譪 下適行，其中有中國和英國的高層代表 、 40多個國家的部 閘和40 多個國雋絤織的代表。香港政府的高級官唗、來自 各層面的本地和海外商界與社區頸袖也有出席。約 6 500位 本地與海外的傳媒代表在琭場報道儀式的盛況，乲傳送給全 世界數以億計的電視觀眾。 七月一日凌晨一時三十分，副 總理鍃其琛主持就職儀 式。在儀式中，國家主席江澤民向在座 4 000多名嘉賓正式 宣布中萢人民共和國香港特別行政區成立。行政閘官、主要 官唗、行政會議成唗、舝時立法會議唗、絢審法院和高等法 院法官等宣誓就職。總理李鵬和行政閘官董建萢先後致辭。 儀式完畢後，舝時立法會雜即舉行在香港特別行政區的第一 次會議，制定《香港回歸條例》。 七月一日上午十時，特別行政區成立慶典在香港會議展 覽中心新翼舉行，應邀出席的嘉賓逾 4 600名。首先由國家 主席江澤民發表重要講話，重申 "一國兩制" 、"港人治港" 和"高度自治"將緎持 50 年不變 。繼由行政閘官發表就職 演辭。儀式中，土地基金的賧產移交給香港特別行政區政 府，中央人民政府和 31 個省、自治區和直轄市也給香港特 別行政區致送秠物。儀式統束後，還有盛大的文藝表演，其 中一項演出節目是世界首演的交響曲1997《天地人》。 七月一日下午四時，香港會議展覽中心新翼再度熱鬧起 來，約 5 000名各國顯要和中外賔賓出席特別行政區政府招 待酒會，冠蓋雲集。 除官方儀式外，香港本地坒體和社區絤織也舉行各式各 樣的慶祝活動，多不勝數，其中包括煙花卹演、電視綾合表 演、海港花艇燈飾巡遊、文藝表演和各式宴會。城中每一個 角落均洋溢着歡欣和節日的氣氛。 六月三十日也舉行了一些儀式，標読156 年英國管治的 絢統。當天下午四時三十分，前總督府舉行了香港最後一任 總督彭定康告別其官邸的簡單儀式。 添駌艦的告別儀式在特為該活動而建造的場地上舉行， 查理斯王子和總督彭定康在儀式上先後致辭。日落時份，英 國和香港的旗幟徐徐降下。 六月三十日的英國告別晚宴，由英國外交及聯邦事務大 臣郭偉邦宴請，有 4 000位顯要和賔賓參加。英國外相郭偉 邦為香港的未來祝酒，副總理兼外閘鍃其琛繼而祝酒答謝。 六月三十日，509 名先遣士兵由熊自仁少將率頸，在晚 上九時適入香港。中英兩國的軍隊在威爾斯觝王軍爄舉行了 一個防務責任交接儀式。七月一日零時，所有軍爄均舉行升 旗儀式，象徵着防務責任正式移交香港駐軍。七月一日上午 六時，由海、陸、空三軍部隊絤成的駐軍主體部隊適駐香港 的14 個軍爄。'
    # c = ['\n谢谢邀请。我因为家里离香港很近的缘故，一年总要有两次去香港。在我看来，香港回归15年，褒贬不一，现在的官媒、“档”媒给出的种种粉饰太平的艳文，不足以说明香港回归之后的现状。请注意，“粉饰太平”在这里并不是指香港已经陷入种种不好的状态，只是在表示这些媒体一贯的做法。在我看来，15年来香港被大陆改变很多。香港的免税环境，让大陆人找到了一个在经济上的宣泄口。当然，如果没有香港这个自由港，也不会看到大陆人在香港像买白菜一样买几十台iphone 4同时还开单位发票。但更多的个人在香港能够买到很多符合自己经济条件的产品，这在极大地促进了香港贸易的同时，也让大陆海关红了眼。15年来，香港作为真正的国际时尚之都，把时尚的概念和实质带到了大陆。时尚当中的一部分特质——奢侈品，也真正在大陆流行起来。以前“吃肯德基是时尚”这种太过蒙昧的观点，早已被冲刷得一干二净，某种程度上也要归咎于香港的贡献。香港的另一贡献就是真正的“时尚经济”曝光了更多在港消费公款的大陆执政官员，让大陆的廉政建设不得不提速。尽管这是party很不愿意的提速，但是在网络社会下，只要一个人的行为和其他人相关联，总有被曝光的时候。第三，私以为香港为大陆人提供了一个透视现代教育先进性的窗口。当越来越多的高考状元选择香港的大学，这让大陆的教育体系受到足够有影响的冲击。因为高考生基本上是完全民事行为能力人，有独立思考的能力，有正常的“三观”，他们对于先进教育和更为广博的知识结构的渴望，在一次又一次地抽打着大陆教育当局的脸。当然，大陆的教育体制也在改变，但改变得实在很有限。所以个人觉得香港在这方面还是做得很不错的。香港变坏了吗？我觉得大处没有。首先，是香港人和内地人的矛盾——这是香港民主、民意、民权、民生的体现，这恰恰说明了香港人有权为自己争取一些什么。我们其实可以看到，香港的底层市民生活依然艰辛，香港的执政派喊出的口号，也没有能够惠及所有人。这是香港政治在口号与执行方面的缺陷，用一句大陆很流行的、善于为自己开脱的话来说，“这样的矛盾必将长期存在”（不禁感到一阵心酸）。不过我也看到了，香港政府重启“居屋”项目（也就是大陆所说的经济适用房），并且带着很大的决心要惠泽黎民，这种不论谁上台都必须当做头等大事来抓的连续性和勇气，恰恰有如台湾省当局大刀阔斧的执政方式改革一样，值得大陆重视和反思。重启居屋项目，是当局对之前房地产政策的一种变相的承认错误。目前香港的房地产已经无法实现软着陆，任谁都明白这一点，所以香港当局花了很大的力气来抓居屋，同时带来的就是交通运输成本、社区综合建设成本的大幅提高。这些钱从哪来？“香港自己解决”（前任香港特首曾荫权语）梁振英：民生问题对政府来说是重大问题，香港的民生问题，一个是住房问题，香港房价比较高，租金比较高，过去八年房子落成量一直下滑，造成比较突出的供需矛盾。一方面我们要维持楼价的稳定，另一方面要该适当增加土地供应量，调节房地产市场。第二个方面医疗和老龄化的问题，这两方面都是民生问题中比较突出的。原文链接：梁振英：香港出生即成永久居民不是基本法原意其次，香港目前政策上的开放，导致了资源愈发稀缺，很多人开始担心香港未来的发展能力。从资本经济上来说，这一点不成问题；从教育、居住和活动面积、公共交通、水电、饮食等方面来看，的确如此。也正因如此，香港人的忧虑倍增。但是这个问题的解决方式并不在香港自身，而在大陆。如果说香港真的有变坏的地方，我自己至今能看见的，一个是香港的城市污染太严重了。每天要承受15年前200倍甚至500倍的观光人口，香港的治污能力早已羸弱不堪。另一个是香港市民的自信、观察问题的方式正在遭受严重的打击。这些恰恰是我们“大陆人”带来的。一个真正是政治清平的国家，你看不到有人一次性去买35台iphone 4和42台ipad 2还开的是对公增值税发票，也看不到有人在海港城爱马仕一口气买18个包送领导和关系，而且这些话还是在爱马仕的店门口破锣大嗓、旁若无人地对着自己的老婆说的。题外：用一句“台巴子”（这里把台湾人说成“台巴子”，是带有浓重反讽的意味，而不是蔑称，请观者勿对号入座）说的话“没错，台湾岛也有很多穷人，但是我们的‘马总统’连拉票都要去问这些穷人，我们相信在真正的民主下，现在的‘马总统’和以后的‘驴总统’都会重视这个问题，让穷人不再穷。但是反过来，在xxxxx，我觉得根本看不到希望。”这里的xxxxx是哪里，大家自行想象吧。我注意到这个问题有一个标签是“香港电影”，其实香港“变坏了”的地方并不包括香港电影。对香港电影来说，没落和失去吸引力是非常正常的。受限于地域、文化、社会结构、从业人员素质的因素，香港电影自娱自乐影响几代人的时代已经过去了。接下来要进入的是一个黑暗的低潮期，这个低潮期，香港电影和大陆电影将共享之，持续起码十年。++++++++++++++写在最后的分割线++++++++++++++++++++++++++今天，7月3日，看到问题为什么那么多的香港人反对梁振英？之后，我觉得关于本答案当中的港首梁振英的话，我太过于信任他的发言，也太过于信任他在这个政策上的执行力了。就这一点，我必须承认我在政治上很幼稚。犯了非常恶心的错误。在此，仅因为这一点，向各位知友表示歉意。\n\n', '\n转自互联网      要让中国国旗准时升起，仅仅得到英方的同意远远不够。筹备人员还要在实际操作时，把所有活动需要的时间提前算好，精确到秒，连仪仗队每一步走多远都要计算好，不能有丝毫误差。安文彬为此专门从美国买了一块相当精确的手表，与伦敦格林尼治天文台和南京紫金山天文台对好了时间。他还让两个司仪专门掌控时间，设立了礼宾总协调和中方技术监控人，严格掌握时间。而军乐团的两名副指挥，用读秒的方式掌握国歌响起时间。然而，到仪式进行时，还是出现了一点小意外。当时本来给查尔斯王子的讲话时间是6分钟，但他讲了6分23秒。为了抢回这23秒，现场指挥安文彬命令随后的活动加紧进行，司仪讲话速度加快，仪仗队加快步伐，终于把时间赶回来了，还多争取了一秒。再往后，英国旗帜于59分23秒开始降下，最后是59分53秒完全降下，我方多出了7秒时间。    但我方不能违反协议。为了控制时间，安文彬站在乐队指挥旁边读秒，一直到58秒时，才让指挥抬起指挥棒，这中间有将近5秒的“真空”时间，很多人都奇怪，以为当时技术上出了什么问题。当时的《人民日报》文章也提到，英国国旗徐徐降下，“这时，距零点只差几秒，全场一片肃穆”。当时他们肯定不知道，这是为了保证国旗百分之百精确地于1日零时零分零秒在香港上空升起。\n\n', '\n淘寶包郵…？\n\n']

    q = u"唐太宗是谁"
    print(q.encode('utf8'))

    # 返回一个装满答案的列表，分别对应 SoGou_ske, ZhiDao_ske, ZhiHu_ske
    # 每个答案都是一个列表 [答案1, 答案2, ...]
    ans = fromSE(q)
    label = [u"搜狗", u"知道", u"知乎"]
    cnt = 0
    for i in ans:
        print("============= Answer from ", label[cnt], " =============")
        cnt += 1
        if i is None:
            print("None")
        else:
            for j in i:
                print("-----")
                print(j)


if __name__ == "__main__":
    test()


