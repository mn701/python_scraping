import csv
import pymysql
from datetime import date
from dateutil.relativedelta import relativedelta
import os
import json

pw = os.environ.get('mysql_password')
conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock',user='root', passwd=pw, db='mysql')
cur = conn.cursor(pymysql.cursors.DictCursor)
cur.execute("USE shop")

# Create CSV for new colorsizes to upload
sql = "SELECT Variations.*, Items.listed, Listed_items.category FROM Items, Variations, Listed_items \
WHERE Items.item_id = Variations.item_id AND Listed_items.item_id = Variations.item_id AND \
Items.listed = 3 AND has_stock = 1 AND availability IN ('In Stock', 'Low in Stock') \
AND Variations.id = 1085"
cur.execute(sql)
rows = cur.fetchall()

with open('colorsizes.csv', 'w', newline='') as file:
    fieldnames = ['商品管理番号', '並び順', 'サイズ名称', 'サイズ単位', '検索用サイズ', '色名称', '色系統', '在庫ステータス', '幅', '高さ', 'マチ', '縦', '横', '厚み']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        new_variation = {'商品管理番号': row['item_id'], '並び順': row['bm_order'], 'サイズ名称': row['size_name'],
        '検索用サイズ': row['bm_searchsize'], '色名称': row['bm_col_name'], '色系統': row['bm_col_family'], '在庫ステータス': row['has_stock']}

        dict_size_info = dict()
        if row['size_info'] != None:
            dict_size_info = json.loads(row['size_info'])

        if row['category'] == 3169 or row['category'] == 3111:
            new_variation['縦'] = dict_size_info['Height']
            new_variation['横'] = dict_size_info['Width']
            new_variation['厚み'] = dict_size_info['Depth']
        else:
            new_variation['高さ'] = dict_size_info['Height']
            new_variation['幅'] = dict_size_info['Width']
            new_variation['マチ'] = dict_size_info['Depth']

        writer.writerow(new_variation)

# Create CSV for new items
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
    new_listing = {}
    # default values
    new_listing['コントロール'] = '公開'
    new_listing['買付可数量'] = 2
    new_listing['参考価格/通常出品価格'] = 0
    new_listing['配送方法'] = COURIER
    new_listing['買付エリア'] = AREA_CODE
    new_listing['買付都市'] = 0
    new_listing['発送エリア'] = AREA_CODE
    new_listing['発送都市'] = 0
    new_listing['関税込み'] = 2

    one_mon_later = date.today() + relativedelta(months=1)
    valid_till = one_mon_later.strftime("%Y-%m-%d")
    new_listing['購入期限'] = valid_till

    for row in rows:
        if row['brand_id'] == 1:
            new_listing['ブランド'] = 827
            new_listing['買付ショップ'] = CK_SHOP
            new_listing['買付先名1'] = CK_SHOP
        elif row['brand_id'] == 2:
            new_listing['ブランド'] = 13301
            new_listing['買付ショップ'] = PW_SHOP
            new_listing['買付先名1'] = PW_SHOP

        new_listing['商品管理番号'] = row['item_id']
        new_listing['商品名'] = row['listed_name']
        new_listing['カテゴリ'] = row['category']
        new_listing['シーズン'] = row['season']
        new_listing['単価'] = row['sale_price']
        new_listing['商品コメント'] = row['comment']
        new_listing['色サイズ補足'] = row['reference']
        new_listing['タグ'] = row['tags']

        cur.execute("SELECT id, item_id, img_urls FROM variations where item_id = 204 order by color_code")
        rows_v = cur.fetchall()

        lst_urls = list()
        for row_v in rows_v:
            urls = row_v['img_urls']
            lst_urls.append(urls.split(", "))

        num_colors = len(lst_urls) # 3
        sum = 0
        for lst in lst_urls:
            sum += len(lst) - 1
        q = divmod(sum, num_colors)[0] # 6

        lst19 = list()
        for i in range(q):
            for lst in lst_urls:
                lst19.append(lst[i + 1])

        new_listing['商品イメージ1'] = lst19[0] if 0 < len(lst19) else None
        new_listing['商品イメージ2'] = lst19[1] if 1 < len(lst19) else None
        new_listing['商品イメージ3'] = lst19[2] if 2 < len(lst19) else None
        new_listing['商品イメージ4'] = lst19[3] if 3 < len(lst19) else None
        new_listing['商品イメージ5'] = lst19[4] if 4 < len(lst19) else None
        new_listing['商品イメージ6'] = lst19[5] if 5 < len(lst19) else None
        new_listing['商品イメージ7'] = lst19[6] if 6 < len(lst19) else None
        new_listing['商品イメージ8'] = lst19[7] if 7 < len(lst19) else None
        new_listing['商品イメージ9'] = lst19[8] if 8 < len(lst19) else None
        new_listing['商品イメージ10'] = lst19[9] if 9 < len(lst19) else None
        new_listing['商品イメージ11'] = lst19[10] if 10 < len(lst19) else None
        new_listing['商品イメージ12'] = lst19[11] if 11 < len(lst19) else None
        new_listing['商品イメージ13'] = lst19[12] if 12 < len(lst19) else None
        new_listing['商品イメージ14'] = lst19[13] if 13 < len(lst19) else None
        new_listing['商品イメージ15'] = lst19[14] if 14 < len(lst19) else None
        new_listing['商品イメージ16'] = lst19[15] if 15 < len(lst19) else None
        new_listing['商品イメージ17'] = lst19[16] if 16 < len(lst19) else None
        new_listing['商品イメージ18'] = lst19[17] if 17 < len(lst19) else None
        new_listing['商品イメージ19'] = lst19[18] if 18 < len(lst19) else None

        writer.writerow(new_listing)

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
