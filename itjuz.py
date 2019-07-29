"""
it 桔子项目信息采集
"""
import json
import time
import re
import os
import threading

import requests
import pymysql
from selenium import webdriver


class Spider:
    """
    爬虫基类
    """
    TAG = True  # 监控状态的变量

    def __init__(self, payload, token, cookies, page):
        self.authorization = token
        self.cookies = cookies
        self.payloadData = payload
        self.page = page

    def get_contents(self):
        """
        入口主函数 根据payload条件列表获取项目基本信息
        :return:
        """
        api_url = "https://itjuzi.com/api/companys"
        headers1 = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Authorization': self.authorization,
            'Connection': 'keep-alive',
            'Content-Length': '203',
            'Content-Type': 'application/json;charset=UTF-8',
            'Cookie': self.cookies,
            'CURLOPT_FOLLOWLOCATION': 'true',
            'Host': 'itjuzi.com',
            'Origin': 'https://itjuzi.com',
            'Referer': 'https://itjuzi.com/company',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/74.0.3729.108 Safari/537.36',
        }
        self.payloadData['page'] = self.page
        response = requests.post(url=api_url, headers=headers1, data=json.dumps(self.payloadData))
        if response.status_code == 200:
            response.encoding = 'utf-8'
            target = json.loads(response.text)['data']['data']
            for project in target:
                juz_id = project['id']  # 二级id
                project_name = project['name']
                company_name = project['register_name']
                found_time = project['agg_born_time']
                current_round = project['round']
                total_money = project['total_money']  # 已经获投总额
                tags = ','.join([i['tag_name'] for i in project['tag']])
                industry = project['scope']  # 行业分类
                sub_industries = project['sub_scope']  # 子行业
                description = project['des']
                province = project['prov']
                city = project['city']
                cdn = project['logo']
                name = re.findall(r'.*/(.*(png|jpg|jpeg|icon|gif|PNG|JPG|JPEG|ICON|GIF)).*', cdn)[0][0]
                fin_needs = self.payloadData['com_fund_needs']  # 融资需求
                local = 1 if project['location'] == 'in' else 0
                status = project['status']  # 经营状态
                base_info = [project_name, company_name, found_time, tags, current_round, total_money, industry,
                             sub_industries, description, province, city, fin_needs, local, status]

                # 判断数据库是否存在该项目信息
                pro_id = self.query_pro_id(project_name, company_name)
                if not pro_id:
                    # 继续获取历史融资信息
                    inv_info = self.get_invest(juz_id)
                    if inv_info['code'] == 200:
                        # 获取团队信息和竞品信息
                        persons_info = self.get_person(juz_id)
                        if persons_info['code'] == 200:
                            # 处理主表当前伦次非最新
                            if inv_info['datas']:
                                # 主项目信息表更新
                                sql1 = r"insert into pro_base_info (project_name,company_name,found_time,tags," \
                                       r"current_round,total_money,industry,sub_industries, description,province," \
                                       r"city,fin_needs,local,status,image,update_time,add_time)values" \
                                       r"(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
                                logo_path = self.deal_images(cdn, name)
                                cur_time = time.strftime("%Y-%m-%d %H:%M:%S")
                                cur_round = inv_info['datas'][-1][0]
                                base_info[4] = cur_round
                                base_info.append(logo_path)
                                base_info.append(cur_time)
                                base_info.append(cur_time)
                                self.insert_to_db(sql1, base_info)

                                # 获取新建项目id
                                new_pro_id = self.query_pro_id(project_name, company_name)[0]

                                # 推荐表（限定条件）同步
                                exc_cond = ["尚未获投", "新三板", "已被收购", "已上市", "已退市", "战略投资", "种子轮",
                                            "并购", "IPO上市", "IPO上市后", "合并", "退市", "新三板定增"]
                                if cur_round not in exc_cond:
                                    rec_info = [project_name, description, province, city, cur_round, local, tags,
                                                industry]
                                    sql_rec = r"insert into rec_pro_info (project_name,description,province,city," \
                                              r"current_round, local,tags,industry,image,pro_id,update_time," \
                                              r"add_time) values (%s,%s,%s,%s,%s,%s,%s,%s," \
                                              r"%s,%s,%s,%s);"
                                    rec_info.append(logo_path)
                                    rec_info.append(new_pro_id)
                                    rec_info.append(cur_time)
                                    rec_info.append(cur_time)

                                    thread = threading.Thread(target=self.insert_to_db, args=(sql_rec, rec_info))
                                    thread.start()
                                    # 历史融资信息更新
                                    sql2 = "insert into pro_invest_info (fin_round,investors,fin_date," \
                                           "update_time,add_time,money,project_id) values (%s,%s,%s,%s,%s,%s,%s);"
                                    for obj in inv_info['datas']:
                                        obj.append(new_pro_id)
                                        self.insert_to_db(sql2, obj)

                                # 团队信息更新
                                if persons_info['persons']:
                                    sql3 = r"insert into pro_team_info(name,position,description,update_time," \
                                           r"add_time,project_id) values (%s,%s,%s,%s,%s,%s);"
                                    for person in persons_info['persons']:
                                        person.append(new_pro_id)
                                        self.insert_to_db(sql3, person)

                                # 竞品信息更新
                                if persons_info['compepitors']:
                                    sql4 = "insert into pro_similar_info(competing_name,current_round,industry,sub_industries," \
                                           "update_time,add_time,tag,money,project_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s);"
                                    for com in persons_info['compepitors']:
                                        com.append(new_pro_id)
                                        self.insert_to_db(sql4, com)
                            else:
                                # 主项目信息表更新
                                sql1 = r"insert into pro_base_info (project_name,company_name,found_time,tags," \
                                       r"current_round,total_money,industry,sub_industries, description,province," \
                                       r"city,fin_needs,local,status,image,update_time,add_time)values" \
                                       r"(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
                                logo_path = self.deal_images(cdn, name)
                                cur_time = time.strftime("%Y-%m-%d %H:%M:%S")
                                base_info.append(logo_path)
                                base_info.append(cur_time)
                                base_info.append(cur_time)
                                self.insert_to_db(sql1, base_info)
                                # 获取新建项目id
                                new_pro_id = self.query_pro_id(project_name, company_name)[0]

                                # 团队信息更新
                                if persons_info['persons']:
                                    sql3 = r"insert into pro_team_info(name,position,description,update_time," \
                                           r"add_time,project_id) values (%s,%s,%s,%s,%s,%s);"
                                    for person in persons_info['persons']:
                                        person.append(new_pro_id)
                                        self.insert_to_db(sql3, person)

                                # 竞品信息更新
                                if persons_info['compepitors']:
                                    sql4 = "insert into pro_similar_info(competing_name,current_round,industry,sub_industries," \
                                           "update_time,add_time,tag,money,project_id) values (%s,%s,%s,%s,%s,%s,%s,%s,%s);"
                                    for com in persons_info['compepitors']:
                                        com.append(new_pro_id)
                                        self.insert_to_db(sql4, com)
                            success_info = "{} ok".format(project_name)
                            print(success_info)
                            self.log(success_info)
                        else:
                            lo = "get_persons_error {}".format(juz_id)
                            self.log(lo)
                    else:
                        Spider.TAG = False
                        lo = "get_invest_error {}".format(juz_id)
                        self.log(lo)
                else:
                    lo = "<{}>信息重复,请做更新操作".format(project_name)
                    self.log(lo)
        else:
            Spider.TAG = False
            lo = "error page:{}".format(self.page)
            self.log(lo)

    def get_invest(self, juz_id):
        """
        获取项目历史融资信息（二级抓取）
        :param juz_id: 二级关键字段
        :return: dict（请求返回状态, datas）
        """
        inv_url = "https://itjuzi.com/api/companies/{}/invse".format(juz_id)
        refer = 'https://itjuzi.com/company/{}'.format(juz_id)
        headers2 = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Authorization': self.authorization,
            'Connection': 'keep-alive',
            'Cookie': self.cookies,
            'CURLOPT_FOLLWLOCATION': 'true',
            'Host': 'itjuzi.com',
            'Referer': refer,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/74.0.3729.108 Safari/537.36'
        }
        res = requests.get(url=inv_url, headers=headers2)
        datas = []
        if res.status_code == 200:
            res.encoding = 'utf-8'
            obj = json.loads(res.text)
            invst_info = obj['invst']
            if invst_info:
                cur_time = time.strftime("%Y-%m-%d %H:%M:%S")
                for inv in invst_info:
                    round = inv['round']
                    money = inv['money']
                    investor = []
                    for i in inv['investors']:
                        investor.append(i['name'])
                    if investor:
                        investors = ','.join(investor)
                    else:
                        investors = '未透露'
                    date = inv['date']
                    data = [round, investors, date, cur_time, cur_time, money]
                    datas.append(data)
                return dict(code=200, datas=datas)
            else:
                return dict(code=200, datas=datas)
        else:
            return dict(code=res.status_code, datas=datas)

    def get_person(self, juz_id):
        """
        获取团队信息和竞品信息（二级抓取）
        :param juz_id: 二级关键字段
        :return: dict(响应状态,团队信息,竞品信息)
        """
        refer = 'https://itjuzi.com/company/{}'.format(juz_id)
        person_url = 'https://itjuzi.com/api/companies/{}?type=person'.format(juz_id)
        headers3 = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Authorization': self.authorization,
            'Connection': 'keep-alive',
            'Cookie': self.cookies,
            'CURLOPT_FOLLOWLOCATION': 'true',
            'Host': 'itjuzi.com',
            'Referer': refer,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/74.0.3729.108 Safari/537.36',
        }
        res = requests.get(url=person_url, headers=headers3)
        persons = []
        compepitors = []
        if res.status_code == 200:
            res.encoding = 'utf-8'
            contents = json.loads(res.text)['data']
            person_list = contents['person']
            cur_time = time.strftime("%Y-%m-%d %H:%M:%S")
            if person_list:

                for per in person_list:
                    person_info = [per['name'], per['des'], per['per_des'], cur_time, cur_time]
                    persons.append(person_info)
            comp = contents['competitor']['tag_rel_com']

            # 说明：竞品信息过多 暂定每个大类取3个
            if comp:
                for com in comp.values():
                    tag = com['tag_name']
                    for index, obj in enumerate(com['com_info']):
                        comp_info = [obj['name'], obj['round_name'], obj['cat_name'], obj['cat_name_order'],
                                     cur_time, cur_time, tag, obj['money']]
                        compepitors.append(comp_info)
                        if index == 2:
                            break
            return dict(code=res.status_code, persons=persons, compepitors=compepitors)
        else:
            return dict(code=res.status_code, persons=persons, compepitors=compepitors)

    def deal_images(self, cdn, name):
        """
        logo 下载
        :param cdn: url
        :param name: 保存的名字
        :return: 保存的路径（结合web后台）
        """
        response = requests.get(cdn)
        data = response.content
        path = "logos/{}".format(name)
        save_path = 'D:/work/IFMS/media/' + path
        if not os.path.exists(save_path):
            with open(save_path, 'wb') as f:
                f.write(data)
        return path

    def insert_to_db(self, sql, data):
        """
        数据库 新增函数
        :param sql:
        :param data:
        :return:
        """
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

    def query_pro_id(self, project_name, company_name):
        """
        项目查询函数
        :param project_name:项目名称
        :param company_name:公司名称
        :return: None/tuple 示例(1,)
        """
        con = pymysql.Connect(
            host="localhost",
            user="root",
            database="develop",
            password="000000",
            charset="utf8",
            port=3306
        )
        cursor = con.cursor()
        sql = 'SELECT id FROM pro_base_info WHERE project_name="%s" AND company_name="%s"'\
              % (project_name, company_name)
        cursor.execute(sql)
        pro = cursor.fetchone()
        cursor.close()
        con.close()
        return pro

    def log(self, datas):
        """
        自定义日志记录（也可使用logging模块）
        :param datas:
        :return:
        """
        with open('./itjuzi/log.txt', 'a+', encoding="utf-8") as f:
            cur_time = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write("{}".format(cur_time) + datas + '\n')


def get_cookies(account="xxxxxxxx", password='xxxxx'):
        """
        模拟登陆获取token
        :param account: 账号
        :param password: 密码
        :return: 由cookie 和 构成的元组
        """
        browser = webdriver.Chrome('chromedriver.exe')
        browser.get('https://www.itjuzi.com/login?url=%2F')
        time.sleep(1)
        browser.find_element_by_name("account").send_keys(account)
        time.sleep(1)
        browser.find_element_by_name("password").send_keys(password)
        time.sleep(1)
        browser.find_element_by_tag_name('button').click()
        time.sleep(1)
        # token&cookies
        infos = browser.get_cookies()

        co = [item["name"] + "=" + item["value"] for item in infos]
        cookies = '; '.join(item for item in co)

        # token
        browser.close()
        for i in infos:
            if i['name'] == 'juzi_token':
                tok = i['value']
                break
        else:
            tok = ''
        result = (cookies, tok)
        return result


if __name__ == "__main__":

    payloadData = {
        'city': [],
        'com_fund_needs': "需要融资",
        'keyword': "",
        'location': "",
        'page': 1,
        'pagetotal': 0,
        'per_page': 20,
        'prov': "",
        'round': [],
        'scope': "",
        'selected': "",
        'sort': "",
        'status': "",
        'sub_scope': "",
        'total': 0,
        'year': [],
    }
    tup = get_cookies()
    start_page = 2150  # 起始页
    end_page = 2300  # 结束页
    count = 1
    while True:
        spider = Spider(payloadData, tup[1], tup[0], start_page)
        try:
            spider.get_contents()
        except Exception as e:
            print(e)
            break
        if not Spider.TAG:
            tup = get_cookies()
            count += 1
            if count >= 5:
                break
        else:
            start_page += 1
            if start_page >= end_page:
                break

