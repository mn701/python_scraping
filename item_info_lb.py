from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
from urllib.error import URLError
import requests
import re
import os
import pymysql
import webbrowser
import logging
import math
import json
from classes.myclasses import *
from classes.utilities import *
from classes.common_funcs import *

# logging
log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(filename='log/lb_item_info.log', level=logging.DEBUG, format=log_format)

# scrape one url and returns an Item objectß
def getItemInfo(url, brand_id):
    crawler = Crawler()
    bsObj = crawler.getPage(url)

    sku_short = crawler.safeGet(bsObj, 'div[itemprop="sku"]')
    # check if sku_short already exists in Items table
    dbc = DBHelper()
    if dbc.check_item_exists(sku_short):
        logging.info('%s already exists', sku_short)
        return None

    item_name = crawler.safeGet(bsObj, 'span[itemprop="name"]')
    item_name = item_name[:60]
    price = crawler.safeGet(bsObj, 'span[class="price"]')
    price = re.match(".*\s([0-9.]+)", price)[1]
    description = crawler.safeGet(bsObj, 'div[itemprop="description"]')

    detailslist = bsObj.find("div", {"class":{"pdp-detailslist"}}).find_all("li")
    details_dict = dict()
    for li in detailslist:
        bene_title = li.find("div", {"class":{"pdp-benefits-1__title"}})
        if bene_title:
            subtitle = crawler.safeGet(li, 'span[class="pdp-benefits-1__subtitle"]')
            details_dict[bene_title.string] = subtitle
    material_span = bsObj.find("div", string="Material & Care").find_next_sibling()
    details_dict['Material'] = material_span.get_text()
    # convert dict to string
    details = json.dumps(details_dict)

    original_price = price
    available = bsObj.find("div", {"title":{"Availability"}})
    availability = crawler.safeGet(available, 'span')

    item = create_item(brand_id, sku_short, url, item_name, price, original_price, '', description, details, '')
    return item

def getVariationInfo(url):
    crawler = Crawler()
    bsObj = crawler.getPage(url)
    dbc = DBHelper()

    sku_short = crawler.safeGet(bsObj, 'div[itemprop="sku"]')
    item_id = dbc.get_item_id(sku_short)
    if item_id is None: return None

    tbl_obj = bsObj.find("div", {"class":{"lb__size-guide__cm-body-measurement"}})

    size_dict = process_size_table(tbl_obj)

    script_string = ''
    magento_scripts = bsObj.find_all("script", {"type":{"text/x-magento-init"}})
    for script in magento_scripts:
        if '[data-role=swatch-options]' in script.string:
            script_string = script.string

    loadedjson = json.loads(script_string)
    jsonConfig = loadedjson['[data-role=swatch-options]']['Magento_Swatches/js/swatch-renderer']['jsonConfig']

    index = jsonConfig['index']
    attributes = jsonConfig['attributes']
    skus = jsonConfig['sku']
    images = jsonConfig['images']

    colors = attributes['94']['options']
    for option in colors:
        process_lb_colors(option['id'],option['label'])

    # create a dictionary of size id - size label
    sizes = attributes['150']['options']

    size_labels = dict()
    for option in sizes:
        size_labels[option['id']] = option['label']

    # holds BMM show order for each size
    orderdict = dict()
    temp_list = list(size_labels)
    for i in range(len(temp_list)):
        orderdict[temp_list[i]] = i + 1

    variations = list()
    # key in index is each prod
    for key in index:
        prod_id = key
        sku = skus[key]
        color_id = index[key]['94']
        size_id = index[key]['150']
        size_label = size_labels[size_id]
        bm_order = orderdict[size_id]
        size_info = size_dict[size_label]
        salable_qty = index[key]['lb_salable_qty']

        # images contain blank []
        prod_images = images[key]
        img_urls = list()
        for imginfo in prod_images:
            if len(imginfo) > 0:
                img_urls.append(imginfo.get('img'))
        # print ('prod_id: ', prod_id)
        # print ('sku: ', sku)
        # print ('color_id: ', color_id)
        # print ('size_id: ', size_label)
        # print ('salable_qty: ', salable_qty)
        # print ('size_info: ', size_info)
        # for url in img_urls:
        #     # print(url)
        # print('\n\n')
        variation = create_lb_variation(item_id, sku, url, color_id, size_label, bm_order, size_info, img_urls, prod_id, salable_qty)
        variations.append(variation)
    return variations

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

# Create a new variation  object. Return a Variationobject
def create_lb_variation(item_id, sku, url, color_id, size_name, bm_order, size_info, img_urls, lb_product, lb_salable_qty):
    availability = 'OUT OF STOCK'
    has_stock = 0
    lb_salable_qty = int(lb_salable_qty)
    if lb_salable_qty > 0:
        has_stock = 1
        if lb_salable_qty < 50:
            availability = 'Low in Stock'
        else:
            availability = 'In Stock'

    # fetch color information from tbl Ck_colors
    bm_col_name = get_lb_color_j(color_id)
    bm_col_family = get_lb_color_family(color_id)

    # size_info is a dict
    size_info = json.dumps(size_info)

    # create a Variationobject
    variation = Lb_Variation(item_id, sku, url, color_id, size_name, has_stock, availability, \
    bm_order, bm_col_name, bm_col_family, size_info, img_urls, lb_product, lb_salable_qty)

    return variation

# store lb color(id and label) in db
# params: color_id, color_label
def process_lb_colors(color_id, color_label):
    dbc = DBHelper()
    sql = "INSERT IGNORE INTO Lb_colors (id, color_label) VALUES (" + color_id + ", '" + color_label + "')"
    dbc.execute_insert(sql, 'lb_color', color_id)

# param: bs object
# returns a dictionary containing size information
def process_size_table(tbl_obj):
    headers = list()
    for th in tbl_obj.findAll('th'):
        headers.append(th.get_text())

    size_lsts = list()
    for tr in tbl_obj.findAll('tr'):
        tds = tr.findAll('td')
        if len(tds) > 0:
            child_lst= list()
            for td in tds:
                child_lst.append(td.get_text())
            size_lsts.append(child_lst)

    num = len(headers)
    size_dict = dict()
    for i in range(1, num):
        td_dict = dict()
        for lst in size_lsts:
            td_dict[lst[0]] = lst[i]
        size_dict[headers[i]] = td_dict

    return size_dict

def get_items_from_list(lst, brand_id):
    dbc = DBHelper()
    for url in lst:
        item = getItemInfo(url, brand_id)
        if item != None:
            dbc.insert_item(item)
            fetch_other_buyers(item)

            item_variations = getVariationInfo(url)
            if item_variations != None:
                for var in item_variations:
                    dbc.insert_lb_variation(var)

# takes one URL and return multiple item URLs it contains
def get_lb_urls(url):
    html = urlopen(url)
    logging.info("crawling %s: ", url)
    print(url)
    bsObj = BeautifulSoup(html, 'lxml')

    new_urls = list()
    for div in bsObj.find_all('div', {"class":"product-item-info"}):
        a = div.find('a', {"class":"product-item-photo"})

        limited_span = div.find('span', {"class":"lb-limitedstock"})
        if len(limited_span.get_text()) > 0:
            continue

        outofstock_span = div.find('span', {"class":"lb-outofstock"})
        if outofstock_span and len(outofstock_span.get_text()) > 0:
            continue
        new_urls.append(a['href'])

    return new_urls
# fetch LB items
def item_lb():
    # brand_id
    LB_ID = '3'

    crawler = Crawler()
    bsObj = crawler.getPage("https://www.lovebonito.com/sg/women/category/dresses")
    res_cont_div = bsObj.find('p', {"class":"product-count"}).string.strip()
    res_cont = int(re.sub(r'[^0-9]+', '', res_cont_div))
    print(res_cont)

    n = math.ceil(res_cont / 40)
    urls = list()
    # for i in range(n):
    #     urls = urls + get_lb_urls("https://www.lovebonito.com/sg/women/category/dresses?page=" + str(i + 1)

    urls = get_lb_urls("https://www.lovebonito.com/sg/women/category/dresses")

    get_items_from_list(urls, LB_ID)

# Enter Item manually
def item_enter():
    input_list = []
    try:
        url = input("Enter url (enter 0 to end): ")
        while url != "0":
            input_list.append(url)
            url = input("Enter url (enter 0 to end): ")
        brand_id = input("Enter brand ID: ")
        get_items_from_list(input_list, brand_id)
    except:
      print(input_list)

# test purpose only
def enter_addison():
    input_list = []
    input_list.append("https://www.lovebonito.com/sg/addison-shift-dress.html")
    get_items_from_list(input_list, "3")


# enter_addison()
item_lb()
