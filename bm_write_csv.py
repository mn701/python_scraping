import csv
import pymysql
from datetime import date
from dateutil.relativedelta import relativedelta
import os

pw = os.environ.get('mysql_password')
conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock',user='root', passwd=pw, db='mysql')
cur = conn.cursor(pymysql.cursors.DictCursor)
cur.execute("USE shop")

sql = "SELECT * FROM Items, Variations \
WHERE Items.item_id = Variations.item_id AND Items.listed = 3 AND \
has_stock = 1 AND availability IN ('In Stock', 'Low in Stock')"
cur.execute(sql)
rows = cur.fetchall()

with open('colorsizes.csv', 'w', newline='') as file:
    fieldnames = ['商品管理番号', '並び順', 'サイズ名称', 'サイズ単位', '検索用サイズ', '色名称', '色系統', '在庫ステータス', '縦', '横', '厚み']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({'商品管理番号': row['item_id'], '並び順': row['bm_order'], 'サイズ名称': row['size_name'],
        '検索用サイズ': row['bm_searchsize'], '色名称': row['bm_col_name'], '色系統': row['bm_col_family'], '在庫ステータス': row['has_stock'],
        '縦': 10.3, '横': 13, '厚み': 4})

sql = "SELECT Listed_items.*, Items.listed, Items.brand_id FROM Items, Listed_items \
WHERE listed = 3 AND Items.item_id = Listed_items.item_id AND Items.item_id = 204"
cur.execute(sql)
rows = cur.fetchall()

AREA_CODE = 2002005
COURIER = 677239
CK_SHOP = 'Charles&Keith直営店'
PW_SHOP = 'Pedro直営店'

with open('items.csv', 'w', newline='') as file:
    fieldnames = ['商品ID','商品管理番号','コントロール','商品名','ブランド','カテゴリ','シーズン','単価','買付可数量', \
    '購入期限','参考価格/通常出品価格', '商品コメント', '色サイズ補足', 'タグ', '配送方法', '買付エリア', '買付都市', '買付ショップ', \
    '発送エリア','発送都市','関税込み', '商品イメージ1','商品イメージ2','商品イメージ3','商品イメージ4','商品イメージ5', \
    '商品イメージ6','商品イメージ7','商品イメージ8','商品イメージ9','商品イメージ10','商品イメージ11','商品イメージ12','商品イメージ13', \
    '商品イメージ14','商品イメージ15','商品イメージ16','商品イメージ17','商品イメージ18','商品イメージ19','商品イメージ20','買付先名1']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    new_listings = {}
    # default values
    new_listings['コントロール'] = '公開'
    new_listings['買付可数量'] = 2
    new_listings['参考価格/通常出品価格'] = 0
    new_listings['配送方法'] = COURIER
    new_listings['買付エリア'] = AREA_CODE
    new_listings['買付都市'] = 0
    new_listings['発送エリア'] = AREA_CODE
    new_listings['発送都市'] = 0
    new_listings['関税込み'] = 2

    one_mon_later = date.today() + relativedelta(months=1)
    valid_till = one_mon_later.strftime("%Y-%m-%d")
    new_listings['購入期限'] = valid_till

    for row in rows:
        if row['brand_id'] == 1:
            new_listings['ブランド'] = 827
            new_listings['買付ショップ'] = CK_SHOP
            new_listings['買付先名1'] = CK_SHOP
        elif row['brand_id'] == 2:
            new_listings['ブランド'] = 13301
            new_listings['買付ショップ'] = PW_SHOP
            new_listings['買付先名1'] = PW_SHOP

        new_listings['商品管理番号'] = row['item_id']
        new_listings['商品名'] = row['listed_name']
        new_listings['カテゴリ'] = row['category']
        new_listings['シーズン'] = row['season']
        new_listings['単価'] = row['sale_price']
        new_listings['商品コメント'] = row['comment']
        new_listings['色サイズ補足'] = row['reference']
        new_listings['タグ'] = row['tags']

        new_listings['商品イメージ1'] = 'https://www.charleskeith.com/dw/image/v2/BCWJ_PRD/on/demandware.static/-/Sites-ck-products/default/dw4ae864e9/images/hi-res/2021-L2-CK6-10840224-01-1.jpg?sw=1152&sh=1536'

        writer.writerow(new_listings)



    # '商品イメージ1','商品イメージ2','商品イメージ3','商品イメージ4','商品イメージ5', \
    # '商品イメージ6','商品イメージ7','商品イメージ8','商品イメージ9','商品イメージ10','商品イメージ11','商品イメージ12','商品イメージ13', \
    # '商品イメージ14','商品イメージ15','商品イメージ16','商品イメージ17','商品イメージ18','商品イメージ19','商品イメージ20',

# fetch variations unavailable, yet listed on bm
sql = "SELECT Variations.*, listed_items.buyma_id FROM Variations, listed_items \
WHERE listed_items.item_id = Variations.item_id AND has_stock = 1 AND \
availability NOT IN ( 'In Stock', 'Low in Stock' )"
cur.execute(sql)
rows = cur.fetchall()

with open('colsize_outofstock.csv', 'w', newline='') as file:
    fieldnames = ['商品ID','並び順','サイズ名称','検索用サイズ','色名称','色系統','在庫ステータス']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        # update 在庫ステータス to 0
        writer.writerow({'商品ID': row['buyma_id'], '並び順': row['bm_order'], 'サイズ名称': row['size_name'],
        '検索用サイズ': row['bm_searchsize'], '色名称': row['bm_col_name'], '色系統': row['bm_col_family'], '在庫ステータス': 0})

# fetch variations back to available, and not listed
sql = "SELECT Variations.*, listed_items.buyma_id FROM Variations, listed_items \
WHERE listed_items.item_id = Variations.item_id AND has_stock = 0 AND is_listed IS NOT NULL \
AND availability IN ( 'In Stock', 'Low in Stock' )"
cur.execute(sql)
rows = cur.fetchall()



with open('colsize_backstock.csv', 'w', newline='') as file:
    fieldnames = ['商品ID','並び順','サイズ名称','検索用サイズ','色名称','色系統','在庫ステータス']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        # update 在庫ステータス to 1
        writer.writerow({'商品ID': row['buyma_id'], '並び順': row['bm_order'], 'サイズ名称': row['size_name'],
        '検索用サイズ': row['bm_searchsize'], '色名称': row['bm_col_name'], '色系統': row['bm_col_family'], '在庫ステータス': 1})

def get_images(item_id):
    sql = "SELECT img_urls FROM variations WHERE item_id = " + str(item_id)
    cur.execute(sql)
    rows = cur.fetchall()
    fp = open('file.csv', 'w')
    myFile = csv.writer(fp)
    myFile.writerow(rows)
    fp.close()

    # for row in rows:
    #     url_lst = row[0].split(", ")
    #     print(url_lst)

get_images(204)
