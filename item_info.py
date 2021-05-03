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

        if len(bsObj.findAll("span", {"itemprop":{"productID"}})) > 0:
            sku = bsObj.find("span", {"itemprop":{"productID"}}).get_text()
        elif len(bsObj.findAll("span", {"class":{"product-id"}})) > 0:
            sku = bsObj.find("span", {"class":{"product-id"}}).get_text()
        price = bsObj.find("meta", {"itemprop":{"price"}})['content']
        description = bsObj.find("div", {"itemprop":{"description"}}).get_text()
        details = bsObj.find("div", {"class":"js-product-details_val"}).get_text()
        color = bsObj.find("div", {"class":{"selected-color"}}).get_text()

        for img in bsObj.findAll("img", {"itemprop":"image"}):
            imglocation = img['src']
            imgname= re.findall("[\d, \w,-]+\.jpg", imglocation)[0]
            urlretrieve(imglocation, imgname)
    except AttributeError as e:
        return None
    print('title: ' + title + '\n' +
        'sku: ' + sku + '\n' +
        'price: ' + price + '\n' +
        'description: ' + description + '\n' +
        'details: ' + details+ '\n' +
        'color: ' + color)
print("Enter your url:")
url = input()
getItemInfo(url)
