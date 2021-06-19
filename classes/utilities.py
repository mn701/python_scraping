import pymysql
import logging
from bs4 import BeautifulSoup
import requests
import re
from .db_config_file import db_config

# #logging
log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='log/item_info.log', level=logging.DEBUG, format=log_format)

# Handle connecting MySQL
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

    # query Variations table for sku and url
    def check_variation_exists_url(self, sku, url):
        sql = "SELECT * FROM Variations WHERE sku = '" + sku + "' OR url='" + url + "'"
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
        sql = "INSERT IGNORE INTO Items (brand_id, serial, url, item_name, price, original_price, sale_info, description, details, season, postage, listed) VALUES ('" \
        + str(item.brand_id) + "', '" + item.serial + "', '" + item.url + "', '" + item.item_name  + "', '" + str(item.price)  + "', '" + str(item.original_price)  + "', '" \
        + item.sale_info  + "', '" + item.description + "', '" + item.details + "', '" + item.season + "', '" + str(item.postage) + "', 3)"
        self.execute_insert(sql, 'item', item.serial)

    # insert a new variation of an item into Variations table
    # param: a Variaion object
    def insert_variation(self, variation):
        sql = "INSERT IGNORE INTO Variations (item_id, sku, url, color_code, size_name, has_stock, availability, bm_order, bm_col_name, bm_col_family, size_info) VALUES ('" \
        + str(variation.item_id) + "','" + variation.sku + "','" + variation.url + "','" + variation.color_code + "','" + variation.size_name + "','" \
        + str(variation.has_stock) + "', '" + variation.availability + "', '" + str(variation.bm_order) + "', '" + str(variation.bm_col_name) + "', '" + str(variation.bm_col_family) + "', '" \
        + variation.size_info + "')"

        if self.execute_insert(sql, 'variation', variation.sku):
            variation_id = self.get_variation_id(variation.sku)
            # save_imgs(img_urls, sku_short)
            self.store_img_urls(str(variation.item_id), str(variation_id), variation.img_urls)

    def store_img_urls(self, item_id, variation_id, img_urls):
        for url in img_urls:
            try:
                img_name = re.findall("[\d, \w,-]+\.jpg", url)[0]
            except indexError as error:
                logging.error("Check img name: " + url)
            if img_name:
                sql = "SELECT img_name FROM Images WHERE img_name ='" + img_name + "'"
                exist = self.fetchone(sql)
                if exist is None:
                    sql =  "INSERT INTO Images(item_id, variation_id, img_name, img_url) VALUES \
                    ('" + item_id + "','" + variation_id + "','" + img_name + "','" + url + "')"

                    self.execute_insert(sql, 'img_urls', img_name)

    # insert a new buyer_price for an item into Buyer_price table
    # param: a buyer_price object
    def insert_buyer_price(self, buyer_price):
        sql =  "INSERT INTO Buyer_price(item_id, buyer, price, url) VALUES ('" + \
        str(buyer_price.item_id) + "','" + buyer_price.buyer + "','" + str(buyer_price.price) + "','" + buyer_price.url + "')"
        self.execute_insert(sql, 'buyer_price', buyer_price.url)

    # insert a new lb_item into Items table
    # param: a Lb_item object
    def insert_lb_variation(self, lb_variation):
        self.insert_variation(lb_variation)

        variation_id = self.get_variation_id(lb_variation.sku)
        sql = "UPDATE Variations SET lb_product = " + str(lb_variation.lb_product) + \
        ", lb_salable_qty = " + str(lb_variation.lb_salable_qty) + " WHERE id = " + str(variation_id)

        self.execute(sql)

class Crawler:
    def getPage(self, url):
        try:
            req = requests.get(url)
        except requests.exceptions.RequestException:
            return None
        return BeautifulSoup(req.text, 'html.parser')

    def safeGet(self, pageObj, selector):
        childObj = pageObj.select(selector)
        if childObj is not None and len(childObj) > 0:
            return childObj[0].get_text().strip()
        return ''
