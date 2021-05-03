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
        description = bsObj.find("div", {"itemprop":{"description"}}).get_text()
        details = bsObj.find("div", {"class":"js-product-details_val"}).get_text()

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
        'details: ' + details)

getItemInfo("https://www.pedroshoes.com/sg/women/PW2-75060043_GREEN.html")
