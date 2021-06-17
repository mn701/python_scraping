from .myclasses import *
from .utilities import *

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

# download images in the folder
def save_imgs(brand_id, imglocations, folderName):
    # currPath = os.path.dirname(os.path.realpath(__file__))
    brandPath = img_config.img_folder[brand_id]
    reqPath = os.path.join(brandPath,folderName)
    if os.path.isdir(reqPath) == False:
        os.mkdir(reqPath)

    for imglocation in imglocations:
        imgname = re.findall("[\d, \w,-]+\.jpg", imglocation)[0]
        filename = os.path.join(reqPath, imgname)
        urlretrieve(imglocation, filename)
