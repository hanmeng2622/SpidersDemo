import os
import re
import uuid

from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import psycopg2


class LogScript:
    """将日志文件数据逐行添加至数据库"""

    def __init__(self, log_path):
        self.log_path = log_path

        self.sql = "insert into test_chinare_data_center.system_status_code_record_nginx (id, status_code, " \
                   "code_nums, now_date) values (%s,%s,%s,%s);"
        # self.sql = "insert into system_status_code_record_nginx (id, status_code, " \
        #            "code_nums, now_date) values (%s,%s,%s,%s);"

    def write_to_db(self, _sql, _datas):
        """写入数据库"""
        conn = psycopg2.connect(
            database="test",
            user="root",
            password="000000",
            host="127.0.0.1",
            port="3306")
        cursor = conn.cursor()

        for data in _datas:
            try:
                cursor.execute(_sql, data)
                conn.commit()
            except Exception as error:
                conn.rollback()
                print(error)
        cursor.close()
        conn.close()

    def read_log_file(self, path):
        """打开文件并处理数据"""
        status_codes = []
        all_data = []
        with open(path, 'r') as file:
            _lines = file.readlines()
            for line in _lines:
                _line = line.split(' ')
                code = _line[-2]
                if len(code) > 3:
                    continue
                status_codes.append(code)
        counter = dict(Counter(status_codes))

        res = re.match(r'.*\_(\d+)\_.*', path)
        _date = res.group(1)
        now_date = self.deal_date(_date)

        for item in counter.items():
            all_data.append([str(uuid.uuid4()), item[0], item[1], now_date])
        self.write_to_db(self.sql, all_data)
        print("{path} 文件数据加载数据库成功".format(path=self.log_path))

    def deal_date(self, date):
        """
        取一年中每一天的后一天
        :param date:"20200607"
        :return:
        """
        if date[4:] == '0131':
            next_date = date[:4] + '0201'
        elif date[4:] == '0228' or date[4:] == '0229':
            if date[4:] == '0228' and (int(date[:4]) % 4 == 0 and int(
                    date[:4]) % 400 == 0 or int(date[:4]) % 4 == 0 and int(date[:4]) % 100 != 0):
                next_date = date[:4] + '0229'
            else:
                next_date = date[:4] + '0301'
        elif date[4:] == '0331':
            next_date = date[:4] + '0401'
        elif date[4:] == '0430':
            next_date = date[:4] + '0501'
        elif date[4:] == '0531':
            next_date = date[:4] + '0601'
        elif date[4:] == '0630':
            next_date = date[:4] + '0701'
        elif date[4:] == '0731':
            next_date = date[:4] + '0801'
        elif date[4:] == '0831':
            next_date = date[:4] + '0901'
        elif date[4:] == '0930':
            next_date = date[:4] + '1001'
        elif date[4:] == '1031':
            next_date = date[:4] + '1101'
        elif date[4:] == '1130':
            next_date = date[:4] + '1201'
        elif date[4:] == '1231':
            next_date = date[:4] + '0101'
        else:
            next_date = str(int(date) + 1)
        return next_date

    def run(self):
        """启动流程"""
        self.read_log_file(self.log_path)


# 列表承载文件路径
path_list = []


def get_path(_dir):
    """
    递归获取一个目标目录下的所有文件
    :param _dir:
    :return:
    """
    dir_list = os.listdir(_dir)
    # if 'err' in dir_list:
    #     dir_list.remove('err')
    # if 'error' in dir_list:
    #     dir_list.remove('error')

    for i in dir_list:
        sub_dir = os.path.join(_dir, i)
        if os.path.isdir(sub_dir):
            get_path(sub_dir)
        else:
            path_list.append(sub_dir)


def run(path):
    """
    线程池启动函数
    :param path:
    :return:
    """
    LogScript(path).run()


if __name__ == "__main__":

    thread_pool = ThreadPoolExecutor(4)
    get_path(r'D:\Data\data')
    for path in path_list:
        try:
            thread_pool.submit(run, path)
        except Exception as err:
            with open("error.txt", 'w+') as f:
                f.write(path)
                f.write(err)
