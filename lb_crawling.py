import pymysql
import requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
import os
import logging
import json
from classes.utilities import *

#logging
log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='lb_crawling.log', level=logging.DEBUG, format=log_format)

crawler = Crawler()
dbc = DBHelper()
sql = "SELECT item_id, url FROM Items WHERE Items.brand_id = 3"
rows = dbc.fetchall(sql)
print(dbc.rowcount(sql))
for row in rows:
    bsObj = crawler.getPage(row['url'])

    availability = 'OUT OF STOCK'
    has_stock = 0

    script_string = ''
    magento_scripts = bsObj.find_all("script", {"type":{"text/x-magento-init"}})
    for script in magento_scripts:
        if '[data-role=swatch-options]' in script.string:
            script_string = script.string

    loadedjson = json.loads(script_string)
    jsonConfig = loadedjson['[data-role=swatch-options]']['Magento_Swatches/js/swatch-renderer']['jsonConfig']

    index = jsonConfig['index']

    # key in index is each prod
    for key in index:
        prod_id = key
        salable_qty = index[key]['lb_salable_qty']

        if int(salable_qty) > 0:
            has_stock = 1
            if int(salable_qty) < 50:
                availability = 'Low in Stock'
            else:
                availability = 'In Stock'

        sql = "UPDATE variations SET has_stock = " + str(has_stock) + ", " + \
                                    "availability = '" + availability +  "', " + \
                                    "lb_salable_qty = " + salable_qty + \
                                    " WHERE lb_product = '" + prod_id + "'"
        dbc.execute(sql)
