# -*- coding: utf-8 -*-
import datetime as dt
from datetime import timedelta
import numpy as np
import pandas as pd
import os

class Extract_Features:
    '''
    # classifier's features X:
          weekday:[1:7]
          lunar_month:[1:12]
          season:[1:4]
          comment's sentiment: SnowNLP, based on short text classifier's result
          economical environment : cpi, gdp_year, gdp_quarter,  money_supply
    # label Y: actual trends
          0: increase
        #? 1: keep
          2: decrease
    '''

    def __init__(self):
        pass

    def parse_weekday(self, date):
        '''
        :param date:date
        :return: weekday
        '''
        if type(date) is str:
            date = dt.datetime.strptime(date, '%Y-%m-%d')
            return date.isoweekday()
        elif type(date) is dt.date or type(date) is dt.datetime:
            return date.isoweekday()
        else:
            raise TypeError('date must be datetime type!')

    def lunar_month(self, date):
        '''
        :param date:date
        :return: lunar month
        '''
        from lunar import Lunar
        #date = str(date.year)+'-'+str(date.month)+'-'+str(date.day)
        date = dt.datetime.strptime(date, '%Y-%m-%d')
        ln = Lunar(date)
        lunar_date = ln.ln_date()
        return lunar_date[1]

    def season(self, date):
        '''
        :param date:date
        :return: season
        '''
        dict = {1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3, 9: 3, 10: 4, 11: 4, 12: 4}
        if type(date) is dt.datetime or type(date) is dt.date:
            return dict[date.month]
        elif type(date) is str:
            return dict[int(date.split('-')[1])]

    def cpi(self, date):
        '''

        :param date: date
        :return: cpi
        '''
        data = open('./data/cpi.csv', 'rb').readlines()[1:]
        cpi = {}
        for line in data:
            item = line.split(',')
            cpi_dates = '-'.join(item[1].split('.'))
            cpi_datas = float(item[2])
            cpi[cpi_dates] = cpi_datas

        if type(date) is dt.datetime or type(date) is dt.date:
            return cpi[str(date.year)+"-"+str(date.month)]
        elif type(date) is str:
            return cpi[date.split('-')[0]+'-'+str(int(date.split('-')[1]))]

    def get_price_chage(self, date):
        '''

        :param date: date
        :return: delta price
        '''
        #date = dt.datetime.strptime(date, '%Y-%m-%d')
        data = pd.read_csv('sz.csv', index_col='date')
        delta = data['price_change']
        #return delta[str(date.year)+'-'+str(date.month)+'-'+str(date.day)]
        return delta[date]

    def get_sz_close_price(self, date):
        '''
        :param date:
        :return:shenzhen close price
        '''
        data = pd.read_csv('sz.csv', index_col='date')
        delta = data['close']
        #return delta[str(date.year)+'-'+str(date.month)+'-'+str(date.day)]
        return delta[date]

    def gdp_year(self, date):
        data = pd.read_csv('./data/gdp_year.csv', index_col='year')
        gdp_year_data = data['gdp']
        if type(date) is dt.datetime or type(date) is dt.date:
            return gdp_year_data[date.year]
        elif type(date) is str:
            return gdp_year_data[int(date.split('-')[0])]
        else:
            raise TypeError("type of date must be string or datetime.date or datetime.datetime!")

    def gdp_quarter(self, date):
        data = pd.read_csv('./data/gdp_quarter.csv', index_col='quarter')
        gdp_year_data = data['gdp']
        if type(date) is dt.date or type(date) is dt.datetime:
            date_for_quarter = date.year + self.season(date)/10.0
            return gdp_year_data[date_for_quarter]
        elif type(date) is str:
            return gdp_year_data[int(date.split('-')[0]) + self.season(date)/10.0]
        else:
            raise TypeError("type of date must be string or datetime.date or datetime.datetime!")

    def rrr(self, date):
        data = pd.read_csv('./data/rrr.csv', index_col='date')
        rrr_data = data['now']
        rrr_data.index = pd.to_datetime(rrr_data.index)
        # date compare...
        if type(date) is str:
            date = dt.datetime.strptime(date, '%Y-%m-%d')
        return rrr_data.loc[rrr_data.index < date][0]

    def MoneySupply(self, date):
        # return last month's data
        data = open('./data/money_supply.csv', 'rb').readlines()[1:]
        money_supply = {}
        for line in data:
            item = line.split(',')
            money_supply_dates = '-'.join(item[1].split('.'))
            if item[2] == '--':
                continue
            money_supply[money_supply_dates] = float(item[2])

        if type(date) is dt.datetime or type(date) is dt.date:
            if date.month > 1:
                return money_supply[str(date.year) + "-" + str(date.month-1)]
            elif date.month == 1:
                return money_supply[str(date.year-1) + "-" + str(12)]
            else:
                raise "date.month error!"

        elif type(date) is str:
            if int(date.split('-')[1]) > 1:
                if str(date.split('-')[0]) + '-' + str(int(date.split('-')[1])-1) in money_supply.keys():
                    return money_supply[str(date.split('-')[0]) + '-' + str(int(date.split('-')[1])-1)]
                else:
                    if int(date.split('-')[1]) > 2:
                        return money_supply[str(date.split('-')[0]) + '-' + str(int(date.split('-')[1]) - 2)]
                    if int(date.split('-')[1]) == 1:
                        return money_supply[str(int(date.split('-')[0]) - 1) + '-12']
            elif int(date.split('-')[1]) == 1:
                return money_supply[str(int(date.split('-')[0])-1) + '-12']
            else:
                raise "date.month error!"

    def short_text_classification(self, date):
        # no used
        print date
        from snownlp import SnowNLP
        # TODO:throw into init()
        with open('news600841.txt', 'rb') as f:
            data = []
            data = f.readlines()
            print type(data)

        corpus = []
        item = []
        for i in range(1, len(data) - 1):
            if (i - 1) % 5 == 0:
                continue
            elif (i - 1) % 5 == 1:
                item.append(data[i].rstrip())
            elif (i - 1) % 5 == 2:
                item.append(data[i].rstrip())
            elif (i - 1) % 5 == 3:
                item.append(data[i].rstrip())
            elif (i - 1) % 5 == 4:
                # print item
                corpus.append(item)
                item = []
                continue

        average_sentiment = 0
        sum_sentiment = 0
        temp_date = ""
        count = 1
        summary_dict = {}
        summary_flag = False
        # TODO!
        for i in range(0, len(corpus)):
            # sentiment analysis,result is not very well
            s = SnowNLP(corpus[i][1].decode('utf-8'))
            sentiment = s.sentiments
            # one to many mapping
            summary_dict.setdefault(corpus[i][0], []).append(sentiment)
            # print s.sentiments,":",corpus[i][0],corpus[i][1]
        for key in summary_dict:
            print key, ":",
            for i in summary_dict[key]:
                print i,
            print ''

    def class_feature(self, date):
        feature = []
        feature.append(self.parse_weekday(date))
        feature.append(self.lunar_month(date))
        feature.append(self.season(date))
        feature.append(self.short_text_classification(date))
        return feature

    def trends(self, code, date):
        if type(date) is str:
            date = dt.datetime.strptime(date, '%Y-%m-%d')
        data = pd.read_csv(str(code)+'.csv', index_col='date')
        close_price_trend = data['close']
        subday = date+timedelta(days=-1)
        print type(close_price_trend), subday.year, subday.month, subday.day
        today = close_price_trend[str(date.year)+'-'+str(date.month)+'-'+str(date.day)]
        while str(subday.year)+'-'+str(subday.month)+'-'+str(subday.day) not in close_price_trend.index:
            subday = subday + timedelta(days=-1)

        yesterday = close_price_trend[str(subday.year)+'-'+str(subday.month)+'-'+str(subday.day)]

        if today > yesterday:
            return 1
        else:
            return 0

    def ML_XY(self):
        # TODO, no use
        X_temp = self.class_feature(None)
        X = []
        y = []
        return np.array(X), np.array(y)

    def classification(feature):
        # TODO, no use
        label = None
        return label

    def test(self, date):
        print "date = ", date

        weekday = self.parse_weekday(date)
        print "weekday = ", weekday
        lunar_months = self.lunar_month(date)
        print 'lunar month = ', lunar_months
        season = self.season(date)
        print "season = ", season
        '''
        cpi_data = ef.cpi(date)
        print "cpi_data = ", cpi_data
        gdp_year = ef.gdp_year(date)
        print "gdp_year = ", gdp_year
        gdp_quarter = ef.gdp_quarter(date)
        print "gdp_quarter = ", gdp_quarter

        trend = ef.trends(600841, date)
        print "trends =", trend
        '''
        close = self.get_sz_close_price(date)
        print "close = ", close
        delta = self.get_price_chage(date)
        print "delta = ", delta
        print self.cpi('2016-7-3')
        rrr_d = self.rrr(date)
        print "rrr = ", rrr_d
        moneySupply = self.MoneySupply(date)
        print "moneySupply = ", moneySupply
