from urllib import request as req
from bs4 import BeautifulSoup
from datetime import date
import json
import psycopg2
import demjson


conn = psycopg2.connect("dbname=postgres user=postgres password=88888888")
cur = conn.cursor()
day = date.today().strftime("%Y%m%d")


def add_news_to_db(item, table_name):
    url = item[1]
    sql = "SELECT * FROM %s WHERE url='%s'" % (table_name, url)
    cur.execute(sql)
    res = cur.fetchone()
    if not res:
        sql = "INSERT INTO %s (title, url, date) VALUES ('%s', '%s', '%s')"\
              % ((table_name,) + tuple(item))
        cur.execute(sql)
    conn.commit()


def get_finance_top_sina():
    url = 'http://top.finance.sina.com.cn/ws/GetTopDataList.php?top_type=day&top_cat=finance_0_suda&top_time='\
          + day + '&top_show_num=20&top_order=DESC'
    # print url
    reqs = req.Request(url=url)
    response = req.urlopen(reqs, timeout=20)
    result = response.read()
    # print result[11:-2]
    data = json.loads(result[11:-2])['data']
    for item in data:
        cdate = item['create_date']
        url = item['url']
        title = item['title'].replace('"', '\"')
        add_news_to_db([title, url, cdate], "sina_news")
    conn.commit()


def get_finance_top_ntes():
    url = 'http://money.163.com/special/002526BH/rank.html'
    reqs = req.Request(url=url)
    response = req.urlopen(reqs, timeout=20)
    result = response.read().decode('gbk')
    soup = BeautifulSoup(result, "html.parser")
    content = soup.find('div', {"class": "area-half left"}).div.contents[3]
    data = content.find_all('a')[:20]
    for item in data:
        url = item['href']
        cdate = day
        title = item.text
        add_news_to_db([title, url, cdate], "nets_news")
    conn.commit()


def get_hs300():
    url = 'http://money.finance.sina.com.cn/d/api/openapi_proxy.php/?__s=[["jjhq",1,300,"amount",0,"hs300"]]'
    reqs = req.Request(url=url)
    response = req.urlopen(reqs, timeout=20)
    result = response.read().decode('gbk')
    # print result
    data = json.loads(result[1:-1])
    items = data['items']
    index = 0
    for item in items:
        index += 1
        sql = "SELECT * FROM hs300 WHERE symbol='%s' AND date='%s'" % (item[0], day)
        cur.execute(sql)
        res = cur.fetchone()
        if res:
            sql = "UPDATE hs300 SET trade = %s, pricechange = %s, changepercent = %s, buy = %s, sell = %s," \
                  " settlement = %s, open = %s, high = %s, low = %s, volume = %s, amount = %s, code =  '%s'," \
                  " ticktime =  '%s', rank = %s WHERE symbol='%s' AND date='%s'" % (tuple(item[2:-2]) + (index, item[0], day))
            cur.execute(sql)
        else:
            item.append(day)
            item.append(index)
            sql = "INSERT INTO hs300 (symbol, name, trade, pricechange, changepercent, buy, sell, settlement," \
                  " open, high, low, volume, amount, code, ticktime, focus, fund,date, rank) VALUES " \
                  "('%s', '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '%s', '%s', '%s', '%s', '%s', %s)"\
                  % tuple(item)
            cur.execute(sql)
    conn.commit()


def get_top_bill():
    url = 'http://money.finance.sina.com.cn/d/api/openapi.php/CN_Bill.getBillTopListByDay'
    reqs = req.Request(url=url)
    response = req.urlopen(reqs, timeout=20)
    result = response.read().decode('gbk')
    # print result
    data = json.loads(result)['result']['data']
    items = data['items']

    sql = "DELETE FROM topbill WHERE date='%s'" % day
    cur.execute(sql)

    for item in items:
        sql = "INSERT INTO topbill (symbol, name, ticktime, price, volume, prev_price, kind, settlement," \
              " ratio_avg_volume_20, date) VALUES ('%s', '%s',  '%s', %s, %s, %s, '%s', %s, %s, '%s')"\
              % (tuple(item) + (day,))
        cur.execute(sql)
    conn.commit()


def get_top_bill_history():
    sql = "SELECT symbol, name, settlement, SUM(volume), rank() over(order by SUM(volume) desc)rank FROM topbill " \
          "WHERE date='%s' GROUP BY symbol, settlement, name" % day
    cur.execute(sql)
    rows = cur.fetchall()
    for row in rows:
        sql = "SELECT kind, SUM(volume) FROM topbill WHERE symbol='%s' AND date='%s' GROUP BY kind" % (row[0], day)
        cur.execute(sql)
        kind_rows = cur.fetchall()
        kind_list = [0, 0, 0]
        kinds = ['U', 'D', 'E']
        for (k, v) in dict(kind_rows).items():
            kind_list[kinds.index(k)] = v

        temp = list(row) + kind_list
        sql = "SELECT * FROM topbill_history WHERE symbol='%s' AND date='%s'" % (row[0], day)
        cur.execute(sql)
        res = cur.fetchone()
        if res:
            sql = "UPDATE topbill_history SET settlement = %s, volume = %s, rank = %s, kind_u = %s, kind_d = %s, " \
                  "kind_e = %s WHERE symbol='%s' AND date='%s'" % (tuple(temp[2:]) + (row[0], day))
            cur.execute(sql)
        else:
            temp.append(day)
            sql = "INSERT INTO topbill_history (symbol, name, settlement, volume, rank, kind_u, kind_d, kind_e, " \
                  "date) VALUES ('%s', '%s', %s, %s, %s, %s, %s, %s, '%s')" % tuple(temp)
            cur.execute(sql)
        conn.commit()


def get_funds():
    symbol_list = []
    url = "http://vip.stock.finance.sina.com.cn/fund_center/api/jsonp.php/IO.XSRV2.CallbackList['Il$nvMbY72HdQyks']" \
          "/NetValueReturn_Service.NetValueReturnOpen?page=1&num=100&sort=form_year&asc=0&ccode=&type2=0&" \
          "type3=&%5Bobject%20HTMLDivElement%5D=546oa"
    reqs = req.Request(url=url)
    response = req.urlopen(reqs, timeout=20)
    result = response.read().decode('gbk')

    startPos = result.find('{')
    jsonData = result[startPos:-2]
    jsonData = jsonData
    data = demjson.decode(jsonData)['data']
    for item in data:
        for (k, v) in item.items():
            pass



get_finance_top_sina()
get_finance_top_ntes()
get_hs300()
get_top_bill()
get_top_bill_history()

get_funds()

cur.close()
conn.close()
