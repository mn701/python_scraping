import csv
import pymysql

pw = os.environ.get('mysql_password')
conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock',user='root', passwd=pw, db='mysql')

cur = conn.cursor(pymysql.cursors.DictCursor)
cur.execute("USE shop")
cur.execute("SELECT * FROM variations where is_listed = null")
rows = cur.fetchall()

with open('newcolorsized.csv', 'w', newline='') as file:
    fieldnames = ['商品管理番号', '並び順', 'サイズ名称', '検索用サイズ', '色名称', '色系統', '在庫ステータス', '幅', '高さ', 'マチ']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({'商品管理番号': row['item_id'], '並び順': row['bm_order'], 'サイズ名称': row['size_name'],
        '検索用サイズ': row['bm_searchsize'], '色名称': row['bm_col_name'], '色系統': row['bm_col_family'], '在庫ステータス': row['has_stock'],
        '幅': 22.5, '高さ': 16.5, 'マチ': 9.5})

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

fp = open('file.csv', 'w')
myFile = csv.writer(fp)
myFile.writerow(rows)
fp.close()

with open('colsize_backstock.csv', 'w', newline='') as file:
    fieldnames = ['商品ID','並び順','サイズ名称','検索用サイズ','色名称','色系統','在庫ステータス']
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        # update 在庫ステータス to 1
        writer.writerow({'商品ID': row['buyma_id'], '並び順': row['bm_order'], 'サイズ名称': row['size_name'],
        '検索用サイズ': row['bm_searchsize'], '色名称': row['bm_col_name'], '色系統': row['bm_col_family'], '在庫ステータス': 1})
