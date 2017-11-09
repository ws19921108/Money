#coding:utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
# from pyecharts import Scatter3D
# from pyecharts.constants import DEFAULT_HOST
import urllib2
import json
import psycopg2
from datetime import date
from bs4 import BeautifulSoup


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
    if request.method == 'POST':
        print request.form['symbol']
    return render_template('fund.html')

if __name__ == '__main__':
    app.run()
    cur.close()
    conn.close()