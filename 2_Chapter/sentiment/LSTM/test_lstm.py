from algorithm.lstm_model import lstm_train, lstm_test
from algorithm.extract_feature import extract_lstm_train, extract_lstm_test


dictionary, x, y, length = extract_lstm_train('./data/car/train.xlsx')
xt, yt = extract_lstm_test(dictionary, './data/car/test.xlsx')

model = lstm_train(dictionary, x, y, length)

lstm_test(model, xt, yt)

