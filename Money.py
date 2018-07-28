# coding:utf-8
from flask import Flask, render_template, request, url_for
from flask_bootstrap import Bootstrap
from pyecharts import Bar

from urllib import request as req
import json
import psycopg2
from datetime import date, datetime
from bs4 import BeautifulSoup
import demjson


MONEY = 1000
RATE = 0.9985
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
history_symbols = []
DEFAULT_HOST = "https://pyecharts.github.io/assets/js"
app = Flask(__name__)
bootstrap = Bootstrap(app)

day = date.today().strftime("%Y%m%d")
conn = psycopg2.connect("dbname=postgres user=postgres password=88888888")
cur = conn.cursor()


def get_news_from_db(table_name):
    sql = "SELECT title, url FROM %s WHERE date='%s'" % (table_name, day)
    cur.execute(sql)
    rows = cur.fetchall()
    return rows


def get_hs300_from_db():
    sql = "SELECT symbol, name, trade, changepercent, settlement, amount, ticktime FROM hs300 WHERE date='%s' " \
          "ORDER BY amount DESC" % day
    cur.execute(sql)
    rows = cur.fetchall()
    return rows


def get_symbol_from_hs300(symbol):
    sql = "SELECT date, settlement, amount, rank, name FROM hs300 WHERE symbol='%s'" % symbol
    cur.execute(sql)
    rows = cur.fetchall()
    history_list = [[], [], [], []]
    for row in rows:
        history_list[0].append(row[0].strftime("%Y-%m-%d"))
        history_list[1].append(row[1])
        history_list[2].append(int(row[2]/10000))
        history_list[3].append(row[3])
    history_list.append(row[4])
    return history_list


def get_top_bill_symbol():
    sql = "SELECT symbol, name, SUM(volume), settlement FROM topbill WHERE date='%s' " \
          "GROUP BY (symbol, name, settlement) ORDER BY SUM(volume) DESC" % day
    cur.execute(sql)
    rows = cur.fetchall()
    return rows


def get_symbol_from_topbill(symbol):
    sql = "SELECT symbol, name, ticktime, price, volume, prev_price, kind, settlement, ratio_avg_volume_20 " \
          "FROM topbill WHERE symbol='%s' AND date='%s'" % (symbol, day)
    cur.execute(sql)
    rows = cur.fetchall()
    return rows


def store_top_bill():
    url = 'http://money.finance.sina.com.cn/d/api/openapi.php/CN_Bill.getBillTopListByDay'
    reqs= req.Request(url=url)
    response = req.urlopen(reqs, timeout=20)
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






def StoreHs300Data():
    url = 'http://money.finance.sina.com.cn/d/api/openapi_proxy.php/?__s=[["jjhq",1,300,"amount",0,"hs300"]]'
    reqs= req.Request(url=url)
    response = req.urlopen(reqs, timeout=20)
    result = response.read().decode('gbk')
    # print result
    data = json.loads(result[1:-1])
    fields = data['fields']
    items = data['items']
    table_name = 'hs300_' + day
    # table_name = 't501000'
    sql = "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename='%s'" % table_name
    cur.execute(sql)
    res =  cur.fetchone()
    if res:
        sql = "DROP TABLE %s" % table_name
        cur.execute(sql)
    sql = "CREATE TABLE %s (id serial PRIMARY KEY, symbol varchar, name varchar, trade real, pricechange real, changepercent real, buy real, sell real, settlement real, open real, high real, low real, volume bigint, amount bigint, code varchar, ticktime time, focus varchar, fund varchar)" % table_name
    cur.execute(sql)

    for item in data['items']:
        sql = "INSERT INTO %s (symbol, name, trade, pricechange, changepercent, buy, sell, settlement, open, high, low, volume, amount, code, ticktime, focus, fund) VALUES ('%s', '%s', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, '%s', '%s', '%s', '%s')"\
              % ((table_name, ) + tuple(item))
        # print sql
        cur.execute(sql)
    conn.commit()
# def get_top_bill_all(table_name):
#     sql = "SELECT symbol, name, ticktime, price, volume, prev_price, kind, settlement, ratio_avg_volume_20 FROM %s" % table_name
#     cur.execute(sql)
#     rows = cur.fetchall()
#     return rows







def HandleSymbolList(symbol_list):
    total_list = [[], [], []]
    kind_list = ['U', 'D', 'E']
    for item in symbol_list:
        ticktime = date.today().strftime("%Y-%m-%d ") + item[2].strftime("%H:%M:%S")
        price = round((item[3] - item[7]) / item[7] * 100, 2)
        volume = item[4]
        total_list[kind_list.index(item[6])].append([ticktime, price, volume])
    return total_list



def DateFormat(table_name,start):
    year = table_name[start:start+4]
    month = table_name[start+4:start+6]
    day = table_name[start+6:]
    return '%s-%s-%s' % (year, month, day)


def HandleSymbolHistory(symbol):
    sql = "SELECT date, volume, kind_u, kind_d, kind_e, rank FROM topbill_history WHERE symbol='%s'" % symbol
    cur.execute(sql)
    rows = cur.fetchall()
    history_list = [[], [], [], [], [], []]
    for row in rows:
        history_list[0].append(row[0].strftime("%Y-%m-%d"))
        history_list[1].append(int(row[1] / 10000))
        history_list[2].append(int(row[2] / 10000))
        history_list[3].append(int(row[3] / 10000))
        history_list[4].append(int(row[4] / 10000))
        history_list[5].append(row[5])
    return history_list

def get_finance_top_sina():
    url = 'http://top.finance.sina.com.cn/ws/GetTopDataList.php?top_type=day&top_cat=finance_0_suda&top_time='+ day +'&top_show_num=20&top_order=DESC'
    # print url
    reqs= req.Request(url=url)
    response = req.urlopen(reqs, timeout=20)
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
    reqs= req.Request(url=url)
    response = req.urlopen(reqs, timeout=20)
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
        reqs = req.Request(url=url)
        response = req.urlopen(reqs, timeout=20)
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
        if page * 20 >= total_num:
            break
        page += 1
    conn.commit()


def GetFundData(symbol):
    sql = "SELECT tdate,value FROM t%s ORDER BY tdate DESC LIMIT 300" % symbol
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


def eBarRate(week_list):
    attrs = []
    values = []
    for item in week_list:
        attrs.append(item[0])
        values.append(item[3])
    bar = Bar("定投回报")
    bar.add("回报率", attrs, values, mark_point=["max", "min"])
    return bar


def GetSymbolList():
    symbol_list = []
    url = "http://vip.stock.finance.sina.com.cn/fund_center/api/jsonp.php/IO.XSRV2.CallbackList['Il$nvMbY72HdQyks']/NetValueReturn_Service.NetValueReturnOpen?page=1&num=100&sort=form_year&asc=0&ccode=&type2=0&type3=&%5Bobject%20HTMLDivElement%5D=546oa"
    reqs= req.Request(url=url)
    response = req.urlopen(reqs, timeout=20)
    result = response.read().decode('gbk')

    startPos = result.find('{')
    jsonData = result[startPos:-2]
    jsonData = jsonData
    data = demjson.decode(jsonData)['data']
    for item in data:
        symbol_list.append(str(item['symbol']))

    #symbol_list.remove('000970')

    return symbol_list


def HandleWeekList(week_list):
    rate_list = []
    rate_list = []
    for item in week_list:
        rate_list.append(item[3])
    return rate_list.index(max(rate_list)),rate_list.index(min(rate_list))


def FundStatistic(symbol_list):
    best_count_list = [0]*5
    worst_count_list = [0] * 5
    for symbol in symbol_list:
        # print symbol
        StoreFundData(symbol)
        week_list = CalcFundByWeek(symbol)
        max_weekday,min_weekday = HandleWeekList(week_list)
        best_count_list[max_weekday] += 1
        worst_count_list[min_weekday] += 1
    return best_count_list, worst_count_list


def eBarCount(best_count_list, worst_count_list):
    attrs = WEEKDAYS[:5]
    bar = Bar("定投回报最佳日统计")
    bar.add("最优次数", attrs, best_count_list, mark_point=["max", "min"])
    bar.add("最差次数", attrs, worst_count_list, mark_point=["max", "min"])
    return bar


@app.route('/')
def News():
    sina_list = get_news_from_db("sina_news")[:20]
    ntes_list = get_news_from_db("nets_news")[:20]
    return render_template('index.html', sina_list=sina_list, ntes_list=ntes_list)


@app.route('/hs300')
def HS300():
    hs_list = get_hs300_from_db()
    return render_template('hs300.html', hs_list=hs_list)


@app.route('/hs300/<symbol>')
def HS300Symbol(symbol):
    history_list = get_symbol_from_hs300(symbol)
    return render_template('hssymbol.html', symbol=symbol, history_list=history_list)


@app.route('/tb')
def TopBill():
    bill_list = get_top_bill_symbol()
    # print bill_list
    return render_template('top_bill.html', bill_list=bill_list)


@app.route('/tb/<symbol>')
def ShowSymbol(symbol):
    symbol_list = get_symbol_from_topbill(symbol)
    total_list = HandleSymbolList(symbol_list)
    history_list = HandleSymbolHistory(symbol)
    print(history_list)
    return render_template('symbol.html', symbol_list=symbol_list, total_list=total_list, history_list=history_list)


@app.route('/fund', methods=['GET', 'POST'])
def Fund():
    week_list = []
    symbol = ''
    if request.method == 'POST':
        symbol = request.form['symbol']
    elif 'symbol' in request.args:
        symbol = request.args['symbol']
    if symbol != '':
        if symbol not in history_symbols:
            StoreFundData(symbol)
            history_symbols.append(symbol)
        week_list = CalcFundByWeek(symbol)
    bar = eBarRate(week_list)
    return render_template('fund.html',
                           symbol=symbol,
                           week_list=week_list,
                           history_symbols=history_symbols,
                           bar=bar.render_embed(),
                           host=DEFAULT_HOST,
                           script_list=['echarts.min'])


@app.route('/fundsta')
def FundTopSta():
    symbol_list = GetSymbolList()
    best_count_list, worst_count_list = FundStatistic(symbol_list)
    bar = eBarCount(best_count_list, worst_count_list)
    return render_template('fundsta.html',
                           bar=bar.render_embed(),
                           host=DEFAULT_HOST,
                           script_list=['echarts.min'])


if __name__ == '__main__':
    app.run(debug=True)
    cur.close()
    conn.close()

