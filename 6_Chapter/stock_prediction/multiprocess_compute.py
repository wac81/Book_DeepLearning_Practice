# -*- coding:utf-8 -*-
import os
os.environ['KERAS_BACKEND'] = "theano"
os.environ['THEANO_FLAGS'] = "device=cpu"
from data_preprocess.preprocess import *
from data_preprocess.load_data import *
import csv
from data_preprocess.Extract_Features import Extract_Features
from keras.models import model_from_json
from algorithum.clf_mlp import clf_model
import tushare as ts
# import myglobal
import time
dates = []
oneDayLine = []
thirtyDayLine = []
month_dates = []
acc_result = []

from multiprocessing import Pool, Array, Process, Manager
# manager = Manager()
# acc_result = []
acc_result = Manager().list()

models_path = './data/models_22_test/'

# 删除原有目录，××××注意××××××
import shutil
# shutil.rmtree(models_path,True)
# os.remove('./models/*')  #清空
if os.path.isdir(models_path) is not True:
    os.mkdir(models_path)

stock_data_path = './data/stock_data/'
if os.path.isdir(stock_data_path) is not True:
    os.mkdir(stock_data_path)


# 结果文件需改 sz 或 sh
choose_stock_results = './data/sort_results_22_test.csv'

# 600004  603999   sh
stock_code_start_sh = 600004
stock_code_end_sh = 603999

# 000002  002815   sz
stock_code_start_sz = 2
stock_code_end_sz = 2815

download_economy()

stock_codes = [code for code in range(stock_code_start_sh, stock_code_end_sh)] #603996

stock_codes += [code for code in range(stock_code_start_sz, stock_code_end_sz)]

# 上证指数
open_index_sh, close_index_sh, volume_index_sh, ma5_index_sh, vma5_index_sh, dates_index_sh = load_index_open_close_volume_ma5_vma5_from_tushare(
    stock_data_path + '../sh.csv')

# 深证指数
open_index_sz, close_index_sz, volume_index_sz, ma5_index_sz, vma5_index_sz, dates_index_sz = load_index_open_close_volume_ma5_vma5_from_tushare(
    stock_data_path + '../sz.csv')


def compute_code(code):
    time.sleep(0.1)  # 防止进程争抢资源
    if len(str(code))<6:
        code = ''.join('0' for _ in range(6-len(str(code))))+str(code)
    try:
        # print "this is code ", code
        if download_fq_data_from_tushare(code):
            print code, "download over ~ "
        else:
            return

        # oneDayLine, dates = load_data_from_tushare(stock_data_path + str(code) + '.csv')
        # volume, volume_dates = load_volume_from_tushare(stock_data_path + str(code) + '.csv')
        open_price, oneDayLine, volume, ma5, vma5, dates = load_fq_open_close_volume_ma5_vma5_turnover_from_tushare(stock_data_path + str(code) + '_fq.csv')

        if (str(code)[0] == '6'):
            # 上证指数
            open_index, close_index, volume_index, ma5_index, vma5_index, dates_index = open_index_sh, close_index_sh, volume_index_sh, ma5_index_sh, vma5_index_sh, dates_index_sh
        else:
            # 深证指数
            open_index, close_index, volume_index, ma5_index, vma5_index, dates_index = open_index_sz, close_index_sz, volume_index_sz, ma5_index_sz, vma5_index_sz, dates_index_sz


        # thirtyDayLine, month_dates = load_data_from_tushare(stock_data_path + str(code) + '_month.csv')
        if len(oneDayLine) < 400:
            return

        ef = Extract_Features()
        daynum = 5
        '''
        ~~~~~ for classification ~~~~~~ X is delta close price, y is 10 for increase while 01 for decrease
        '''
        X_clf = []
        y_clf = []
        for i in range(daynum, len(oneDayLine)-1):
            #大单交易数据
            # big_deals = get_big_deal_volume(code, dates[i])

            '''
            对齐大盘与个股的日期,得到大盘的对应日期位置p
            由于大盘数据个别不准，必须以复权数据为标准进行对齐
            '''
            p = dates_index.index(dates[i])
            #组装数据

            X_delta = [oneDayLine[k] - oneDayLine[k - 1] for k in range(i - daynum, i)] + \
                      [volume[k] - volume[k-1] for k in range(i - daynum, i)] + \
                      [turnover[k] for k in range(i - daynum, i)] + \
                      [ma5[i]] + \
                      [vma5[i]] + \
                      [open_index[p]] + [close_index[p]] + [volume_index[p]] + [ma5_index[p]] + [vma5_index[p]] + \
                      [big_deals] + \
                      [ef.parse_weekday(dates[i])] + \
                      [ef.lunar_month(dates[i])] + \
                      [ef.MoneySupply(dates[i])]
                      # [ef.rrr(dates[i - 1])] + \
            X_clf.append(X_delta)
            y_clf.append([1, 0] if oneDayLine[i + 1] - oneDayLine[i] > 0 else [0, 1])
            # y_clf.append([1, 0] if ((oneDayLine[i] - oneDayLine[i - 1])/oneDayLine[i - 1]) > 0.01 else [0, 1])

        # X_clf = preprocessing.MinMaxScaler().fit_transform(X_clf)
        y_clf = preprocessing.MinMaxScaler().fit_transform(y_clf)

        #测试数据取多少在这里修改!
        X_clf_train, X_clf_test, y_clf_train, y_clf_test = create_Xt_Yt(X_clf, y_clf, 0.86)#0.8

        input_dime = len(X_clf[0])
        # out = input_dime * 2 + 1
        if True:#not os.path.isfile('./data/model_'+str(code)+'.h5'):
            model = clf_model(input_dime)
            model.fit(X_clf_train,
                      y_clf_train,
                      nb_epoch=700,
                      batch_size=50,
                      verbose=0,
                      # validation_split=0.12
                      )
            # serialize model to JSON
            model_json = model.to_json()
            with open(models_path + "model_" + str(code) + ".json", "w") as json_file:
                json_file.write(model_json)
            # serialize weights to HDF5
            model.save_weights(models_path +"model_" + str(code) + ".h5")
            print("Saved model to disk")

        else:

            json_file = open(models_path + 'model_' + str(code) + '.json', 'r')
            loaded_model_json = json_file.read()
            json_file.close()
            model = model_from_json(loaded_model_json)
            # load weights into new model
            model.load_weights(models_path + "model_" + str(code) + ".h5")
            print("Loaded model from disk")
            print "model" + str(code) + "loaded!"

        score = model.evaluate(X_clf_test, y_clf_test, batch_size=10)

        print "****************************************"
        print 'code =', code
        print "****************************************"

        print ""
        print "test : ", model.metrics_names[0], score[0], model.metrics_names[1], score[1]
        print("%s: %.2f%%" % (model.metrics_names[1], score[1] * 100))
        acc_result.append([code, score[1]])
            # return [code, score[1]]

    except Exception as e:
        print e
        # 有些股票停牌冷,或者刚上市公司数据不足以用于训练,过滤掉。
        print code, "is non type or is too less data!"
        return
# for stock in stock_codes:
#     compute_code(stock)

#并行化
from multiprocessing import Pool

# Make the Pool of workers
pool = Pool(1)
# Open the urls in their own threads
# and return the results

results = pool.map(compute_code, stock_codes)
#close the pool and wait for the work to finish
pool.close()
pool.join()



# acc结果排序
sort = sorted(acc_result, key=lambda x: (x[1]), reverse=True)
print sort
# 写入文件
with open(choose_stock_results, 'wb') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(sort)  # in order of list

print 'acc_result', len(acc_result)
# 平均acc
print "*******************************"
print sum([acc_result[i][1] for i in range(0, len(acc_result))])*1.0/len(acc_result)
print "*******************************"