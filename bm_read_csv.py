import pymysql
import pandas as pd
import os

# connect to db
pw = os.environ.get('mysql_password')
conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock',user='root', passwd=pw, db='mysql')
# cur = conn.cursor()
cur = conn.cursor(pymysql.cursors.DictCursor)
cur.execute("USE shop")
df = pd.read_csv('./downloaded/colorsizes.utf8.csv', dtype=str)

cur.execute("SELECT * FROM variations")
rows = cur.fetchall()

for row in rows:
    item_id_str = str(row['item_id'])
    col_name = row['bm_col_name']
    try:
        selected_variation = df.loc[(df['商品管理番号'] == item_id_str) & (df['色名称'] == col_name)]
        new_stock = selected_variation['在庫ステータス'].values[0]
        sql = "UPDATE variations SET has_stock = '" + new_stock + "' WHERE id = '" + str(row['id']) + "'"
        cur.execute(sql)
        if row['is_listed'] == None:
            bm_col_family = selected_variation['色系統'].values[0]
            sql = "UPDATE variations SET bm_col_family = '" + bm_col_family + "', is_listed = 1 WHERE id = '" + str(row['id']) + "'"
            cur.execute(sql)
        conn.commit()
    except IndexError:
        pass

df = pd.read_csv('./downloaded/items.utf8.csv', dtype=str)

cur.execute("SELECT * FROM Listed_items")
rows = cur.fetchall()
for row in rows:
    item_id_str = str(row['item_id'])

    try:
        selected_item = df.loc[(df['商品管理番号'] == item_id_str)]
        bm_id = selected_item['商品ID'].values[0]
        bm_control = selected_item['コントロール'].values[0]
        listed_name = selected_item['商品名'].values[0]
        sale_price = selected_item['単価'].values[0]
        bm_pcs = selected_item['買付可数量'].values[0]
        valid_till = selected_item['購入期限'].values[0]
        bm_has_refprice = selected_item['参考価格/通常出品価格'].values[0]

        bm_brand_id = selected_item['ブランド'].values[0]
        category = selected_item['カテゴリ'].values[0]
        season = selected_item['シーズン'].values[0]
        tags = selected_item['タグ'].values[0]
        supplier = selected_item['買付ショップ'].values[0]

        if bm_id != row['buyma_id']:
            sql = "UPDATE Listed_items SET buyma_id = '" + bm_id + "', "\
                + "listed_name = '" + listed_name + "', "\
                + "sale_price = '" + sale_price + "', "\
                + "bm_pcs = '" + bm_pcs + "', "\
                + "bm_has_refprice = '" + bm_has_refprice + "', "\
                + "bm_brand_id = '" + bm_brand_id + "', "\
                + "category = '" + category + "', "\
                + "season = '" + season + "', "\
                + "tags = '" + tags + "', "\
                + "supplier = '" + supplier + "' "\
                + " WHERE id = " + str(row['id'])
            cur.execute(sql)

        sql = "UPDATE Listed_items SET buyma_id = '" + bm_id + "', "\
            + "bm_control = '" + bm_control + "', "\
            + "valid_till = '" + valid_till + "' "\
            + " WHERE id = " + str(row['id'])
        cur.execute(sql)
        conn.commit()
    except IndexError:
        pass

cur.close()
conn.close()
