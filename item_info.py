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
# from db_config_file import db_config
from classes.myclasses import *
from classes.utilities import *


# #logging
log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='log/item_info.log', level=logging.DEBUG, format=log_format)

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
        # create a new Item object
        item = create_item(brand_id, sku_short, url, title, price, original_price, sale_info, description, details, season)
        # save the Item object in db
        dbc.insert_item(item)
        fetch_other_buyers(item)
    else:
        if exist_item['listed'] != 3:
            dbc.execute("UPDATE Items set listed = 4 WHERE serial='" + sku_short + "'")

# Create a new Item object from params. Return an Item object
def create_item(brand_id, serial, url, item_name, price, original_price, sale_info, description, details, season):
    description = description.replace("'", "''")
    details = details.replace("'", "''")
    # create an Item object
    item = Item(brand_id, serial, url, item_name, price, original_price, sale_info, description, details, season, 3)
    return item

# takes an Item object
def get_item_id_for_item(item):
    dbc = DBHelper()
    return dbc.get_item_id(item.serial)

def process_variation_data(serial, sku, url, color_code, size, availability, size_info, img_urls):
    dbc = DBHelper()
    if dbc.check_item_exists(serial):
        item_id = dbc.get_item_id(serial)

        variation = create_variation(item_id, sku, url, color_code, size, availability, size_info, img_urls)
        # insert Variationobj into Variations table
        dbc.insert_variation(variation)

# Create a new Variationobject. Return a Variationobject
def create_variation(item_id, sku, url, color_code, size_name, availability, size_info, img_urls):
    # fetch color information from tbl Ck_colors
    bm_col_name = get_color_j(color_code)
    bm_col_family = get_color_family(color_code)
    # has_stock = 0 when the variation is unavailable
    has_stock = 1
    if availability != 'In Stock' and availability != 'Low in Stock':
        has_stock = 0

    # create a Variationobject
    variation = Variation(item_id, sku, url, color_code, size_name, availability, has_stock, bm_col_name, bm_col_family, size_info, img_urls)

    return variation

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

# fetch color name in Japanese from table "lb_colors"
# receives ID, not color_code
def get_lb_color_j(color_id):
    dbc = DBHelper()
    sql = "select color_j from Lb_colors where id = '" + color_id + "'"
    color_j = ""
    try:
        row = dbc.fetchone(sql)
        if row is None: color_j = ""
        else: color_j = row['color_j']
    except pymysql.err.IntegrityError:
            logging.warning("check color of: %s", sku)
    return color_j

# fetch BM color family from table "lb_colors"
def get_lb_color_family(color_id):
    dbc = DBHelper()
    sql = "select bm_color_family from Lb_colors where id = '" + color_id + "'"
    row = dbc.fetchone(sql)
    color_family = 0
    if row is None:
        color_family = 0
        logging.warning("check color of: %s", sku)
    else:
        color_family = row['bm_color_family']
    return color_family

# crawl Buyma and get info about the same product from other buyers
# receives an Item object
def fetch_other_buyers(item):
    item_id = get_item_id_for_item(item)
    crawler = Crawler()
    bsObj = crawler.getPage("https://www.buyma.com/r/-F1/" + item.serial)
    resultList = bsObj.find(id="n_ResultList")
    divs = resultList.findAll('div', {'class': 'product_body'})

    # list holds multiple Buyer_price objects
    b_prices = list()
    for div in divs:
        div_product_name = div.find('div', {'class': 'product_name'})
        buyer_item = div_product_name.find('a')['href']
        price = div_product_name.find('a')['price']
        buyer_name = div.find('div', {'class':'product_Buyer'}).find('a').string

        #create a buyer_price object
        b_price = Buyer_price(item_id, buyer_name, price, buyer_item)
        b_prices.append(b_price)

    # process list of buyer_prices
    store_buyer_prices(b_prices)

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
