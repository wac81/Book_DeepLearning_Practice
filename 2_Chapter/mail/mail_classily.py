#coding=utf8
from tgrocery import Grocery
train_src = [
    ('garbage', '(AD)蒲公英新品X5首发：你的第一台“跳蛋”路由器'),
    ('garbage', '016 IBM云计算峰会报名免费抢座-2016.10.19 北京国际饭店会议中心'),
    ('garbage', 'Can We Talk? Setting the Record Straight About 4 Content Misconceptions'),
    ('garbage', '欢迎参加简仪科技开源测控技术研讨会-北京站2016年9月22日'),
    ('garbage', 'NEW! Advance your career with 19 MicroMasters programs'),
    ('garbage', '0.1元购家电！iPhone6s-Plus仅4488，海尔热水器699~10亿优惠券狂撒，国庆福利快接着→'),
    ('normal', '[WeLoop社区] 论坛注册地址 - 论坛注册地址 这封信是由 WeLoop社区 发送的'),
    ('normal', 'Fwd: [Bitbucket] SSH key added to futurenlp'),
    ('normal', '您的帐户在Linux设备上的Chrome中有新的登录活动'),
    ('normal', '神经网络与深度学习代码'),
    ('normal', 'Fw:关于ICP备案申请审核通过的通知'),
    ('normal', '技术部-SSL数字加密证书')
]


# 创建一个 grocery，'mail_class'为模型名称
grocery = Grocery('mail_class')

grocery.train(train_src)

grocery.save()

# Load model(和之前设的名字一样)
new_grocery = Grocery('mail_class')

new_grocery.load()
# 预测
print new_grocery.predict('关于神经网络与深度学习一书源码')
# education
# Test from list
# test_src = [
#     ('education', 'Abbott government spends $8 million on higher education media blitz'),
#     ('sports', 'Middle East and Asia boost investment in top level sports'),
# ]
# new_grocery.test(test_src)
# # Return Accuracy
# # 1.0
# # Or test from file
# new_grocery.test('test_ch.txt')
# # Custom tokenize
# custom_grocery = Grocery('custom', custom_tokenize=list)