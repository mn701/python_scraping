from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
import re
import os
import pymysql

# Connect MySQL
conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock', user='root', passwd=None, db='mysql', charset='utf8')
cur = conn.cursor()
cur.execute("USE shop")

def getItemInfo(url):
    try:
        html = urlopen(url)
    except HTTPError as e:
        return None
    try:
        bsObj = BeautifulSoup(html, 'lxml')
        sku = bsObj.find("span", {"itemprop":{"productID"}}).get_text()
        title = bsObj.h1.string
        price = bsObj.find("meta", {"itemprop":{"price"}})['content']
        description = bsObj.find("div", {"itemprop":{"description"}}).get_text().strip()
        details = bsObj.find("div", {"class":"js-product-details_val"}).get_text().strip()
        color = bsObj.find("div", {"class":{"selected-color"}}).get_text().strip()

        sku_short = re.findall("\w+\d-\d+", sku)[0]
        brand_id = '2'

        try:
            store_item(brand_id, sku_short, url, title, price, description, details)
            cur.execute("SELECT item_id FROM items WHERE serial='" + sku_short + "'")
            if(cur.rowcount > 0):
                item_id = cur.fetchone()[0]
                store_variation(str(item_id), sku, url)
        finally:
            cur.close()
            conn.close()

        arr_img = bsObj.findAll("img", {"itemprop":"image"})
        # Creating a folder using sku
        foldername = sku_short
        save_imgs(arr_img, foldername)
    except AttributeError as e:
        return None

# download images in the folder
def save_imgs(images, folderName):
    currPath = os.path.dirname(os.path.realpath(__file__))
    reqPath = os.path.join(currPath,folderName)
    if os.path.isdir(reqPath) == False:
        os.mkdir(folderName)
    for img in images:
        imglocation = img['src']
        imgname= re.findall("[\d, \w,-]+\.jpg", imglocation)[0]
        filename = os.path.join(reqPath, imgname)
        urlretrieve(imglocation, filename)

# Storing item info into  MySQL database
def store_item(brand_id, serial, url, item_name, price, description, details):
    cur.execute("SELECT * FROM Items WHERE serial='" + serial + "'")
    exist = cur.fetchone()
    if exist is None:
        cur.execute("INSERT INTO Items (brand_id, serial, url, item_name, price, description, details) VALUES ('" + brand_id + "','" + serial + "','" + url + "','" + item_name  + "','" + price  + "','" + description + "','" + details + "')")
        cur.connection.commit()

# Storing items' Variation into Variations table
def store_variation(item_id, sku, url):
    cur.execute("SELECT * FROM Variations WHERE sku='" + sku + "'")
    exist = cur.fetchone()
    if exist is None:
        cur.execute("INSERT INTO Variations (item_id, sku, url, has_stock) VALUES ('" + item_id + "','" + sku + "','" + url + "', 1)")
        cur.connection.commit()
    else:
        print("Item already exist!")

print("Enter your url:")
url = input()
getItemInfo(url)
