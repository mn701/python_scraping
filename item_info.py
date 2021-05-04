from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
import re

def getItemInfo(url):
    try:
        html = urlopen(url)
    except HTTPError as e:
        return None
    try:
        bsObj = BeautifulSoup(html, 'lxml')
        title = bsObj.h1.string
        sku = bsObj.find("span", {"itemprop":{"productID"}}).get_text()
        price = bsObj.find("meta", {"itemprop":{"price"}})['content']
        description = bsObj.find("div", {"itemprop":{"description"}}).get_text().strip()
        details = bsObj.find("div", {"class":"js-product-details_val"}).get_text().strip()
        color = bsObj.find("div", {"class":{"selected-color"}}).get_text().strip()

        sku_short = re.findall("\w+\d-\d+", sku)[0]

        print_item(sku_short, url, title, price, description, details)
        pritn_variant(sku, url, color)

        for img in bsObj.findAll("img", {"itemprop":"image"}):
            imglocation = img['src']
            imgname= re.findall("[\d, \w,-]+\.jpg", imglocation)[0]
            urlretrieve(imglocation, imgname)
    except AttributeError as e:
        return None


def print_item(product_id, url, product_name, price, description, details):
    print('product_id: '+ product_id + '\n' +
        'url: ' + url + '\n' +
        'product name: ' + product_name + '\n' +
        'price: ' + price + '\n' +
        'description: ' + description + '\n' +
        'details: ' + details+ '\n')
def pritn_variant(sku, url, color):
    print('variant sku: '+ sku + '\n' +
    'variant url: ' + url + '\n' +
    'color: ' + color)

print("Enter your url:")
url = input()
getItemInfo(url)
