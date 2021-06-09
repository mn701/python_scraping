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

# #logging
# log_format = '%(asctime)s %(filename)s: %(message)s'
# logging.basicConfig(filename='item_info.log', level=logging.DEBUG, format=log_format)
#
# Connect MySQL
pw = os.environ.get('mysql_password')
conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock', user='root', passwd=pw, db='mysql', charset='utf8')
cur = conn.cursor()
cur.execute("USE shop")

def getItemInfo(url, brand_id):
    try:
        html = urlopen(url)
    except HTTPError as e:
        return None
    try:
        bsObj = BeautifulSoup(html, 'lxml')
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

        cur.execute("SELECT * FROM Variations WHERE sku='" + sku + "' OR url='" + url +"'")
        exist = cur.fetchone()
        if exist is None:
            cur.execute("SELECT item_id FROM items WHERE serial='" + sku_short + "'")
            exist = cur.fetchone()
            if exist is None:
                ## add new item
                store_item(brand_id, sku_short, url, title, price, original_price, sale_info, description, details, season)
            else:
                cur.execute("UPDATE items set listed = 4 WHERE serial='" + sku_short + "'")
                conn.commit()
            ## add new variation
            cur.execute("SELECT item_id FROM items WHERE serial='" + sku_short + "'")
            if(cur.rowcount > 0):
                item_id = cur.fetchone()[0]
                store_variation(str(item_id), sku, url, color_code, size, availability, size_info)
                fetch_other_buyers(str(item_id), sku_short)
                cur.execute("SELECT id FROM Variations WHERE sku='" + sku + "'")
                if(cur.rowcount > 0):
                    variation_id = cur.fetchone()[0]
                store_img_urls(str(item_id), str(variation_id), img_urls)
            save_imgs(img_urls, sku_short)
        else:
            logging.info('%s already exists', sku)

        # opening URL in chrome browser
        # chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
        # url = "https://www.buyma.com/r/-F1/" + sku_short
        # webbrowser.get(chrome_path).open(url)

    except AttributeError as e:
        return None

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

# Storing item info into  MySQL database
def store_item(brand_id, serial, url, item_name, price, original_price, sale_info, description, details, season):
    cur.execute("SELECT * FROM Items WHERE serial='" + serial + "'")
    exist = cur.fetchone()
    if exist is None:
        description = description.replace("'", "''")
        details = details.replace("'", "''")
        sql = "INSERT INTO Items (brand_id, serial, url, item_name, price, original_price, sale_info, description, details, season, listed) VALUES ('" \
        + brand_id + "','" + serial + "','" + url + "','" + item_name  + "','" + price  + "','" + original_price  + "','" \
        + sale_info  + "', '" + description + "', '" + details + "','" + season + "', 3)"
        execute_sql(sql, 'item', serial)

# execute insert-into and log result
def execute_sql(sql, category, key):
    try:
        affected_count = cur.execute(sql)
        conn.commit()
        # logging.warning("%d", affected_count)
        logging.info("inserted %s: %s", category, key)
    except pymysql.err.IntegrityError:
        logging.warning("failed to insert %s: %s", category, key)

# Storing item variation into Variations table
def store_variation(item_id, sku, url, color_code, size_name, availability, size_info):
    sql = "select color_j from ck_colors where color_code = '" + color_code + "'"
    try:
        cur.execute(sql)
        row = cur.fetchone()
        if row == None: color_j = ""
        else: color_j = row[0]
        sql = "select bm_color_family from ck_colors where color_code = '" + color_code + "'"
        cur.execute(sql)
        row = cur.fetchone()
        if row == None:
            color_family = 0
        else:
            color_family = row[0]
    except pymysql.err.IntegrityError:
            logging.warning("check color of: %s", sku)

    sql = "INSERT INTO Variations (item_id, sku, url, color_code, size_name, availability, has_stock, bm_col_name, bm_col_familys, size_info) VALUES ('" \
    + item_id + "','" + sku + "','" + url + "','" + color_code + "','" + size_name + "','" \
    + availability + "', 1, '" + str(color_j) + "', '" + str(color_family) + "', '" + size_info + "')"
    execute_sql(sql, 'variation', sku)

# crawl Buyma and get info about the same product from other buyers
def fetch_other_buyers(item_id, serial):
    cur.execute("SELECT * FROM Buyer_price WHERE item_id ='" + item_id + "'")
    exist = cur.fetchone()
    if exist is None:
        url = "https://www.buyma.com/r/-F1/" + serial
        try:
            html = urlopen(url)
        except (HTTPError, URLError) as e:
            print(e.code)
            return None
        try:
            bsObj = BeautifulSoup(html, 'lxml')

            divs = bsObj.findAll('div', {'class': 'product_body'})
            for div in divs:
                div_product_name = div.find('div', {'class': 'product_name'})
                buyer_item = div_product_name.find('a')['href']
                buyer_price = div_product_name.find('a')['price']
                buyer_name = div.find('div', {'class':'product_Buyer'}).find('a').string

                cur.execute("SELECT * FROM Buyer_price WHERE url ='" + buyer_item + "'")
                exist = cur.fetchone()
                if exist is None:
                    store_buyer_price(item_id, buyer_name, buyer_price, buyer_item)
        except AttributeError as e:
            return None

def store_buyer_price(item_id, buyer, price, url):
    sql =  "INSERT INTO Buyer_price(item_id, buyer, price, url) VALUES ('" + item_id + "','" + buyer + "','" + price + "','" + url + "')"
    execute_sql(sql, 'buyer_price', url)

def size_from_details(lst):
    size_info = {}
    for str in lst:
        myregex = '(\w+)\s\(cm\):\s(\d+(\.\d+)?)'
        matched = re.match(myregex, str)
        if matched:
            key = re.findall(myregex, str)[0][0]
            val = re.findall(myregex, str)[0][1]
            size_info[key] = val
    return size_info

def store_img_urls(item_id, variation_id, img_urls):
    for url in img_urls:
        img_name = re.findall("[\d, \w,-]+\.jpg", url)[0]
        cur.execute("SELECT img_name FROM Images WHERE img_name ='" + img_name + "'")
        exist = cur.fetchone()
        if exist is None:
            sql =  "INSERT INTO Images(item_id, variation_id, img_name, img_url) VALUES \
            ('" + item_id + "','" + variation_id + "','" + img_name + "','" + url + "')"
            execute_sql(sql, 'img_urls', img_name)

def get_items_from_list(lst, brand_id):
    for url in lst:
        getItemInfo(url, brand_id)

PEDRO_ID = '2'
def get_pedro_urls(url):
    html = urlopen(url)
    logging.info("crawling %s: ", url)
    bsObj = BeautifulSoup(html, 'lxml')
    base = "https://www.pedroshoes.com"
    new_urls = list()
    for div in bsObj.find_all(class_='active'):
        a = div.find('a', {"class":"full-pdp-link"})
        new_urls.append(base + a['href'])

    get_items_from_list(new_urls, PEDRO_ID)

CK_ID = '1'
def get_ck_urls(url):
    html = urlopen(url)
    logging.info("crawling %s: ", url)
    bsObj = BeautifulSoup(html, 'lxml')
    base = "https://www.charleskeith.com"
    new_urls = list()
    for div in bsObj.find_all(class_='active'):
        a = div.find('a', {"class":"full-pdp-link"})
        new_urls.append(base + a['href'])

    get_items_from_list(new_urls, CK_ID)

# fetch Pedro items
html = urlopen("https://www.pedroshoes.com/sg/women/bags")
bsObj = BeautifulSoup(html, 'lxml')

res_cont_div = bsObj.find('div', {"class":"result-count"}).find('span').string.strip()
res_cont = int(re.sub(r'[^0-9]+', '', res_cont_div))
# print(res_cont)
#
# n = math.ceil(res_cont / 60)
# for i in range(n):
#     get_pedro_urls("https://www.pedroshoes.com/sg/women/bags?page=" + str(i + 1))

# different from item.py, scrawling sale pages
# get_pedro_urls("https://www.pedroshoes.com/sg/sale/women/bags")
# get_pedro_urls("https://www.pedroshoes.com/sg/sale/women/bags?page=2")

# fetch CK items
# n = math.ceil(657 / 90)
# for i in range(n):
#     get_ck_urls("https://www.charleskeith.com/sg/bags?page=" + str(i + 1))

# get_ck_urls("https://www.charleskeith.com/sg/bags")
# get_ck_urls("https://www.charleskeith.com/sg/bags?page=2")
# get_ck_urls("https://www.charleskeith.com/sg/bags?page=3")
# get_ck_urls("https://www.charleskeith.com/sg/bags?page=4")
# get_ck_urls("https://www.charleskeith.com/sg/bags?page=5")
# get_ck_urls("https://www.charleskeith.com/sg/bags?page=6")
# get_ck_urls("https://www.charleskeith.com/sg/bags?page=7")
# get_ck_urls("https://www.charleskeith.com/sg/bags?page=8")

# Enter Item manually
input_list = []
try:
    url = input("Enter url (enter 0 to end): ")
    while url != "0":
        input_list.append(url)
        url = input("Enter url (enter 0 to end): ")
    brand_id = input("Enter brand ID: ")
except:
  print(input_list)

get_items_from_list(input_list, brand_id)

cur.close()
conn.close()
