# -*- coding:utf-8 -*-
# instructions: this file tries to use xgboost to solve the problem od prediction via the idea of regression
import matplotlib.pyplot as plt
import os
import datetime as dt
import pandas as pd
from data_preprocess.load_data import *
from sklearn import cross_validation
from algorithum.rmse import *
import xgboost as xgb
from sklearn import preprocessing

path = './data/stock_data/'
code = 600300

dates = []
oneDayLine = []
thirtyDayLine = []
month_dates = []

if os.path.isfile(path + str(code) + '.csv'):
    pass
else:
    download_from_tushare(code)

oneDayLine, dates = load_data_from_tushare(path + str(code) + '.csv')
thirtyDayLine, month_dates = load_data_from_tushare(path + str(code) + '_month.csv')

'''
~~~~~ for idea one ~~~~~~   X is 5 onedayline and 1 thirtydayline with close price
'''
# one dayline time series
X_one = []
y_one = []
daynum = 7
for i in range(0, len(oneDayLine)-daynum+1):
    dat = dates[i].split('-')
    for k, word in enumerate(month_dates):
        if word.startswith(dat[0] + '-' + dat[1]):
            index = k
    X_one.append(thirtyDayLine[k:k+1] + oneDayLine[i:i+daynum])
    if (i+daynum) < len(oneDayLine):
        y_one.append(oneDayLine[i+daynum])
    else:
        y_one.append(0)

X_one = np.array(X_one)
y_one = np.array(y_one)

'''
~~~~~ for idea three ~~~~~~   X is 5 onedayline with all items
'''
X3_one = []
y3_one = []

all_items_day, dates_onedayline = load_all_item_from_tushare(path + str(code) + '.csv')
all_items_month, dates_thirty = load_all_item_from_tushare(path + str(code) + '_month.csv')
for day in range(0, len(all_items_day)-daynum+1):
    dat = dates[day].split('-')
    for k, word in enumerate(month_dates):
        if word.startswith(dat[0]+'-'+dat[1]):
            index = k
    X3_one.append(thirtyDayLine[k:k+1]+[float(c) for c in sum(all_items_day[day:day+daynum], [])])
    if (day+daynum) < len(oneDayLine):
        y3_one.append(all_items_day[day+daynum][2])
    else:
        y3_one.append(0)

X3_one = np.array(X3_one)
y3_one = [float(y3) for y3 in y3_one]
y3_one = np.array(y3_one)

X1_train, X1_test, y1_train, y1_test = create_Xt_Yt(X_one, y_one, 0.8)
X3_train, X3_test, y3_train, y3_test = create_Xt_Yt(X3_one, y3_one, 0.8)

X_dtrain, X_deval, y_dtrain, y_deval = cross_validation.train_test_split(X3_train, y3_train, random_state=1026, test_size=0.3)
d3train = xgb.DMatrix(X_dtrain, y_dtrain)
d3test = xgb.DMatrix(X_deval, y_deval)
watchlist = [(d3test, 'eval')]
params = {
    'booster': 'gbtree',
    'objective': 'reg:linear',
    'subsample': 0.5,
    'colsample_bytree': 0.25,
    'eta': 0.005,
    'max_depth': 5,
    'seed': 1000,
    'silent': 0,
    'eval_metric': 'rmse'
}
rgs = xgb.train(params, d3train, num_boost_round=1000, evals=watchlist)
pred = rgs.predict(xgb.DMatrix(X3_test))

gbm = xgb.XGBClassifier(max_depth=10, n_estimators=400, learning_rate=0.05).fit(X1_train, y1_train)
predicts = gbm.predict(X1_test)

gbm3 = xgb.XGBRegressor(max_depth=5, n_estimators=40000, learning_rate=0.001).fit(X3_train, y3_train)
predicts3 = gbm3.predict(X3_test)

true1_count = 0
false1_count = 0
print ''
print "~~~~~~~~~~ feature 1 ~~~~~~~~~~"
for i in range(1, len(X1_test)-1):
    if ((predicts[i]-y1_test[i-1]) >= 0) != ((y1_test[i]-y1_test[i-1]) >= 0):
        print '\033[91m'+str((predicts[i]-y1_test[i-1]) >= 0)+'\033[0m', (y1_test[i]-y1_test[i-1]) >= 0
        false1_count += 1
    else:
        print (predicts[i]-y1_test[i-1]) >= 0, (y1_test[i]-y1_test[i-1]) >= 0
        true1_count += 1
    print X1_test[i:i+1], predicts[i], y1_test[i], y1_test[i-1]
print ''
print X1_test[len(X1_test)-1:len(X1_test)], y1_test[len(X1_test)-1]
print gbm.predict(X1_test[len(X1_test)-1:len(X1_test)])-y1_test[len(X1_test)-2] >= 0
print ""

true2_count = 0
false2_count = 0
print "~~~~~~~~~~~~~model 2~~~~~~~~~~~~~~~"
for i in range(1, len(X3_test)-1):
    if ((pred[i]-pred[i-1]) >= 0) != ((y3_test[i]-y3_test[i-1]) >= 0):
        print '\033[91m'+str((pred[i]-pred[i-1]) >= 0)+'\033[0m', (y3_test[i]-y3_test[i-1]) >= 0
        false2_count += 1
    else:
        print (predicts[i]-pred[i-1]) >= 0, (y3_test[i]-y3_test[i-1]) >= 0
        true2_count += 1

print ''
print "true2_count = ", true2_count, "false2_count = ", false2_count, "len(X3_test) = ", len(X3_test)-2
print X3_test[len(X3_test)-1:len(X3_test)], y3_test[len(X3_test)-1]
print rgs.predict(xgb.DMatrix(X3_test[len(X3_test)-1:len(X3_test)]))-y3_test[len(X3_test)-2] >= 0
print "~~~~~~~~~~~~~~~~~~~~"

false3_count = 0
true3_count = 0
print ''
print "~~~~~~~~~~~feature 3~~~~~~~~~"
for i in range(1, len(X3_test)-1):
    print "predict = ", predicts3[i], y3_test[i-1], y3_test[i]
    if ((predicts3[i]-predicts3[i-1]) >= 0) != ((y3_test[i]-y3_test[i-1]) >= 0):
        print '\033[91m'+str((predicts3[i]-predicts3[i-1]) >= 0)+'\033[0m', (y3_test[i]-y3_test[i-1]) >= 0
        false3_count += 1
    else:
        print (predicts3[i]-predicts3[i-1]) >= 0, (y3_test[i]-y3_test[i-1]) >= 0
        true3_count += 1

print ''
print X3_test[len(X3_test)-1:len(X3_test)], y3_test[len(X3_test)-1]
print gbm3.predict(X3_test[len(X3_test)-1:len(X3_test)])-gbm3.predict(X3_test[len(X3_test)-2:len(X3_test)-1]) >= 0
print "true3_count = ", true3_count, "false3_count = ", false3_count, "len(X3_test) = ", len(X3_test)-2
print "~~~~~~~~~~~~~~~~~~~~"

print "*********************************"
print "true1_count = ", true1_count, "false1_count = ", false1_count, "len(X1_test) = ", len(X1_test)-2
print "true2_count = ", true2_count, "false2_count = ", false2_count, "len(X3_test) = ", len(X3_test)-2
print "true3_count = ", true3_count, "false3_count = ", false3_count, "len(X3_test) = ", len(X3_test)-2
print "the prediction accuracy of model xgboost with feature 1 is ", float(true1_count)/(len(X1_test)-2)*1.0
print "the prediction accuracy of model 2 xgboost is ", float(true2_count)/(len(X3_test)-2)*1.0
print "the prediction accuracy of model xgboost with feature 3 is ", float(true3_count)/(len(X3_test)-2)*1.0
print "*********************************"

dates = [dt.datetime.strptime(d, '%Y-%m-%d').date() for d in dates]
plt.figure(1)
plt.subplot(311)
plt.plot(dates[len(dates)-len(y1_test):len(dates)], y1_test, color='g')
plt.plot(dates[len(dates)-len(y1_test):len(dates)], predicts, color='r')
plt.subplot(312)
plt.plot(dates[len(dates)-len(y3_test):len(dates)], y3_test, color='g')
plt.plot(dates[len(dates)-len(y3_test):len(dates)], predicts3, color='r')
plt.subplot(313)
plt.plot(dates[len(dates)-len(y3_test):len(dates)], y3_test, color='g')
plt.plot(dates[len(dates)-len(y3_test):len(dates)], pred, color='r')
plt.show()
