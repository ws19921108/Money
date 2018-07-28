import psycopg2
conn = psycopg2.connect("dbname=postgres user=postgres password=88888888")
cur = conn.cursor()


def create_news_table(table_name):
    sql = "CREATE TABLE %s (id serial PRIMARY KEY, title varchar, url varchar, date date)" \
          % table_name
    cur.execute(sql)
    conn.commit()


def create_hs300_table():
    sql = "CREATE TABLE hs300 (id serial PRIMARY KEY, symbol varchar, name varchar, trade real, pricechange real, " \
          "changepercent real, buy real, sell real, settlement real, open real, high real, low real, volume bigint, " \
          "amount bigint, code varchar, ticktime time, focus varchar, fund varchar, date date, rank smallint)"
    cur.execute(sql)
    conn.commit()


def create_top_bill_table():
    sql = "CREATE TABLE topbill (id serial PRIMARY KEY, symbol varchar, name varchar, ticktime time, price real, " \
          "volume integer, prev_price real, kind varchar, settlement real, ratio_avg_volume_20 integer, date date)"
    cur.execute(sql)
    conn.commit()


def create_top_bill_history_table():
    sql = "CREATE TABLE topbill_history (id serial PRIMARY KEY, symbol varchar, name varchar, volume integer, " \
          "kind_u integer, kind_d integer, kind_e integer, settlement real, rank smallint,date date)"
    cur.execute(sql)
    conn.commit()


def create_fund_list_table():
    sql = "CREATE TABLE fund_list (id serial PRIMARY KEY, symbol varchar, sname varchar, per_nav real, " \
          "total_nav real, three_month real, six_month real, one_year real, form_year real, form_start real, " \
          "name varchar, zmjgm varchar, clrq date, jjjl varchar, dwjz real, ljjz real, jzrq date, zjzfe INTEGER, " \
          "jjglr_code varchar)"
    cur.execute(sql)
    conn.commit()


def has_table(table_name):
    sql = "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename='%s'" % table_name
    cur.execute(sql)
    res = cur.fetchone()
    return res


def truncate_table(table_name):
    sql = "TRUNCATE TABLE %s" % table_name
    cur.execute(sql)
    conn.commit()


table_name = "sina_news"
if has_table(table_name):
    truncate_table(table_name)
else:
    create_news_table(table_name)

table_name = "nets_news"
if has_table(table_name):
    truncate_table(table_name)
else:
    create_news_table(table_name)

table_name = "hs300"
if has_table(table_name):
    truncate_table(table_name)
else:
    create_hs300_table()

table_name = "topbill"
if has_table(table_name):
    truncate_table(table_name)
else:
    create_top_bill_table()

table_name = "topbill_history"
if has_table(table_name):
    truncate_table(table_name)
else:
    create_top_bill_history_table()

table_name = "fund_list"
if has_table(table_name):
    truncate_table(table_name)
else:
    create_fund_list_table()

cur.close()
conn.close()
