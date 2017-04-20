# -*- coding: utf-8 -*-
import os
os.environ['KERAS_BACKEND'] = "theano"
os.environ['THEANO_FLAGS'] = "device=cpu"
# instruction: simulating the last month to see the profit and loss
from keras.models import model_from_json
import math
from data_preprocess.preprocess import *

principle = 50000
my_bonus = 0
my_stock_value = 0
left_money = principle
stock_dict = {}


models_path = 'models_22_val/'

acc_threshold = 0.64

acc_low_threshold = 1-acc_threshold

read_result = read_sort_result('./data/sort_result_22_val.csv')
# read_result += read_sort_result('./data/sort_results_sz.csv')

stock_num = 5  # 5手 500股
money_limit = 10000
# 根据阈值过滤排序结果
read_result = sorted(read_result, key=lambda x: (x[1]), reverse=True)
read_result = read_result[0:30]
read_result = [item for item in read_result if float(item[1]) >= acc_threshold]
# read_result = [item for item in read_result if float(item[1]) >= acc_threshold  or float(item[1]) <= acc_low_threshold]

data_path = './data/'
baseline, baseline_date = load_data(data_path + 'sh.csv')
am_price_latest, pm_price_latest = get_am_pm_price(str(read_result[0][0]), baseline_date[-1])
base_X, base_y = get_last_month_more_data_for_MLP(str(read_result[0][0]))
X_all = {}
y_all = {}
model_all = {}


download_economy()

for item in range(0, len(read_result)):
    json_file = open(data_path + models_path + 'model_' + str(read_result[item][0]) + '.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    model_all[item] = model_from_json(loaded_model_json)
    # load weights into new model
    model_all[item].load_weights(data_path + models_path + "model_" + str(read_result[item][0]) + ".h5")
    print("Loaded model " + str(read_result[item][0]) + " from disk")
    print "model " + str(read_result[item][0]) + " loaded!"
    #下载当日个股复权数据
    if download_fq_data_from_tushare(str(read_result[item][0])):
        print str(read_result[item][0]), "download over ~ "
    X_all[item], y_all[item] = get_last_month_more_data_for_MLP(str(read_result[item][0]))
    X_all[item] = preprocessing.MinMaxScaler().fit_transform(X_all[item])


# oneDayLine, date = load_data(data_path + 'stock_data/' + str(read_result[0][0]) + '.csv')
for i in range(0, len(base_X)):
    for model_index in range(0, len(read_result)):
        am_price, pm_price = get_am_pm_price(str(read_result[model_index][0]), baseline_date[i - len(base_X)])
        # 试探那一天股票是否停牌
        # if math.isnan(pm_price):
        #     print str(read_result[model_index][0]), ": this stock is Suspension!(ting pai)"
        # 试探股票是否停牌
        # am_price_latest, pm_price_latest = get_am_pm_price(str(read_result[model_index][0]), baseline_date[-1])
        if math.isnan(pm_price):
            print str(read_result[model_index][0]), ": this stock is Suspension!(ting pai)"
        else:
            # increase:Buy
            # if model_all[model_index].predict(X_all[model_index][i].reshape((1, len(X_all[model_index][i]))))[0][0] > 0.7:
            # print str(read_result[model_index][0]) + ":", model_all[model_index].predict(X_all[model_index][i].reshape((1, len(X_all[model_index][i]))))[0][0]
            if (float(read_result[model_index][1]) >= acc_threshold and
                        model_all[model_index].predict(
                            X_all[model_index][i].reshape((1, len(X_all[model_index][i]))))[0][0] > 0.80) or \
                    (float(read_result[model_index][1]) <= acc_low_threshold and
                             model_all[model_index].predict(
                                 X_all[model_index][i].reshape((1, len(X_all[model_index][i]))))[0][
                                 0] <= 0.6):

                if left_money >= money_limit:
                    if str(read_result[model_index][0]) in stock_dict.keys():
                        if stock_dict[str(read_result[model_index][0])] > stock_num:
                            print str(read_result[model_index][0]), "you can't buy too much!"
                            break
                        else:
                            stock_dict[str(read_result[model_index][0])] += int(
                                money_limit / am_price / 100)
                            left_money -= int(money_limit / am_price / 100) * am_price * 100 * (1 + 0.003)
                    else:
                        stock_dict[str(read_result[model_index][0])] = int(money_limit / am_price / 100)
                        left_money -= int(money_limit / am_price / 100) * am_price * 100 * (1 + 0.003)
                    print i, ' ', baseline_date[i - len(base_X)], ' ', str(
                        read_result[model_index][0]), "Buy Buy Buy!"
                else:
                    print i, ' ', baseline_date[i - len(base_X)], ' ', str(read_result[model_index][0]), \
                        "I want to buy, but there is no money left!"

            # decrease:sell
            # elif model_all[model_index].predict(X_all[model_index][i].reshape((1, len(X_all[model_index][i]))))[0][0] <= 0.4:
            if (float(read_result[model_index][1]) >= acc_threshold and
                        model_all[model_index].predict(
                            X_all[model_index][i].reshape((1, len(X_all[model_index][i]))))[0][0] <= 0.6) or \
                    (float(read_result[model_index][1]) <= acc_low_threshold and
                             model_all[model_index].predict(
                                 X_all[model_index][i].reshape((1, len(X_all[model_index][i]))))[0][0] > 0.8):
                if str(read_result[model_index][0]) in stock_dict.keys():
                    if stock_dict[str(read_result[model_index][0])] > 0:
                        left_money += stock_dict[str(read_result[model_index][0])] * pm_price * 100*(1-0.004)
                        stock_dict.pop(str(read_result[model_index][0]), None)
                        print i, ' ', baseline_date[i-len(base_X)], ' ', " Sell out ", str(read_result[model_index][0]), " !"
                else:
                    print i, ' ', baseline_date[i-len(base_X)], ' ', str(read_result[model_index][0]), \
                        " : I want to sell out, but you don't have this stock!"


    # for model_index in range(0, len(read_result)):
    #     am_price, pm_price = get_am_pm_price(str(read_result[model_index][0]),
    #                                          baseline_date[i - len(base_X)])
    #     # 试探那一天股票是否停牌
    #     # if math.isnan(pm_price):
    #     #     print str(read_result[model_index][0]), ": this stock is Suspension!(ting pai)"
    #     # 试探股票是否停牌
    #     # am_price_latest, pm_price_latest = get_am_pm_price(str(read_result[model_index][0]), baseline_date[-1])
    #     if math.isnan(pm_price):
    #         print str(read_result[model_index][0]), ": this stock is Suspension!(ting pai)"
    #     else:
    #         # increase:Buy
    #         # if model_all[model_index].predict(X_all[model_index][i].reshape((1, len(X_all[model_index][i]))))[0][0] > 0.7:
    #         print str(read_result[model_index][0]) + ":", \
    #         model_all[model_index].predict(X_all[model_index][i].reshape((1, len(X_all[model_index][i]))))[
    #             0][0]
    #         if (float(read_result[model_index][1]) >= acc_threshold and
    #                     model_all[model_index].predict(
    #                         X_all[model_index][i].reshape((1, len(X_all[model_index][i]))))[0][0] > 0.85) or \
    #                 (float(read_result[model_index][1]) <= acc_low_threshold and
    #                          model_all[model_index].predict(
    #                              X_all[model_index][i].reshape((1, len(X_all[model_index][i]))))[0][
    #                              0] <= 0.6):
    #
    #             if left_money >= money_limit:
    #                 if str(read_result[model_index][0]) in stock_dict.keys():
    #                     if stock_dict[str(read_result[model_index][0])] > 5:
    #                         print str(read_result[model_index][0]), "you can't buy too much!"
    #                         break
    #                     else:
    #                         stock_dict[str(read_result[model_index][0])] += int(
    #                             money_limit / am_price / 100)
    #                         left_money -= int(money_limit / am_price / 100) * am_price * 100 * (1 + 0.003)
    #                 else:
    #                     stock_dict[str(read_result[model_index][0])] = int(money_limit / am_price / 100)
    #                     left_money -= int(money_limit / am_price / 100) * am_price * 100 * (1 + 0.003)
    #                 print i, ' ', baseline_date[i - len(base_X)], ' ', str(
    #                     read_result[model_index][0]), "Buy Buy Buy!"
    #             else:
    #                 print i, ' ', baseline_date[i - len(base_X)], ' ', str(read_result[model_index][0]), \
    #                     "I want to buy, but there is no money left!"


# last_day : all sell
for key in stock_dict:
    am_price, pm_price = get_am_pm_price(str(key), baseline_date[-1])
    my_stock_value += pm_price * stock_dict[key] * 100 * (1 - 0.004)
    print key, pm_price,  stock_dict[key], "my_stock_value = ", pm_price * stock_dict[key]*100

print "cash_money = ", left_money
left_money += my_stock_value
print "left_money = ", left_money
my_bonus = left_money - principle
print "after a month, my bonus is : ", my_bonus

