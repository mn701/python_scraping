import pymysql
import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
import os
import logging

#logging
log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='crawling_rev.log', level=logging.DEBUG, format=log_format)

pw = os.environ.get('mysql_password')
conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock',user='root', passwd=pw, db='mysql')

cur = conn.cursor(pymysql.cursors.DictCursor)
cur.execute("USE shop")
cur.execute("SELECT * From Items WHERE listed IN (3, 4)")
rows = cur.fetchall()
print(cur.rowcount)
for row in rows:
    cur.execute("SELECT * From Variations WHERE item_id = " + str(row['item_id']) + " order by color_code")
    varrows = cur.fetchall()
    counter = 0
    for variation in varrows:
        counter += 1
        sql = "UPDATE variations SET bm_order = '" + str(counter) + "' WHERE id = '" + str(variation['id']) + "'"
        cur.execute(sql)
        conn.commit()

cur.close()
conn.close()
