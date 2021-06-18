import pymysql
import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
import os
import logging
from classes.utilities import *


crawler = Crawler()
dbc = DBHelper()

logging
log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='log/crawling.log', level=logging.DEBUG, format=log_format)

sql = "SELECT id, url FROM variations where has_stock = 1"
rows = dbc.fetchall(sql)
print(dbc.rowcount(sql))
for row in rows:
    bsObj = crawler.getPage(row['url'])

    if bsObj is None:
        print("bsObj is None", row['url'])

    txt_availability = ''
    unavailable = crawler.safeGet(bsObj, 'div.product_retirement-unavailable_text')
    if unavailable:
        txt_availability = 'Unavailable'
        logging.warning("Unavailable: %s", row['url'])
    else:
        span_availability = bsObj.find("span", {"class":"pdp-availability_badge"})
        if span_availability:
            txt_availability = crawler.safeGet(bsObj, 'span.pdp-availability_badge')
            if txt_availability == '':
                txt_availability = 'OUT OF STOCK'
                logging.warning("Check stock: %s", row['url'])
        else:
            txt_availability = 'No Content'
            logging.warning("No availability info: %s", row['url'])

        size = crawler.safeGet(bsObj, 'div.selected-size')
        if re.match(r' - Unavailable', size) or size == "Select Size":
            txt_availability = 'OUT OF STOCK'
            logging.warning("Check stock: %s at %s", row['id'], row['url'])
            size = re.sub(r' - Unavailable', '', size)
            size_span = bsObj.find("span", {"class":"size-value"})
            if size_span:
                size = crawler.safeGet(bsObj, 'span.size-value')

        id = str(row['id'])
        sql = "UPDATE variations SET availability = '" + txt_availability + "' WHERE id = '" + id + "'"
        dbc.execute(sql)
