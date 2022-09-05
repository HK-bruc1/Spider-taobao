# -*- codeing = utf-8 -*-
# @Time : 2022/9/4 9:20
# @Author : Xing
# @File : taobao.py
# @Software: PyCharm

import undetected_chromedriver as uc  # 大牛的补丁，可以绕过检测
# 正常webdriver驱动的引入
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from natsort import natsorted  # 排序的库
from lxml import etree  # xpath的库
import random  # 随机数
import time


class TaoBao:
    """同函数之调用方便一点在类中"""
    # 对象初始化
    def __init__(self):
        url = 'https://login.taobao.com/member/login.jhtml'
        self.url = url
        self.browser = uc.Chrome()
        # 超时时长为10s，为后面的那个等待设置的限制
        self.wait = WebDriverWait(self.browser, 10)

    # 登录淘宝
    def login(self):

        # 打开网页
        self.browser.get(self.url)

        # 自适应等待，输入账号
        self.browser.implicitly_wait(30)
        self.browser.find_element(By.XPATH, '//*[@id="fm-login-id"]').send_keys(taobao_username)

        # 自适应等待，输入密码
        self.browser.implicitly_wait(30)
        self.browser.find_element(By.XPATH, '//*[@id="fm-login-password"]').send_keys(taobao_password)

        # 自适应等待，点击确认登录按钮
        self.browser.implicitly_wait(30)
        self.browser.find_element(By.XPATH, '//*[@id="login-form"]/div[4]/button').click()

        # 直到获取到淘宝会员昵称才能确定是登录成功（根据结构层数下来的，定位到某一个元素）
        taobao_name = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.site-nav-bd > ul.site-nav-bd-l > li#J_SiteNavLogin > div.site-nav-menu-hd > div.site-nav-user > a.site-nav-login-info-nick ')))
        # 输出淘宝昵称
        print('淘宝用户：'+taobao_name.text)

    # 模拟向下滑动浏览
    def swipe_down(self, second):
        for i in range(int(second/0.1)):
            # 根据i的值，模拟上下滑动
            if(i%2==0):
                js = "var q=document.documentElement.scrollTop=" + str(300+400*i)
            else:
                js = "var q=document.documentElement.scrollTop=" + str(200 * i)
            self.browser.execute_script(js)
            time.sleep(0.1)

        js = "var q=document.documentElement.scrollTop=100000"
        self.browser.execute_script(js)
        time.sleep(0.1)

    def true_money(self, gms):
        """通过排序大概选出实付款"""
        gm = natsorted(gms)
        i = 0
        while True:
            if gm[i] != '0.00':  # 如果不是0就是实付款,是字符串
                return gm[i]
            else:
                i += 1

    # 爬取淘宝 我已买到的宝贝商品数据
    def crawl_good_buy_data(self):

        # 对我已买到的宝贝商品数据进行爬虫
        # 不用去点击了，登陆后，再发送目标页面请求，跟点击一样的效果（对于页面要切换的情况）
        self.browser.get("https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm")
        # 点击交易状态出现下拉框
        self.browser.implicitly_wait(30)
        self.browser.find_element(By.XPATH, '//*[@id="tp-bought-root"]/table/tbody/tr/th[6]/span').click()
        # 点击交易成功的单子(模糊定位)
        self.browser.maximize_window()  # 默认窗口是最小化的，出现了不能点击的情况，要最大化一下，而且还要等几秒，不然页面都没加载完，就开始爬了
        self.browser.find_element(By.XPATH, '//li[contains(text(),"交易成功")]').click()  # 模糊定位yyds，跟正则差不多
        # 切换页面需要时间，等待
        time.sleep(4)
        # 单子数和金额
        number = 0
        count = 0
        # 遍历所有页数
        for page in range(1, 7):

            # 等待该页面全部已买到的宝贝商品数据加载完毕
            good_total = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#tp-bought-root > div.js-order-container')))

            # 获取本页面源代码
            html = self.browser.page_source
            # 我只会xpath解析。。。
            tree = etree.HTML(html)
            goods = tree.xpath('//*[@class="index-mod__order-container___1ur4- js-order-container"]')
            for good in goods:
                # 交易数量
                number += 1
                if number == 1:
                    start_time = good.xpath('.//*[@class="bought-wrapper-mod__create-time___yNWVS"]/text()')[0]
                elif page == 6:
                    end_good = goods[-1]  # 最后一页的倒数第一个商品
                    end_time = end_good.xpath('.//*[@class="bought-wrapper-mod__create-time___yNWVS"]/text()')[0]
                goods_time = good.xpath('.//*[@class="bought-wrapper-mod__create-time___yNWVS"]/text()')[0]
                goods_name = good.xpath('./div[1]/table[1]/tbody[2]/tr[1]/td[1]//*[@style="line-height:16px;"]/text()')[0]
                # 没办法只能通过模糊定位，来找，试了很多方法都不行在xpath里，而且只能定位四个价格(返回的是数字字符串列表)
                goods_moneys = good.xpath('.//span[contains(text(),"￥")]/following-sibling::span[1]/text()')
                # 大部分订单都是对的，对有赠品订单可能不太准确（赠品有一个比较低的价格）
                goods_money = self.true_money(goods_moneys)
                count += float(goods_money)
                print(goods_time+' ', goods_name+' ', goods_money+' 元')
            print('\n')

            # 大部分人被检测为机器人就是因为进一步模拟人工操作
            # 模拟人工向下浏览商品，即进行模拟下滑操作，防止被识别出是机器人
            # 随机滑动延时时间
            swipe_time = random.randint(1, 3)
            self.swipe_down(swipe_time)

            # 等待下一页按钮 出现
            good_total = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.pagination-next')))
            # 点击下一页按钮
            good_total.click()
            time.sleep(2)
        print(f'总计成功交易:{number} 单')
        print(f'{end_time}到{start_time}截止估计总消费:{round(count,2)} 元')


if __name__ == "__main__":
    # 使用之前请先查看当前目录下的使用说明文件README.MD

    taobao_username = "18474690403"  # 改成你的账号
    taobao_password = "20171410618good"  # 改成你的密码
    a = TaoBao()
    a.login()  # 登录
    a.crawl_good_buy_data()  # 爬取淘宝 我已买到的宝贝商品数据
