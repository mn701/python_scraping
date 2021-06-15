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
    def __init__(self, item_id, sku, url, color_code, size_name, availability, has_stock, bm_col_name, bm_col_family, size_info, \
    img_urls):
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
        self.img_urls = img_urls

class Lb_Variation(Variation):
    def __init__(self, item_id, sku, url, color_code, size_name, availability, has_stock, bm_col_name, bm_col_family, size_info, \
    img_urls, lb_product, lb_salable_qty):
        super().__init__(item_id, sku, url, color_code, size_name, availability, has_stock, bm_col_name, bm_col_family, size_info, \
        img_urls)
        self.lb_product = lb_product
        self.lb_salable_qty = lb_salable_qty


# Holds information about listing from other buyers for an Item  -> tbl Buyer_price
class Buyer_price:
    def __init__(self, item_id, buyer, price, url):
        self.item_id = item_id
        self.buyer = buyer
        self.price = price
        self.url = url
