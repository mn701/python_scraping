from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
import re
import os
import pymysql
import webbrowser
import logging

#logging
logging.basicConfig(filename='item_info.log', level=logging.DEBUG)

# Connect MySQL
conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock', user='root', passwd=None, db='mysql', charset='utf8')
cur = conn.cursor()
cur.execute("USE shop")

def getItemInfo(url, brand_id):
    try:
        html = urlopen(url)
    except HTTPError as e:
        return None
    try:
        bsObj = BeautifulSoup(html, 'lxml')
        title = bsObj.h1.string
        price = bsObj.find("meta", {"itemprop":{"price"}})['content']
        description = bsObj.find("div", {"itemprop":{"description"}}).get_text().strip()
        details = bsObj.find("div", {"class":"js-product-details_val"}).get_text().strip()
        color = bsObj.find("div", {"class":{"selected-color"}}).get_text().strip()
        size = bsObj.find("div", {"class":{"selected-size"}}).get_text().strip()

        if len(bsObj.findAll("span", {"itemprop":{"productID"}})) > 0:
            sku = bsObj.find("span", {"itemprop":{"productID"}}).get_text()
        elif len(bsObj.findAll("span", {"class":{"product-id"}})) > 0:
            sku = bsObj.find("span", {"class":{"product-id"}}).get_text()

        sku_short = re.findall("\w+\d-\d+", sku)[0]

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

        # img tags
        arr_img = bsObj.findAll("img", {"itemprop":"image"})

        firstimg = arr_img[0]
        imgname = get_imgname(firstimg)
        season = imgname[0:7]
        color_code =  re.findall("([\d|\w]+)-\d\.jpg", imgname)[0]

        cur.execute("SELECT * FROM Variations WHERE sku='" + sku + "'")
        exist = cur.fetchone()
        if exist is None:
            store_item(brand_id, sku_short, url, title, price, original_price, sale_info, description, details, season)
            cur.execute("SELECT item_id FROM items WHERE serial='" + sku_short + "'")
            if(cur.rowcount > 0):
                item_id = cur.fetchone()[0]
                store_variation(str(item_id), sku, url, color_code, size)
                fetch_other_buyers(str(item_id), sku_short)
            save_imgs(arr_img, sku_short)
        else:
            logging.info('%s already exists!', sku)

        # opening URL in chrome browser
        # chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
        # url = "https://www.buyma.com/r/-F1/" + sku_short
        # webbrowser.get(chrome_path).open(url)

    except AttributeError as e:
        return None

# download images in the folder
def save_imgs(images, folderName):
    currPath = os.path.dirname(os.path.realpath(__file__))
    reqPath = os.path.join(currPath,folderName)
    if os.path.isdir(reqPath) == False:
        os.mkdir(folderName)

    color_code = 'none'
    season = 'none'
    for img in images:
        imglocation = get_imglocation(img)
        imgname = get_imgname(img)
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
        sql = "INSERT INTO Items (brand_id, serial, url, item_name, price, original_price, sale_info, description, details, season) VALUES ('" + brand_id + "','" + serial + "','" + url + "','" + item_name  + "','" + price  + "','" + original_price  + "','" + sale_info  + "', '" + description + "', '" + details + "','" + season + "')"
        execute_sql(sql, 'item', serial)

# execute insert-into and log result
def execute_sql(sql, category, key):
    try:
        affected_count = cur.execute(sql)
        conn.commit()
        # logging.warning("%d", affected_count)
        logging.info("inserted %s: %s", category, key)
    except MySQLdb.IntegrityError:
        logging.warning("failed to insert %s: %s", category, key)

# Storing item variation into Variations table
def store_variation(item_id, sku, url, color_code, size_name):
    sql = "INSERT INTO Variations (item_id, sku, url, color_code, size_name, has_stock) VALUES ('" + item_id + "','" + sku + "','" + url + "','" + color_code + "','" + size_name + "', 1)"
    execute_sql(sql, 'variation', sku)

# crawl Buyma and get info about the same product from other buyers
def fetch_other_buyers(item_id, serial):
    cur.execute("SELECT * FROM Buyer_price WHERE item_id ='" + item_id + "'")
    exist = cur.fetchone()
    if exist is None:

        url = "https://www.buyma.com/r/-F1/" + serial
        html = urlopen(url)
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

def store_buyer_price(item_id, buyer, price, url):
    sql =  "INSERT INTO Buyer_price(item_id, buyer, price, url) VALUES ('" + item_id + "','" + buyer + "','" + price + "','" + url + "')"
    execute_sql(sql, 'buyer_price', url)

def get_items_from_list(lst, brand_id):
    try:
        for url in lst:
            getItemInfo(url, brand_id)
    finally:
        cur.close()
        conn.close()

html = urlopen("https://www.pedroshoes.com/sg/women/bags")
bsObj = BeautifulSoup(html, 'lxml')
base = "https://www.pedroshoes.com"
new_urls = list()
for div in bsObj.find_all(class_='active'):
    a = div.find('a', {"class":"full-pdp-link"})
    new_urls.append(base + a['href'])

get_items_from_list(new_urls, "2")

# input_list = []
# try:
#     url = input("Enter url (enter 0 to end): ")
#     while url != "0":
#         input_list.append(url)
#         url = input("Enter url (enter 0 to end): ")
#     brand_id = input("Enter brand ID: ")
# except:
#   print(input_list)
#
# get_items_from_list(input_list, brand_id)
