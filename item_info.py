from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from urllib.error import URLError
import re
import os
import pymysql
import webbrowser
import logging
import math
import json
from db_config_file import db_config
from classes.myclasses import Item, Variation, Buyer_price

# #logging
log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='item_info.log', level=logging.DEBUG, format=log_format)

# Connect MySQL
class DBHelper:
    def __init__(self):
        self.conn = pymysql.connect(host=db_config['host'],user=db_config['username'], password=db_config['password'], db=db_config['database'], cursorclass=pymysql.cursors.DictCursor)
        self.cur = self.conn.cursor()

    def __connect__(self):
        self.conn = pymysql.connect(host=db_config['host'],user=db_config['username'], password=db_config['password'], db=db_config['database'], cursorclass=pymysql.cursors.DictCursor)
        # self.conn = pymysql.connect(host=self.host, user=self.user, password=self.password, db=self.db, cursorclass=pymysql.cursors.DictCursor)
        self.cur = self.conn.cursor()

    def __disconnect__(self):
        self.conn.close()

    def fetchall(self, sql):
        self.__connect__()
        self.cur.execute(sql)
        result = self.cur.fetchall()
        self.__disconnect__()
        return result

    def fetchone(self, sql):
        self.__connect__()
        self.cur.execute(sql)
        result = self.cur.fetchone()
        # error
        # self.__disconnect__()
        return result

    def rowcount(self, sql):
        self.__connect__()
        self.cur.execute(sql)
        self.__disconnect__()
        return self.cur.rowcount

    def execute(self, sql):
        self.__connect__()
        try:
            if self.conn and self.cur:
                self.cur.execute(sql)
                self.conn.commit()
        except:
            logging.error("execute failed: " + sql)
            # error already disconnected
            # self.__disconnect__()
            return False
        return True

    def execute_insert(self, sql, category, key):
        # self.__connect__()
        try:
            if self.conn and self.cur:
                self.cur.execute(sql)
                self.conn.commit()
                # logging.warning("%d", affected_count)
                logging.info("inserted %s: %s", category, key)
        except:
            logging.error("execute failed: " + sql)
            logging.warning("failed to insert %s: %s", category, key)
            # error already disconnected
            # self.__disconnect__()
            return False
        return True

    # query Items table for sku_short
    def check_item_exists(self, serial):
        sql = "SELECT item_id FROM Items WHERE serial='" + serial + "'"
        return self.rowcount(sql) > 0

    # query Variations table for sku
    def check_variation_exists(self, sku):
        sql = "SELECT * FROM Variations WHERE sku = '" + sku + "'"
        return self.rowcount(sql) > 0

    # fetch item_id of serial from Items tbl
    def get_item_id(self, serial):
        sql = "SELECT item_id FROM Items WHERE serial='" + serial + "'"
        exist = self.fetchone(sql)
        if exist != None:
            return exist['item_id']
        return None

    # fetch id from Variations tbl for sku
    def get_variation_id(self, sku):
        sql = "SELECT id FROM Variations WHERE sku = '" + sku + "'"
        exist = self.fetchone(sql)
        if exist != None:
            return exist['id']
        return None

    # insert a new item into Items table
    # param: an Item object
    def insert_item(self, item):
        sql = "INSERT INTO Items (brand_id, serial, url, item_name, price, original_price, sale_info, description, details, season, listed) VALUES ('" \
        + str(item.brand_id) + "', '" + item.serial + "', '" + item.url + "', '" + item.item_name  + "', '" + str(item.price)  + "', '" + str(item.original_price)  + "', '" \
        + item.sale_info  + "', '" + item.description + "', '" + item.details + "', '" + item.season + "', 3)"
        self.execute_insert(sql, 'item', item.serial)

    # insert a new variation of an item into Variations table
    # param: a Variaion object
    def insert_variation(self, variation):
        sql = "INSERT INTO Variations (item_id, sku, url, color_code, size_name, availability, has_stock, bm_col_name, bm_col_family, size_info) VALUES ('" \
        + str(variation.item_id) + "','" + variation.sku + "','" + variation.url + "','" + variation.color_code + "','" + variation.size_name + "','" \
        + variation.availability + "', " + str(variation.has_stock) + ", '" + str(variation.bm_col_name) + "', '" + str(variation.bm_col_family) + "', '" + variation.size_info + "')"
        self.execute_insert(sql, 'variation', variation.sku)

    # insert a new buyer_price for an item into Buyer_price table
    # param: a buyer_price object
    def insert_buyer_price(self, buyer_price):
        sql =  "INSERT INTO Buyer_price(item_id, buyer, price, url) VALUES ('" + \
        buyer_price.item_id + "','" + buyer_price.buyer + "','" + buyer_price.price + "','" + buyer_price.url + "')"
        self.execute_insert(sql, 'buyer_price', buyer_price.url)

def getItemInfo(url, brand_id):
    try:
        html = urlopen(url)
    except HTTPError as e:
        return None
    try:
        bsObj = BeautifulSoup(html, 'lxml')

        sku = ''
        if len(bsObj.findAll("span", {"itemprop":{"productID"}})) > 0:
            sku = bsObj.find("span", {"itemprop":{"productID"}}).get_text()
        elif len(bsObj.findAll("span", {"class":{"product-id"}})) > 0:
            sku = bsObj.find("span", {"class":{"product-id"}}).get_text()
        if len(sku) == 0:
            logging.info('check sku at %s.', url)
            return None

        # check if sku already exists in Variations table
        if check_variation_exists(sku, url):
            logging.info('%s already exists', sku)
            return None

        title = bsObj.h1.string.strip()
        title = title[:60]
        price = bsObj.find("meta", {"itemprop":{"price"}})['content']
        description = bsObj.find("div", {"itemprop":{"description"}}).get_text().strip()
        color = bsObj.find("div", {"class":{"selected-color"}}).get_text().strip()
        size = bsObj.find("div", {"class":{"selected-size"}}).get_text().strip()

        details = '' #string
        details_list = [] #list
        for li in bsObj.find("div", {"class":"js-product-details_val"}).findAll("li"):
            details += li.string + '\r\n'
            details_list.append(li.string)
        size_info = size_from_details(details_list)
        size_info = json.dumps(size_info)

        sku = ''
        if len(bsObj.findAll("span", {"itemprop":{"productID"}})) > 0:
            sku = bsObj.find("span", {"itemprop":{"productID"}}).get_text()
        elif len(bsObj.findAll("span", {"class":{"product-id"}})) > 0:
            sku = bsObj.find("span", {"class":{"product-id"}}).get_text()
        if len(sku) == 0:
            logging.info('check sku at %s.', url)
            return None
        try:
            sku_short = sku
            if re.match("(\w+\d-\d+(-\d)?)", sku):
                sku_short = re.match("(\w+\d-\d+(-\d)?)", sku).group(1)
            elif re.match("[A-Z0-9]+-[A-Z0-9]", sku):
                sku_short = re.match("[A-Z0-9]+-[A-Z0-9]", sku)[0]
        except IndexError:
            logging.info('check sku at %s.', url)

        discounted = bsObj.find("div", {"class":"discount_percentage"})
        if discounted:
            sale_info = discounted.string.strip()
        else:
            sale_info = ""

        strike_through = bsObj.find("span", {"class":"strike-through"})
        if strike_through:
            striked = strike_through.find("span", {"class":"value"}).string
            if len(striked) > 0:
                original_price = re.sub(r'[^0-9.-]+', '', striked)
        else:
            original_price = price

        span_availability = bsObj.find("span", {"class":"pdp-availability_badge"})
        if span_availability:
            availability = span_availability.get_text().strip()
            if availability == '':
                availability = 'OUT OF STOCK'
        else:
            availability = 'Check availability'
        if size == "Select Size":
            availability = 'OUT OF STOCK'
            size_span = bsObj.find("span", {"class":"size-value"})
            if size_span:
                size = size_span.get_text().strip()
        if availability != 'In Stock' and availability != 'Low in Stock':
            logging.info('%s is not available!: %s', sku, url)

        # img tags
        arr_img = bsObj.findAll("img", {"itemprop":"image"})

        firstimg = arr_img[0]
        imgname = get_imgname(firstimg)
        season = imgname[0:7]
        color_code =  re.findall("([\d|\w]+)-\d\.jpg", imgname)[0]

        img_urls = []
        for img in arr_img:
            img_urls.append(get_imglocation(img))

        process_item_data(brand_id, sku_short, url, title, price, original_price, sale_info, description, details, season)
        process_variation_data(sku_short, sku, url, color_code, size, availability, size_info, img_urls)

    except AttributeError as e:
        return None

# query Variations table for sku
def check_variation_exists(sku, url):
    dbc = DBHelper()
    sql = "SELECT * FROM Variations WHERE sku = '" + sku + "' OR url='" + url + "'"
    return dbc.rowcount(sql) > 0

# download images in the folder
def save_imgs(imglocations, folderName):
    currPath = os.path.dirname(os.path.realpath(__file__))
    reqPath = os.path.join(currPath,folderName)
    if os.path.isdir(reqPath) == False:
        os.mkdir(folderName)

    for imglocation in imglocations:
        imgname = re.findall("[\d, \w,-]+\.jpg", imglocation)[0]
        filename = os.path.join(reqPath, imgname)
        urlretrieve(imglocation, filename)

def get_imglocation(img):
    if img.has_attr('data-src'):
        imglocation = img['data-src']
    else:
        imglocation = img['src']
    return imglocation

def get_imgname(img):
    imglocation = get_imglocation(img)
    return re.findall("[\d, \w,-]+\.jpg", imglocation)[0]

def process_item_data(brand_id, sku_short, url, title, price, original_price, sale_info, description, details, season):
    dbc = DBHelper()
    sql_item = "SELECT item_id, listed FROM Items WHERE serial='" + sku_short + "'"
    exist_item = dbc.fetchone(sql_item)
    # if sku_short not in Items table
    if exist_item is None:
        # add new item
        store_item(brand_id, sku_short, url, title, price, original_price, sale_info, description, details, season)
    else:
        if exist_item['listed'] != 3:
            dbc.execute("UPDATE Items set listed = 4 WHERE serial='" + sku_short + "'")

# Storing item info into  MySQL database
def store_item(brand_id, serial, url, item_name, price, original_price, sale_info, description, details, season):
    description = description.replace("'", "''")
    details = details.replace("'", "''")
    # create an Item object
    item = Item(brand_id, serial, url, item_name, price, original_price, sale_info, description, details, season, 3)

    dbc = DBHelper()
    dbc.insert_item(item)

def process_variation_data(serial, sku, url, color_code, size, availability, size_info, img_urls):
    dbc = DBHelper()
    if dbc.check_item_exists(serial):
        item_id = dbc.get_item_id(serial)

        store_variation(item_id, sku, url, color_code, size, availability, size_info)
        fetch_other_buyers(str(item_id), serial)

        if dbc.check_variation_exists(sku):
            variation_id = dbc.get_variation_id(sku)
            # save_imgs(img_urls, sku_short)
            store_img_urls(str(item_id), str(variation_id), img_urls)

# Storing item variation into Variations table
def store_variation(item_id, sku, url, color_code, size_name, availability, size_info):
    # fetch color information from tbl Ck_colors
    bm_col_name = get_color_j(color_code)
    bm_col_family = get_color_family(color_code)
    # has_stock = 0 when the variation is unavailable
    has_stock = 1
    if availability != 'In Stock' and availability != 'Low in Stock':
        has_stock = 0

    # create a Variaion object
    variation = Variation(item_id, sku, url, color_code, size_name, availability, has_stock, bm_col_name, bm_col_family, size_info)

    # insert variaion obj into Variations table
    dbc = DBHelper()
    dbc.insert_variation(variation)

# fetch color name in Japanese from table "ck_colors"
def get_color_j(color_code):
    dbc = DBHelper()
    sql = "select color_j from ck_colors where color_code = '" + color_code + "'"
    color_j = ""
    try:
        row = dbc.fetchone(sql)
        if row is None: color_j = ""
        else: color_j = row['color_j']
    except pymysql.err.IntegrityError:
            logging.warning("check color of: %s", sku)
    return color_j

# fetch BM color family from table "ck_colors"
def get_color_family(color_code):
    dbc = DBHelper()
    sql = "select bm_color_family from ck_colors where color_code = '" + color_code + "'"
    row = dbc.fetchone(sql)
    color_family = 0
    if row is None:
        color_family = 0
        logging.warning("check color of: %s", sku)
    else:
        color_family = row['bm_color_family']
    return color_family

# crawl Buyma and get info about the same product from other buyers
def fetch_other_buyers(item_id, serial):
    url = "https://www.buyma.com/r/-F1/" + serial
    try:
        html = urlopen(url)
    except (HTTPError, URLError) as e:
        print(e.code)
        return None
    try:
        bsObj = BeautifulSoup(html, 'lxml')

        divs = bsObj.findAll('div', {'class': 'product_body'})

        # list holds multiple Buyer_price objects
        b_prices = list()
        for div in divs:
            div_product_name = div.find('div', {'class': 'product_name'})
            buyer_item = div_product_name.find('a')['href']
            price = div_product_name.find('a')['price']
            buyer_name = div.find('div', {'class':'product_Buyer'}).find('a').string

            #create a buyer_price object
            b_prices.append(Buyer_price(item_id, buyer_name, price, buyer_item))

        # process list of buyer_prices
        store_buyer_prices(b_prices)

    except AttributeError as e:
        return None

# takes a list of Buyer_price objects
def store_buyer_prices(lst_b_prices):
    dbc = DBHelper()
    # b_price = Buyer_price object
    for b_price in lst_b_prices:
        sql = "SELECT * FROM buyer_price WHERE url ='" + b_price.url + "'"
        exist = dbc.fetchone(sql)
        if exist is None:
            # insert a buyer_price obj into Buyer_price table
            dbc.insert_buyer_price(b_price)

def size_from_details(lst):
    size_info = {}
    for detail in lst:
        myregex = '(\w+)\s\(cm\):\s(\d+(\.\d+)?)'
        matched = re.match(myregex, detail)
        if matched:
            key = re.findall(myregex, detail)[0][0]
            val = re.findall(myregex, detail)[0][1]
            size_info[key] = val
    return size_info

def store_img_urls(item_id, variation_id, img_urls):
    dbc = DBHelper()
    for url in img_urls:
        img_name = re.findall("[\d, \w,-]+\.jpg", url)[0]
        sql = "SELECT img_name FROM Images WHERE img_name ='" + img_name + "'"
        exist = dbc.fetchone(sql)
        if exist is None:
            sql =  "INSERT INTO Images(item_id, variation_id, img_name, img_url) VALUES \
            ('" + item_id + "','" + variation_id + "','" + img_name + "','" + url + "')"
            dbc = DBHelper()
            dbc.execute_insert(sql, 'img_urls', img_name)

def get_items_from_list(lst, brand_id):
    for url in lst:
        getItemInfo(url, brand_id)

def get_pedro_urls(url):
    html = urlopen(url)
    logging.info("crawling %s: ", url)
    bsObj = BeautifulSoup(html, 'lxml')
    base = "https://www.pedroshoes.com"
    new_urls = list()
    for div in bsObj.find_all(class_='active'):
        a = div.find('a', {"class":"full-pdp-link"})
        new_urls.append(base + a['href'])

    return new_urls

def get_ck_urls(url):
    html = urlopen(url)
    logging.info("crawling %s: ", url)
    bsObj = BeautifulSoup(html, 'lxml')
    base = "https://www.charleskeith.com"
    new_urls = list()
    for div in bsObj.find_all(class_='active'):
        a = div.find('a', {"class":"full-pdp-link"})
        new_urls.append(base + a['href'])

    return new_urls

def item_pw():
    #brand_id
    PEDRO_ID = '2'
    # fetch Pedro items
    html = urlopen("https://www.pedroshoes.com/sg/women/bags")
    bsObj = BeautifulSoup(html, 'lxml')
    res_cont_div = bsObj.find('div', {"class":"result-count"}).find('span').string.strip()
    res_cont = int(re.sub(r'[^0-9]+', '', res_cont_div))
    print(res_cont)
    #
    n = math.ceil(res_cont / 60)
    urls = list()
    for i in range(n):
        urls = urls + get_pedro_urls("https://www.pedroshoes.com/sg/women/bags?page=" + str(i + 1))

    get_items_from_list(urls, PEDRO_ID)

    # different from item.py, scrawling sale pages
    # get_pedro_urls("https://www.pedroshoes.com/sg/sale/women/bags")
    # get_pedro_urls("https://www.pedroshoes.com/sg/sale/women/bags?page=2")

# fetch CK items
def item_ck():
    # brand_id
    CK_ID = '1'

    n = math.ceil(657 / 90)
    urls = list()
    # for i in range(n):
    #     urls = urls + get_ck_urls("https://www.charleskeith.com/sg/bags?page=" + str(i + 1))

    # urls = urls + get_ck_urls("https://www.charleskeith.com/sg/bags")
    # urls = urls + get_ck_urls("https://www.charleskeith.com/sg/bags?page=2")
    # urls = urls + get_ck_urls("https://www.charleskeith.com/sg/bags?page=3")
    # urls = urls + get_ck_urls("https://www.charleskeith.com/sg/bags?page=4")
    # urls = urls + get_ck_urls("https://www.charleskeith.com/sg/bags?page=5")
    # urls = urls + get_ck_urls("https://www.charleskeith.com/sg/bags?page=6")
    urls = urls + get_ck_urls("https://www.charleskeith.com/sg/bags?page=7")
    urls = urls + get_ck_urls("https://www.charleskeith.com/sg/bags?page=8")

    get_items_from_list(urls, CK_ID)

# Enter Item manually
def item_enter():
    input_list = []
    try:
        url = input("Enter url (enter 0 to end): ")
        while url != "0":
            input_list.append(url)
            url = input("Enter url (enter 0 to end): ")
        brand_id = input("Enter brand ID: ")
    except:
      print(input_list)
