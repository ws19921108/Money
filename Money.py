#coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from pyecharts import Bar
from pyecharts.constants import DEFAULT_HOST
import urllib2
import json
import psycopg2
from datetime import date
from bs4 import BeautifulSoup

MONEY = 1000
RATE = 0.9985
WEEKDAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
symbol_list = []


app = Flask(__name__)
bootstrap = Bootstrap(app)
conn = psycopg2.connect("dbname=postgres user=postgres")
cur = conn.cursor()
day = date.today().strftime("%Y%m%d")

def store_top_bill():
    url = 'http://money.finance.sina.com.cn/d/api/openapi.php/CN_Bill.getBillTopListByDay'
    request = urllib2.Request(url=url)
    response = urllib2.urlopen(request, timeout=20)
    result = response.read().decode('gbk')
    # print result
    data = json.loads(result)['result']['data']
    fields = data['fields']
    table_name = 'top_bill' + day
    # table_name = 't501000'
    sql = "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename='%s'" % table_name
    cur.execute(sql)
    res =  cur.fetchone()
    if res:
        sql = "DROP TABLE %s" % table_name
        cur.execute(sql)
    sql = "CREATE TABLE %s (id serial PRIMARY KEY, symbol varchar, name varchar, ticktime time, price real, volume integer, prev_price real, kind varchar, settlement real, ratio_avg_volume_20 integer)" \
          % table_name
    cur.execute(sql)

    for item in data['items']:
        sql = "INSERT INTO %s (symbol, name, ticktime, price, volume, prev_price, kind, settlement, ratio_avg_volume_20) VALUES ('%s', '%s',  '%s', %s, %s, %s, '%s', %s, %s)"\
              % ((table_name,) + tuple(item))
        cur.execute(sql)
    conn.commit()

# def get_top_bill_all(table_name):
#     sql = "SELECT symbol, name, ticktime, price, volume, prev_price, kind, settlement, ratio_avg_volume_20 FROM %s" % table_name
#     cur.execute(sql)
#     rows = cur.fetchall()
#     return rows

def get_top_bill_symbol(table_name):
    sql = "SELECT symbol, name, SUM(volume), settlement FROM %s GROUP BY (symbol, name, settlement) ORDER BY SUM(volume) DESC" % table_name
    cur.execute(sql)
    rows = cur.fetchall()
    return rows

def get_top_bill_by_symbol(table_name, symbol):
    sql = "SELECT symbol, name, ticktime, price, volume, prev_price, kind, settlement, ratio_avg_volume_20 FROM %s WHERE symbol='%s'" % (table_name, symbol)
    cur.execute(sql)
    rows = cur.fetchall()
    return rows

def get_finance_top_sina():
    url = 'http://top.finance.sina.com.cn/ws/GetTopDataList.php?top_type=day&top_cat=finance_0_suda&top_time='+ day +'&top_show_num=20&top_order=DESC'
    # print url
    request = urllib2.Request(url=url)
    response = urllib2.urlopen(request, timeout=20)
    result = response.read()
    # print result[11:-2]
    data = json.loads(result[11:-2])['data']
    sina_list = []
    for item in data:
        cdate = item['create_date']
        ctime = item['create_time']
        url = item['url']
        title = item['title']
        sina_list.append((title,url,cdate,ctime))
    return sina_list

def get_finance_top_ntes():
    url = 'http://money.163.com/special/002526BH/rank.html'
    request = urllib2.Request(url=url)
    response = urllib2.urlopen(request, timeout=20)
    result = response.read().decode('gbk')
    soup = BeautifulSoup(result, "html.parser")
    content = soup.find('div', { "class" : "area-half left" }).div.contents[3]
    data = content.find_all('a')
    ntes_list = []
    for item in data:
        title = item['title']
        url = item['href']
        ntes_list.append((title,url))

    return ntes_list[:20]


def StoreFundData(symbol):

    sql = "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename='t%s'" % symbol
    cur.execute(sql)
    res = cur.fetchone()
    if res:
        sql = "DROP TABLE t%s" % symbol
        cur.execute(sql)
    sql = "CREATE TABLE t%s (id serial PRIMARY KEY, tdate date, value real)" \
          % symbol
    cur.execute(sql)

    page = 1
    total_num = -1
    while True:
        url = 'http://stock.finance.sina.com.cn/fundInfo/api/openapi.php/CaihuiFundInfoService.getNav?symbol=' + symbol + '&page=' + str(
            page)
        request = urllib2.Request(url=url)
        response = urllib2.urlopen(request, timeout=20)
        result = response.read()
        result = json.loads(result)['result']
        if total_num < 0:
            total_num = int(result['data']['total_num'])
            # print total_num
        data = result['data']['data']
        if len(data) > 20:
            data.pop(-1)
        for item in data:
            tdate = item['fbrq'].split()[0]
            value = item['jjjz']
            sql = "INSERT INTO t%s (tdate, value) VALUES ('%s', %s)" % (symbol, tdate, value)
            # print sql
            cur.execute(sql)
        if page * 20 > total_num:
            break
        page += 1
    conn.commit()

def GetFundData(symbol):
    sql = "SELECT tdate,value FROM t%s ORDER BY tdate DESC LIMIT 500" % symbol
    cur.execute(sql)
    rows = cur.fetchall()
    return rows

def GetLatestPrice(symbol):
    sql = "SELECT value FROM t%s WHERE id=1" % symbol
    cur.execute(sql)
    rows = cur.fetchone()
    return rows[0]

def OrderFundByWeekday(symbol,weekday):
    count = 0
    fund_num = 0
    latest = GetFundData(symbol)
    for item in latest:
        if weekday == item[0].weekday():
            count += 1
            fund_num += MONEY * RATE / item[1]
    return count, fund_num

def CalcFundByWeek(symbol):
    week_list = []
    latest_price = GetLatestPrice(symbol)
    for weekday in range(5):
        count, fund_num = OrderFundByWeekday(symbol,weekday)
        money_sum = count * MONEY
        money_value = latest_price * fund_num
        money_value = round(money_value, 2)
        return_rate = (money_value-money_sum)/money_sum
        return_rate = round(return_rate,4)
        week_list.append((WEEKDAYS[weekday], money_sum,money_value,return_rate))
    return week_list

def eBar(week_list):
    attrs = []
    values = []
    for item in week_list:
        attrs.append(item[0])
        values.append(item[3])
    bar = Bar("定投回报")
    bar.add("回报率", attrs, values, mark_point=["max", "min"])
    return bar


@app.route('/')
def News():
    sina_list = get_finance_top_sina()
    ntes_list = get_finance_top_ntes()
    return render_template('index.html', sina_list=sina_list, ntes_list=ntes_list)

@app.route('/tb')
def TopBill():
    store_top_bill()
    table_name = 'top_bill' + day
    bill_list = get_top_bill_symbol(table_name)
    # print bill_list
    return render_template('top_bill.html', bill_list=bill_list)

@app.route('/tb/<symbol>')
def ShowSymbol(symbol):
    table_name = 'top_bill' + day
    symbol_list = get_top_bill_by_symbol(table_name, symbol)
    return render_template('symbol.html', symbol_list=symbol_list)

@app.route('/fund', methods=['GET', 'POST'])
def Fund():
    week_list = []
    symbol = ''
    if request.method == 'POST':
        symbol = request.form['symbol']
    elif 'symbol' in request.args:
        symbol = request.args['symbol']
    if symbol != '':
        if symbol not in symbol_list:
            StoreFundData(symbol)
            symbol_list.append(symbol)
        week_list = CalcFundByWeek(symbol)
    bar = eBar(week_list)
    return render_template('fund.html',
                           symbol=symbol,
                           week_list=week_list,
                           symbol_list=symbol_list,
                           bar=bar.render_embed(),
                           host=DEFAULT_HOST,
                           script_list=['echarts.min'])

if __name__ == '__main__':
    app.run()
    cur.close()
    conn.close()