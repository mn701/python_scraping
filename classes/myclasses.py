import pymysql
import logging
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

# Holds information about an Item  -> tbl Items
class Item:
    def __init__(self, brand_id, serial, url, item_name, price, original_price, sale_info, description, details, season, listed):
        self.brand_id = brand_id
        self.serial = serial
        self.url = url
        self.item_name = item_name
        self.price = price
        self.original_price = original_price
        self.sale_info = sale_info
        self.description = description
        self.details = details
        self.season = season
        self.listed = listed

# Holds information about a Variaion of an Item  -> tbl Variations
class Variation:
    def __init__(self, item_id, sku, url, color_code, size_name, availability, has_stock, bm_col_name, bm_col_family, size_info):
        self.item_id =  item_id
        self.sku = sku
        self.url = url
        self.color_code = color_code
        self.size_name = size_name
        self.availability = availability
        self.has_stock = has_stock
        self.bm_col_name = bm_col_name
        self.bm_col_family = bm_col_family
        self.size_info = size_info

# Holds information about listing from other buyers for an Item  -> tbl Buyer_price
class Buyer_price:
    def __init__(self, item_id, buyer, price, url):
        self.item_id = item_id
        self.buyer = buyer
        self.price = price
        self.url = url