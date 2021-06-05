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

cur = conn.cursor()
cur.execute("USE shop")
cur.execute("SELECT id, item_id, url FROM variations where has_stock = 0 and availability != 'unavailable'")
rows = cur.fetchall()
print(cur.rowcount)
for row in rows:
    res = requests.get(row[2])
    try:
        res.raise_for_status()
    except Exception as e:
        logging.warning("There was a problem: %s %s", e, row[2])
    else:
        html = urlopen(row[2])
        bsObj = BeautifulSoup(html, 'lxml')
        txt_availability = ''
        size_new = ''
        unavailable = bsObj.find("div", {"class":"product_retirement-unavailable_text"})
        if unavailable:
            txt_availability = 'Unavailable'
            # logging.warning("Unavailable: %s", row[2])
        else:
            availability = bsObj.find("span", {"class":"pdp-availability_badge"})
            if availability:
                txt_availability = availability.get_text().strip()
                if txt_availability == '':
                    txt_availability = 'OUT OF STOCK'
                    # logging.warning("Check stock: %s", row[2])
                elif txt_availability == 'In Stock' or txt_availability == 'Low in Stock':
                    logging.warning("Item: %s, variation: %s is back. %s", row[0], row[1], row[2])
            else:
                txt_availability = 'No Content'
                # logging.warning("No availability info: %s", row[2])
            size = bsObj.find("div", {"class":{"selected-size"}}).get_text().strip()
            if size == "Select Size":
                availability = 'OUT OF STOCK'
            else:
                size_new = size
                # logging.warning("Check stock: %s at %s", row[0], row[2])
        id = str(row[0])
        sql = "UPDATE variations SET availability = '" + txt_availability + "' WHERE id = '" + id + "'"
        cur.execute(sql)
        if len(size_new) > 0:
            sql = "UPDATE variations SET size_name = '" + size_new + "' WHERE id = '" + id + "'"
            cur.execute(sql)
        conn.commit()

cur.close()
conn.close()
