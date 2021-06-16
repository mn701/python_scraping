from PIL import Image, ImageDraw
import os
import shutil
import pymysql
from urllib.request import urlretrieve
import img_config
from classes.utilities import *
#
SQUARE_SIZE = 1536
SQUARE_HALF = 768

def create_top(images, brand):
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE))
    if len(images) == 4:
        create_im_from_4(images, brand, 100).save('100.png')
        create_im_from_4(images, brand, 150).save('150.png')
        create_im_from_4(images, brand, 200).save('200.png')
        create_im_from_4_white(images, brand, 100).save('100.png')
        create_im_from_4_white(images, brand, 150).save('150.png')
        create_im_from_4_white(images, brand, 200).save('200.png')
    elif len(images) == 3:
        create_im_3_ver(images, brand, 100).save('100v.png')
        create_im_3_ver(images, brand, 200).save('200v.png')
        create_im_3_hor(images, brand, 100).save('100h.png')
        create_im_3_hor(images, brand, 200).save('200h.png')
        create_im_3_hor(images, brand, 250).save('250h.png')
        create_im_3_hor(images, brand, 300).save('300h.png')
        create_im_3_sq(images, brand, 100).save('300sq.png')
    elif len(images) == 2:
        create_im_2_ver(images, brand, 100).save('100v.png')
        create_im_2_ver(images, brand, 200).save('200v.png')
        create_im_2_hor(images, brand, 100).save('100h.png')
        create_im_2_hor(images, brand, 200).save('200h.png')
        create_im_2_hor(images, brand, 250).save('250h.png')
        create_im_2_hor(images, brand, 300).save('300h.png')
        create_im_2_hor(images, brand, 350).save('350h.png')
    elif len(images) == 1:
        create_im_1(images[0], brand, 0).save('0.png')
        create_im_1(images[0], brand, 50).save('50.png')
        create_im_1(images[0], brand, 100).save('100.png')

def create_im_1(image, brand, crop_size=0):
    copy_im = Image.open(image).copy()
    crop_rectangle = (0 + crop_size, 192 + crop_size, 1152 - crop_size, 1344 - crop_size)
    cropped_im = copy_im.crop(crop_rectangle)
    resized = cropped_im.resize((SQUARE_SIZE, SQUARE_SIZE))

    # Add logo at top
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE))

    new_im = add_logo_top(resized, brand)

    # Add shop logo
    im_with_logo = add_shop_logo(new_im)

    return im_with_logo

def create_im_from_4(images, brand, crop_size=0):
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE))
    # Create a list for quaretersized images.
    quarter_images = []
    for imgfile in images:
        copy_im = Image.open(imgfile).copy()
        cropped_im = crop_bottom_square(copy_im, crop_size)
        quartersized_im = cropped_im.resize((SQUARE_HALF, SQUARE_HALF))
        quarter_images.append(quartersized_im)

    # Create a list of coordinates.
    coords = []
    for left in [0, SQUARE_HALF]:
        for top in [0, SQUARE_HALF]:
            coords.append((left, top))

    # Paste each quartersized image to new_im
    for quarter_im in quarter_images:
        new_im.paste(quarter_im, coords[quarter_images.index(quarter_im)])

    # Add logo at center
    new_im = add_logo_center(new_im, brand)

    # Add shop logo
    im_with_logo = add_shop_logo(new_im)

    return im_with_logo

def create_im_from_4_white(images, brand, crop_size=0):
    MARGIN = 20
    LOGO_HEIGHT_HALF = int(116/2)
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE), (255, 255, 255))
    # Create a list for quaretersized images.
    quarter_images = []
    side = SQUARE_HALF - MARGIN * 2 - LOGO_HEIGHT_HALF
    for imgfile in images:
        copy_im = Image.open(imgfile).copy()
        cropped_im = crop_bottom_square(copy_im, crop_size)

        quartersized_im = cropped_im.resize((side, side))
        quartersized_im = add_corners(quartersized_im)
        quarter_images.append(quartersized_im)

    # Create a list of coordinates.
    coords = []
    for left in [int(SQUARE_HALF / 2 - side / 2), SQUARE_HALF + int(SQUARE_HALF / 2 - side / 2)]:
        for top in [0 + MARGIN, SQUARE_HALF + MARGIN + LOGO_HEIGHT_HALF]:
            coords.append((left, top))

    # Paste each quartersized image to new_im
    for quarter_im in quarter_images:
        new_im.paste(quarter_im, coords[quarter_images.index(quarter_im)], quarter_im)

    # Add logo at center
    new_im = add_logo_center(new_im, brand)

    # Add shop logo
    im_with_logo = add_shop_logo(new_im)

    return im_with_logo

def create_im_3_sq(images, brand, crop_size=0):
    MARGIN = 20
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE), (255, 255, 255))
    # Create a list for quaretersized images.
    quarter_images = []
    side = SQUARE_HALF - MARGIN * 2
    for imgfile in images:
        copy_im = Image.open(imgfile).copy()
        cropped_im = crop_bottom_square(copy_im, crop_size)

        quartersized_im = cropped_im.resize((side, side))
        quartersized_im = add_corners(quartersized_im)
        quarter_images.append(quartersized_im)

    # Create a list of coordinates.
    coords = []
    coords.append((int(SQUARE_HALF - side / 2), MARGIN))
    coords.append((int(SQUARE_HALF / 2 - side / 2), SQUARE_HALF))
    coords.append((SQUARE_HALF + int(SQUARE_HALF / 2 - side / 2), SQUARE_HALF))

    # Paste each quartersized image to new_im
    for quarter_im in quarter_images:
        new_im.paste(quarter_im, coords[quarter_images.index(quarter_im)], quarter_im)

    # Add logo at center
    new_im = add_logo_topleft(new_im, brand)

    # Add shop logo
    im_with_logo = add_shop_logo(new_im)

    return im_with_logo

def create_im_2_ver(images, brand, crop_x_size=100):
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE),(236, 236, 236))
    new_width = SQUARE_HALF
    # Create a new folder to save resized images.
    os.makedirs('vresized', exist_ok=True)

    # Create a list for two vertical images.
    resized_images = get_resized_images_v(images, crop_x_size, new_width)
    new_height = resized_images[0].size[1]

    # Create a list of coordinates.
    coords = []
    for left in [0, SQUARE_HALF]:
        top = SQUARE_HALF - int(new_height / 2)
        coords.append((left, top))

    # Paste each quartersized image to new_im
    for im in resized_images:
        new_im.paste(im, coords[resized_images.index(im)])

    # Add logo at top
    new_im = add_logo_top(new_im, brand)

    # Add shop logo
    im_with_logo = add_shop_logo(new_im)

    return im_with_logo

def create_im_3_ver(images, brand, crop_x_size=100):
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE), (236, 236, 236))
    new_width = int(SQUARE_SIZE / 3)
    # Create a new folder to save resized images.
    os.makedirs('vresized', exist_ok=True)

    # Create a list for 3 vertical images.
    resized_images = get_resized_images_v(images, crop_x_size, new_width)
    new_height = resized_images[0].size[1]

    # Create a list of coordinates.
    coords = []
    for left in [0, new_width, int(new_width * 2)]:
        top = SQUARE_HALF - int(new_height / 2)
        coords.append((left, top))

    # Paste each quartersized image to new_im
    for im in resized_images:
        new_im.paste(im, coords[resized_images.index(im)])

    # Add logo at top
    new_im = add_logo_top(new_im, brand)

    # Add shop logo
    im_with_logo = add_shop_logo(new_im)

    return im_with_logo

def create_im_2_hor(images, brand, crop_y_size):
    MARGIN = 50
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE), (255, 255, 255))
    # if bg_color == 1:
    #     new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE), (236, 236, 236))
    # elif bg_color == 2:
    #     new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE), (233, 229, 228))

    new_height = int(SQUARE_HALF - 112/2 - MARGIN * 2)
    # Create a new folder to save resized images.
    os.makedirs('hresized', exist_ok=True)

    # Create a list for two horizontal images.
    resized_images = get_resized_images_h(images, crop_y_size, new_height)
    new_width = resized_images[0].size[0]

    # Create a list of coordinates.
    coords = []
    for top in [0 + MARGIN, SQUARE_HALF + MARGIN + int(112/2)]:
        left = SQUARE_HALF - int(new_width / 2)
        coords.append((left, top))

    # Paste each quartersized image to new_im
    for im in resized_images:
        new_im.paste(im, coords[resized_images.index(im)], im)

    # save
    new_im.save(os.path.join('hresized', 'wologo.png'))

    # Add logo at center
    new_im = add_logo_center(new_im, brand)

    # Add shop logo
    im_with_logo = add_shop_logo(new_im)

    return im_with_logo

def create_im_3_hor(images, brand, crop_y_size):
    MARGIN = 10
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE), (255, 255, 255))
    new_height = int((SQUARE_SIZE - MARGIN * 4)/ 3)

    # Create a new folder to save resized images.
    os.makedirs('hresized', exist_ok=True)

    # Create a list for three horizontal images.
    resized_images = get_resized_images_h(images, crop_y_size - MARGIN, new_height)
    new_width = resized_images[0].size[0]

    # Create a list of coordinates.
    coords = []
    for top in [MARGIN, int(new_height + MARGIN * 2), int(new_height * 2 + MARGIN * 3)]:
        left = 600
        coords.append((left, top))

    # Paste each quartersized image to new_im
    for im in resized_images:
        new_im.paste(im, coords[resized_images.index(im)], im)

    # save
    new_im.save(os.path.join('hresized', 'wologo.png'))

    # Add logo on the left
    new_im = add_logo_left(new_im, brand)

    # Add shop logo
    im_with_logo = add_shop_logo(new_im)

    return im_with_logo

def create_im_3_hor_len(images, brand, crop_y_size, len_crop, bg_color):
    MARGIN = 10
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE), (255, 255, 255))
    new_height = int((SQUARE_SIZE - MARGIN * 4)/ 3)
    # Create a new folder to save resized images.
    os.makedirs('hresized', exist_ok=True)

    # Create a list for three horizontal images.
    resized_images = get_resized_images_h_len(images, crop_y_size, len_crop, new_height)
    new_width = resized_images[0].size[0]

    # Create a list of coordinates.
    coords = []
    for top in [MARGIN, int(new_height + MARGIN * 2), int(new_height * 2 + MARGIN * 3)]:
        left = 600
        coords.append((left, top))

    # Paste each quartersized image to new_im
    for im in resized_images:
        new_im.paste(im, coords[resized_images.index(im)], im)

    new_im.save(os.path.join('hresized', 'nobg.png'))
    # Add logo on the left
    new_im = add_logo_left(new_im, brand)

    # Add shop logo
    im_with_logo = add_shop_logo(new_im)

    return im_with_logo

def get_resized_images_v(images, crop_x_size, new_width):
    resized_images = []
    for imgfile in images:
        copy_im = Image.open(imgfile).copy()
        cropped_im = crop_x(copy_im, crop_x_size)
        cropped_width, cropped_height = cropped_im.size
        new_height = int(new_width * cropped_height / cropped_width)
        resized_im = cropped_im.resize((new_width, new_height))
        resized_im.save(os.path.join('vresized', imgfile))
        resized_images.append(resized_im)
    return resized_images

def get_resized_images_h(images, crop_y_size, new_height):
    resized_images = []
    for imgfile in images:
        copy_im = Image.open(imgfile).copy()
        cropped_im = crop_y_bottom(copy_im, crop_y_size)
        cropped_width, cropped_height = cropped_im.size
        new_width = int(new_height * cropped_width / cropped_height)
        resized_im = cropped_im.resize((new_width, new_height))
        resized_im.save(os.path.join('hresized', imgfile))
        resized_im = add_corners(resized_im)
        resized_images.append(resized_im)
    return resized_images

def get_resized_images_h_len(images, crop_y_size, len_crop, new_height):
    resized_images = []
    for imgfile in images:
        copy_im = Image.open(imgfile).copy()
        cropped_im = crop_y(copy_im, crop_y_size, len_crop)
        cropped_width, cropped_height = cropped_im.size
        new_width = int(new_height * cropped_width / cropped_height)
        resized_im = cropped_im.resize((new_width, new_height))
        resized_im.save(os.path.join('hresized', imgfile))
        resized_im = add_corners(resized_im)
        resized_images.append(resized_im)
    return resized_images

def crop_x(im, x_crop):
    x, y = im.size
    crop_rectangle = (x_crop, 0, int(x - x_crop), y)
    cropped_im = im.crop(crop_rectangle)
    return cropped_im

def crop_y(im, y_crop, len_crop):
    x, y = im.size
    crop_rectangle = (0, y_crop, x, int(y_crop + len_crop))
    cropped_im = im.crop(crop_rectangle)
    return cropped_im

def crop_y_bottom(im, crop_size):
    x, y = im.size
    crop_square = (0, y - x, x, y)
    square_im = im.crop(crop_square)
    sq_x, sq_y = square_im.size
    crop_rectangle = (0, crop_size, sq_x, int(sq_y - 100))
    cropped_im = square_im.crop(crop_rectangle)
    return cropped_im

def crop_bottom_square(im, crop_size):
    x, y = im.size
    crop_square = (0, y - x, x, y)
    square_im = im.crop(crop_square)
    sq_x, sq_y = square_im.size
    crop_rectangle = (crop_size, crop_size, int(sq_x - crop_size), int(sq_y - crop_size))
    cropped_im = square_im.crop(crop_rectangle)
    return cropped_im

def add_shop_logo(image):
    # Adding logo image
    logo_im = Image.open(img_config.LOGO_SHOP)
    logo_im = logo_im.resize((267, 267))
    logoWidth, logoHeight = logo_im.size
    width, height = image.size

    # Paste logo on botom left
    image.paste(logo_im, (width-logoWidth, height-logoHeight), logo_im)

    return image

def add_logo_top(image, brand):
    # Adding logo image
    if brand == 1:
        # Adding logo image
        logo_im = Image.open(img_config.CK_LOGO).convert("RGBA")
        logo_im = logo_im.resize((400, 400))
        logoWidth, logoHeight = logo_im.size
        width, height = image.size

        # Paste logo on botom left
        image.paste(logo_im, (568, 0), logo_im)

        return image
    elif brand == 2:
        logo_im = Image.open(img_config.PEDRO_LOGO).convert("RGBA")
        logo_im = logo_im.resize((600, 112))
        logoWidth, logoHeight = logo_im.size
        width, height = image.size

        # Paste logo on botom left
        image.paste(logo_im, (468, 20), logo_im)

    elif brand == 3:
        logo_im = Image.open(img_config.LB_LOGO).convert("RGBA")
        logo_im = logo_im.resize((400, 400))
        logoWidth, logoHeight = logo_im.size
        width, height = image.size

        # Paste logo on botom left
        image.paste(logo_im, (568, 0), logo_im)

    return image

# def add_cklogo_top(image):
#     # Adding logo image
#     logo_im = Image.open(img_config.CK_LOGO).convert("RGBA")
#     logo_im = logo_im.resize((400, 400))
#     logoWidth, logoHeight = logo_im.size
#     width, height = image.size
#
#     # Paste logo on botom left
#     image.paste(logo_im, (568, 0), logo_im)
#
#     return image

def add_logo_center(image, brand):
    # Adding logo image
    if brand == 1:
        logo_im = Image.open(img_config.CK_THIN_LOGO).convert("RGBA")
        logo_im = logo_im.resize((1490, 100))
    elif brand == 2:
        logo_im = Image.open(img_config.PEDRO_LOGO).convert("RGBA")
        logo_im = logo_im.resize((600, 112))
    elif brand == 3:
        logo_im = Image.open(img_config.LB_LOGO).convert("RGBA")
        logo_im = logo_im.resize((400, 400))

    logoWidth, logoHeight = logo_im.size
    width, height = image.size

    # Paste logo on botom left
    image.paste(logo_im, ((int(width/2) - int(logoWidth/2)), (int(height/2) - int(logoHeight/2))), logo_im)

    return image

def add_logo_left(image, brand):
    # Adding logo image
    if brand == 1:
        logo_im = Image.open(img_config.CK_LOGO).convert("RGBA")
        logo_im = logo_im.resize((400, 400))
        # Paste logo on botom left
        image.paste(logo_im, (0, 568), logo_im)
    elif brand == 2:
        logo_im = Image.open(img_config.PEDRO_LOGO).convert("RGBA")
        logo_im = logo_im.resize((600, 112))
        # Paste logo on botom left
        image.paste(logo_im, (15, 712), logo_im)
    elif brand == 3:
        logo_im = Image.open(img_config.LB_LOGO).convert("RGBA")
        logo_im = logo_im.resize((400, 400))
        # Paste logo on botom left
        image.paste(logo_im, (0, 568), logo_im)

    return image

def add_logo_topleft(image, brand):
    # Adding logo image
    if brand == 1:
        logo_im = Image.open(img_config.CK_LOGO).convert("RGBA")
        logo_im = logo_im.resize((300, 300))
        # Paste logo on botom left
        image.paste(logo_im, (0, 20), logo_im)
    elif brand == 2:
        logo_im = Image.open(img_config.PEDRO_LOGO).convert("RGBA")
        logo_im = logo_im.resize((600, 112))
        # Paste logo on botom left
        image.paste(logo_im, (15, 20), logo_im)
    elif brand == 3:
        logo_im = Image.open(img_config.LB_LOGO).convert("RGBA")
        logo_im = logo_im.resize((300, 300))
        # Paste logo on botom left
        image.paste(logo_im, (0, 20), logo_im)

    return image

def add_corners(im):
    rad = 50
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im

def get_images(brand):
    images = []
    for filename in os.listdir():
        if (filename.endswith('.jpg') or filename.endswith('.jpeg')):
            images.append(filename)

    if len(images) > 0:
        create_top(images, brand)

# mask directory name
# directory = os.getcwd()
# for filename in os.scandir(directory):
#     if os.path.isdir(filename) and ('PW' in str(filename) or 'CK' in str(filename)):
#         os.chdir(filename.path)
#         if 'PW' in str(filename):
#             brand = 2
#         elif 'CK' in str(filename):
#             brand = 1
#         if not os.path.exists('top'):
#             os.mkdir('top')
#             for filename in os.listdir():
#                 if filename.endswith('-1.jpg') or filename.endswith('-1.jpeg'):
#                     shutil.move(filename, os.path.join('top', filename))
#         if len([name for name in os.listdir() if os.path.isfile(name)]) > 19:
#             if not os.path.exists('extra'):
#                 os.mkdir('extra')
#             for filename in os.listdir():
#                 if filename.endswith('-8.jpg'):
#                     shutil.move(filename, os.path.join('extra', filename))
#         os.chdir('top')
#         get_images(brand)

# pw = pwf.PW
# conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock',user='root', passwd=pw, db='mysql')
#
# cur = conn.cursor(pymysql.cursors.DictCursor)
# cur.execute("USE shop")
#
# sql = "SELECT * FROM Items WHERE Items.listed IN (3, 4)"
# cur.execute(sql)
# rows = cur.fetchall()
# for row in rows:
#     str_item_id = str(row['item_id'])
#     brand_id = row['brand_id']
#     if os.path.isdir(str_item_id) == False:
#         os.mkdir(str_item_id)
#     sql = "SELECT Images.* FROM Images, Variations WHERE Images.variation_id = Variations.id AND Images.item_id = " \
#     + str_item_id + " ORDER BY Variations.color_code"
#     cur.execute(sql)
#     img_rows = cur.fetchall()
#     imglist = list()
#     for img_row in img_rows:
#         if img_row['img_name'].endswith('-1.jpg'):
#             filename = os.path.join(str_item_id, img_row['img_name'])
#             imgfile = urlretrieve(img_row['img_url'], filename)
#             # imglist.append(imgfile)
#
#     os.chdir(str_item_id)
#     get_images(brand_id)
#     os.chdir('..')
