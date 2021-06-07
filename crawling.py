import pymysql
import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
import os
import logging

#logging
log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='crawling.log', level=logging.DEBUG, format=log_format)

conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock',user='root', passwd=os.environ['mysql_password'], db='mysql')

cur = conn.cursor()
cur.execute("USE shop")
cur.execute("SELECT id, url FROM variations where has_stock = 1")
rows = cur.fetchall()
print(cur.rowcount)
for row in rows:
    res = requests.get(row[1])
    try:
        res.raise_for_status()
    except Exception as e:
        logging.warning("There was a problem: %s %s", e, row[1])
    else:
        html = urlopen(row[1])
        bsObj = BeautifulSoup(html, 'lxml')
        txt_availability = ''
        unavailable = bsObj.find("div", {"class":"product_retirement-unavailable_text"})
        if unavailable:
            txt_availability = 'Unavailable'
            logging.warning("Unavailable: %s", row[1])
        else:
            availability = bsObj.find("span", {"class":"pdp-availability_badge"})
            if availability:
                txt_availability = availability.get_text().strip()
                if txt_availability == '':
                    txt_availability = 'OUT OF STOCK'
                    logging.warning("Check stock: %s", row[1])
            else:
                txt_availability = 'No Content'
                logging.warning("No availability info: %s", row[1])
            size = bsObj.find("div", {"class":{"selected-size"}}).get_text().strip()
            if size == "Select Size":
                availability = 'OUT OF STOCK'
                logging.warning("Check stock: %s at %s", row[0], row[1])
                size = bsObj.find("span", {"class":{"size-value"}}).get_text().strip()
        id = str(row[0])
        sql = "UPDATE variations SET availability = '" + txt_availability + "' WHERE id = '" + id + "'"

        cur.execute(sql)
        conn.commit()

cur.close()
conn.close()
