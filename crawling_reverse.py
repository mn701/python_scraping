import pymysql
import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
import os
import logging
from classes.utilities import *

#logging
log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='crawling_rev.log', level=logging.DEBUG, format=log_format)

crawler = Crawler()
dbc = DBHelper()
sql = "SELECT id, item_id, url FROM variations where has_stock = 0 and availability != 'unavailable'"
rows = dbc.fetchall(sql)
print(dbc.rowcount(sql))
for row in rows:
    bsObj = crawler.getPage(row['url'])
    txt_availability = ''
    size_new = ''
    unavailable = crawler.safeGet(bsObj, 'div.product_retirement-unavailable_text')
    if unavailable:
        txt_availability = 'Unavailable'
        # logging.warning("Unavailable: %s", row[2])
    else:
        span_availability = bsObj.find("span", {"class":"pdp-availability_badge"})
        if span_availability:
            txt_availability = crawler.safeGet(bsObj, 'span.pdp-availability_badge')
            if txt_availability == '':
                txt_availability = 'OUT OF STOCK'
                # logging.warning("Check stock: %s", row[2])
            elif txt_availability == 'In Stock' or txt_availability == 'Low in Stock':
                logging.warning("Item: %s, variation: %s is back. %s", row['item_id'], row['id'], row['url'])
        else:
            txt_availability = 'No Content'
            # logging.warning("No availability info: %s", row[2])

        size = crawler.safeGet(bsObj, 'div.selected-size')
        size = re.sub(r' - Unavailable', '', size)
        if size == "Select Size":
            availability = 'OUT OF STOCK'
            size_span = bsObj.find("span", {"class":"size-value"})
            if size_span:
                size = crawler.safeGet(bsObj, 'span.size-value')
        else:
            size_new = size
            # logging.warning("Check stock: %s at %s", row[0], row[2])
    id = str(row['id'])
    sql = "UPDATE variations SET availability = '" + txt_availability + "' WHERE id = '" + id + "'"
    dbc.execute(sql)
    if len(size_new) > 0:
        sql = "UPDATE variations SET size_name = '" + size_new + "' WHERE id = '" + id + "'"
        dbc.execute(sql)
