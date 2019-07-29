"""
企查查根据企业名字提取企业信息
"""

import time
import json


import requests
import pymysql
import pandas as pd
from lxml import etree
from bs4 import BeautifulSoup


class Spider:
    """
    :param companies 目标企业列表
    :param headers 需要设置的cookie,user-agent...等
    """
    def __init__(self, companies, headers):
        self.companies = companies
        self.headers = headers

    def search_com(self):
        for company in self.companies:
            com_id = self.query_com_id(company)
            if not com_id:
                url = 'https://www.qichacha.com/search?key=' + company
                res1 = requests.get(url=url, headers=self.headers)
                if res1.status_code == 200:
                    res1.encoding = "utf-8"
                    selector = etree.HTML(res1.text)
                    # 公司名称匹配
                    try:
                        _name = selector.xpath(
                            "//tbody[@id='search-result']/tr[1]/td[3]/a/text() |"
                            " //tbody[@id='search-result']/tr[1]/td[3]/a/em/text() |"
                            " //tbody[@id='search-result']/tr[1]/td[3]/a/em/em/text() "
                        )
                    except Exception as error:
                        _name = None
                    if _name:
                        if _name[0] == company:
                            sec_url = selector.xpath("//tbody[@id='search-result']/tr[1]//a/@href")[0]
                            com_id = sec_url.replace('/firm_', '').replace('.html', '')
                            com_info = self.get_com(com_id, company)
                            if com_info['code'] == 200:
                                # 进一步获取股东信息
                                people = self.get_people(com_id)
                                if people['code'] == 200:
                                    sql1 = r"insert into com_base_info (company_name,tell,email,web_link,fa_ren," \
                                           r"reg_money,paid_money,status,found_date,credit_code,taxpayer_number," \
                                           r"reg_number,organ_code,company_type,industry,approval_date,reg_authority," \
                                           r"area,english_name,old_name,insured_number,personnel_scale,business_term," \
                                           r"address,business_scope,description,add_time,update_time) values (%s,%s," \
                                           r"%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s," \
                                           r"%s,%s);"
                                    self.insert_to_db(sql1, com_info['datas'])
                                    new_com_id = self.query_com_id(company)[0]
                                    datas = people['datas']
                                    if datas:
                                        sql2 = r"insert into com_stock_info (name,percent,should_capi,add_time," \
                                               r"update_time,company_id) values (%s,%s,%s,%s,%s,%s);"
                                        for record in datas:
                                            record.append(new_com_id)
                                            self.insert_to_db(sql2, record)
                                    info = "{} ok".format(company)
                                    print(info)
                                    self.log(info)
                                else:
                                    print("{} get_people error".format(company))
                            else:
                                info = "{} {}".format(company, com_info['code'])
                                self.log(info)
                        else:
                            info = " {} 的信息检索失败".format(company)
                            self.log(info)
                    else:
                        print(_name)
                else:
                    print(res1.status_code)
            else:
                self.log(company + "信息重复收集")

    def get_com(self, com_id, company):
        url = 'https://www.qichacha.com/firm_{}.html'.format(com_id)
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            html = response.text
            selector1 = etree.HTML(html)
            soup1 = BeautifulSoup(html, 'lxml')
            base_info = [company]
            # 电话 官网 邮箱 法人
            target = soup1.find('div', id='company-top').\
                find('div', 'row').find('div', 'content').find('div', 'dcontent').find_all('div', 'row')
            try:
                tell = target[0].find('span', 'fc').find('span', 'cvlu').find('span').get_text()
            except Exception as error:
                tell = '-'
            base_info.append(tell)
            try:
                email = target[1].find('span', 'fc').find('span', 'cvlu').find('a').get_text()
            except Exception as error:
                email = '-'
            base_info.append(email)
            try:
                web_link = target[0].find_all('span', 'cvlu')[-1].find_all('a')[-1].get_text().strip()
            except Exception as error:
                web_link = '-'
            base_info.append(web_link)
            try:
                fa_ren = selector1.xpath("//h2[@class='seo font-20']/text()")[0]
            except Exception as error:
                fa_ren = '-'
            base_info.append(fa_ren)

            # 工商信息
            _list = []
            r_result = selector1.xpath("//section[@id='Cominfo']/table[last()]/tr")
            for r in r_result:
                result = r.xpath("td/text()")
                if '曾用名' == result[0].strip() and len(result) % 2 == 1:
                    result.insert(1, '')
                for i in range(len(result)):
                    if i % 2 != 0:
                        _list.append(result[i].strip().replace('：', ''))

            # 对含有企业曾用名作特殊处理
            try:
                r_name = selector1.xpath("//section[@id='Cominfo']/table[last()]/tr/td/span/text()")[0].strip()
            except:
                r_name = '-'
            _list[14] = r_name


            # count = _list.count('')
            # for i in range(count):
            #     _list.remove('')

            _list = filter(lambda x: x != '', _list)

            base_info += _list
            # 简介
            try:
                text = selector1.xpath("//p[@id='textShowMore']/text()")
                desc = ''.join(text)
                if not desc.replace(' ', ''):
                    try:
                        text = selector1.xpath(
                            "//div[@class='modal-body']/div[@class='m-t-sm m-b-sm']/text() |"
                            " //div[@class='modal-body']/div[@class='m-t-sm m-b-sm']/p/span/text() |"
                            " //div[@class='modal-body']/div[@class='m-t-sm m-b-sm']/span/text() |"
                            " //div[@class='modal-body']/div[@class='m-t-sm m-b-sm']/div/span/text() |"
                            " //div[@class='modal-body']/div[@class='m-t-sm m-b-sm']/div/text()|"
                            " //div[@class='modal-body']/div[@class='m-t-sm m-b-sm']/p/text() |"
                            " //div[@class='modal-body']/div[@class='m-t-sm m-b-sm']/pre/text()")
                        desc = ''.join(text).replace('\n', '').strip()
                    except Exception as error:
                        desc = '-'
            except Exception as error:
                desc = '-'
            cur_time = time.strftime("%Y-%m-%d %H:%M:%S")
            base_info.append(desc)
            base_info.append(cur_time)
            base_info.append(cur_time)
            return dict(code=200, datas=base_info)
        else:
            return dict(code=response.status_code, datas=None)

    def get_people(self, com_id):

        g_url = 'https://www.qichacha.com/cms_guquanmap3?keyNo={}'.format(com_id)
        res = requests.get(url=g_url, headers=self.headers)
        if res.status_code == 200:
            gudong_list = []
            res.encoding = 'utf-8'
            target = json.loads(res.text)['gudong']['DetailList']
            if target:
                cur_time = time.strftime("%Y-%m-%d %H:%M:%S")
                for obj in target:
                    data = [obj['Name'], obj['Percent'], obj['ShouldCapi'], cur_time, cur_time]
                    gudong_list.append(data)
            return dict(code=200, datas=gudong_list)
        else:
            return dict(code=res.status_code, datas=None)

    def insert_to_db(self, sql, data):

        con = pymysql.Connect(
            host="localhost",
            user="root",
            database="develop",
            password="000000",
            charset="utf8",
            port=3306
        )
        cursor = con.cursor()
        try:
            cursor.execute(sql, data)
            con.commit()
        except Exception as error:
            con.rollback()
            print(error)
        cursor.close()
        con.close()

    def query_com_id(self, company_name):

        con = pymysql.Connect(
            host="localhost",
            user="root",
            database="develop",
            password="000000",
            charset="utf8",
            port=3306
        )
        cursor = con.cursor()
        sql = "SELECT id FROM com_base_info WHERE company_name='%s' " % company_name
        cursor.execute(sql)
        pro = cursor.fetchone()
        cursor.close()
        con.close()
        return pro

    def log(self, datas):
        with open('./qichacha/com_log.txt', 'a+', encoding="utf-8") as f:
            cur_time = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write("{}".format(cur_time) + datas + '\n')


if __name__ == '__main__':

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Cookie': 'QCCSESSID=fjrgk2i944r431e3ire27dgt07; UM_distinctid=16a953cc33ed2-05161c3e03310d-6353160-100200-16a953cc33f8b5; CNZZDATA1254842228=983444626-1557281714-https%253A%252F%252Fwww.baidu.com%252F%7C1557281714; zg_did=%7B%22did%22%3A%20%2216a953cc37f6d5-0b8ba4442297b2-6353160-100200-16a953cc3803e9%22%7D; Hm_lvt_3456bee468c83cc63fb5147f119f1075=1557281949; hasShow=1; _uab_collina=155728194887360439943617; acw_tc=6547699615572819563641343e49512d0440af3b33947c7e4bb839b025; Hm_lpvt_3456bee468c83cc63fb5147f119f1075=1557282274; zg_de1d1a35bfa24ce29bbf2c7eb17e6c4f=%7B%22sid%22%3A%201557281948548%2C%22updated%22%3A%201557282283645%2C%22info%22%3A%201557281948553%2C%22superProperty%22%3A%20%22%7B%7D%22%2C%22platform%22%3A%20%22%7B%7D%22%2C%22utm%22%3A%20%22%7B%7D%22%2C%22referrerDomain%22%3A%20%22www.baidu.com%22%2C%22cuid%22%3A%20%227043860c36ddd8b47154a80be9555b9c%22%7D',
        'Host': 'www.qichacha.com',
        'Referer': 'https://www.qichacha.com/firm_625e8aecdf9f997abfa830351499971f.html',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/74.0.3729.108 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    df = pd.read_excel('company.xlsx')
    com_list = df['企业名称'].values.tolist()[:10]
    spider = Spider(companies=com_list[1:20], headers=headers)
    try:
        spider.search_com()
    except Exception as error:
        print(Exception)