from PIL import Image
import os
import shutil

SQUARE_SIZE = 1536
SQUARE_HALF = 768
LOGO_SHOP = 'logo_200x200.png'
PEDRO_LOGO = 'logo.png'

def create_top(images, brand):
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE))
    if len(images) == 4:
        create_im_from_4(images, brand, 100).save('100.png')
        create_im_from_4(images, brand, 150).save('150.png')
        create_im_from_4(images, brand, 200).save('200.png')
    elif len(images) == 3:
        create_im_3_ver(images, brand, 100).save('100v.png')
        create_im_3_ver(images, brand, 200).save('200v.png')
        create_im_3_hor(images, brand, 100).save('100h.png')
        create_im_3_hor(images, brand, 200).save('200h.png')
        create_im_3_hor(images, brand, 250).save('250h.png')
        create_im_3_hor(images, brand, 300).save('300h.png')
    elif len(images) == 2:
        create_im_2_ver(images, brand, 100).save('100v.png')
        create_im_2_ver(images, brand, 200).save('200v.png')
        create_im_2_hor(images, brand, 100).save('100h.png')
        create_im_2_hor(images, brand, 200).save('200h.png')
        create_im_2_hor(images, brand, 250).save('250h.png')
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
    if brand == 1:
        new_im = add_cklogo_top(resized)
    elif brand == 2:
        new_im = add_logo_top(resized)

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
    if brand == 1:
        new_im = add_cklogo_top(new_im)
    elif brand == 2:
        new_im = add_logo_top(new_im)

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
    if brand == 1:
        new_im = add_cklogo_top(new_im)
    elif brand == 2:
        new_im = add_logo_top(new_im)

    # Add shop logo
    im_with_logo = add_shop_logo(new_im)

    return im_with_logo

def create_im_2_hor(images, brand, crop_y_size=100):
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE),(236, 236, 236))
    new_height = SQUARE_HALF
    # Create a new folder to save resized images.
    os.makedirs('hresized', exist_ok=True)

    # Create a list for two horizontal images.
    resized_images = get_resized_images_h(images, crop_y_size, new_height)
    new_width = resized_images[0].size[0]

    # Create a list of coordinates.
    coords = []
    for top in [0, SQUARE_HALF]:
        left = SQUARE_HALF - int(new_width / 2)
        coords.append((left, top))

    # Paste each quartersized image to new_im
    for im in resized_images:
        new_im.paste(im, coords[resized_images.index(im)])

    # Add logo at center
    new_im = add_logo_center(new_im, brand)

    # Add shop logo
    im_with_logo = add_shop_logo(new_im)

    return im_with_logo

def create_im_3_hor(images, brand, crop_y_size=100):
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE), (236, 236, 236))
    new_height = int(SQUARE_SIZE / 3)
    # Create a new folder to save resized images.
    os.makedirs('hresized', exist_ok=True)

    # Create a list for three horizontal images.
    resized_images = get_resized_images_h(images, crop_y_size, new_height)
    new_width = resized_images[0].size[0]

    # Create a list of coordinates.
    coords = []
    for top in [0, new_height, int(new_height * 2)]:
        left = SQUARE_SIZE - new_width
        coords.append((left, top))

    # Paste each quartersized image to new_im
    for im in resized_images:
        new_im.paste(im, coords[resized_images.index(im)])

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
        resized_images.append(resized_im)
    return resized_images

def crop_x(im, x_crop):
    x, y = im.size
    crop_rectangle = (x_crop, 0, int(x - x_crop), y)
    cropped_im = im.crop(crop_rectangle)
    return cropped_im

def crop_y(im, y_crop):
    x, y = im.size
    crop_rectangle = (0, y_crop, x, int(y - y_crop))
    cropped_im = im.crop(crop_rectangle)
    return cropped_im

def crop_y_bottom(im, crop_size):
    x, y = im.size
    crop_square = (0, y - x, x, y)
    square_im = im.crop(crop_square)
    sq_x, sq_y = square_im.size
    crop_rectangle = (0, crop_size, sq_x, int(sq_y - crop_size*0.8))
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
    logo_im = Image.open(LOGO_SHOP)
    logo_im = logo_im.resize((267, 267))
    logoWidth, logoHeight = logo_im.size
    width, height = image.size

    # Paste logo on botom left
    image.paste(logo_im, (width-logoWidth, height-logoHeight), logo_im)

    return image

def add_logo_top(image):
    # Adding logo image
    logo_im = Image.open(PEDRO_LOGO).convert("RGBA")
    logo_im = logo_im.resize((600, 112))
    logoWidth, logoHeight = logo_im.size
    width, height = image.size

    # Paste logo on botom left
    image.paste(logo_im, (468, 20), logo_im)

    return image

def add_logo_center(image, brand):
    # Adding logo image
    if brand == 2:
        logo_im = Image.open(PEDRO_LOGO).convert("RGBA")
        logo_im = logo_im.resize((600, 112))
    else:
        logo_im = Image.open(CK_LOGO).convert("RGBA")
        logo_im = logo_im.resize((400, 400))

    logoWidth, logoHeight = logo_im.size
    width, height = image.size

    # Paste logo on botom left
    image.paste(logo_im, ((int(width/2) - int(logoWidth/2)), (int(height/2) - int(logoHeight/2))), logo_im)

    return image

def add_logo_left(image, brand):
    # Adding logo image
    if brand == 1:
        logo_im = Image.open(CK_LOGO).convert("RGBA")
        logo_im = logo_im.resize((400, 400))
        # Paste logo on botom left
        image.paste(logo_im, (0, 568), logo_im)
    else:
        logo_im = Image.open(PEDRO_LOGO).convert("RGBA")
        logo_im = logo_im.resize((600, 112))
        # Paste logo on botom left
        image.paste(logo_im, (15, 712), logo_im)

    return image

def add_cklogo_top(image):
    # Adding logo image
    logo_im = Image.open(CK_LOGO).convert("RGBA")
    logo_im = logo_im.resize((400, 400))
    logoWidth, logoHeight = logo_im.size
    width, height = image.size

    # Paste logo on botom left
    image.paste(logo_im, (568, 0), logo_im)

    return image


def get_images(brand):
    images = []
    for filename in os.listdir():
        if (filename.endswith('.jpg') or filename.endswith('.jpg')) and filename.startswith('20'):
            images.append(filename)

    if len(images) > 0:
        create_top(images, brand)

# mask directory name
directory = os.getcwd()
for filename in os.scandir(directory):
    if os.path.isdir(filename) and ('PW' in str(filename) or 'CK' in str(filename)):
        os.chdir(filename.path)
        if 'PW' in str(filename):
            brand = 2
        elif 'CK' in str(filename):
            brand = 1
        if not os.path.exists('top'):
            os.mkdir('top')
            for filename in os.listdir():
                if filename.endswith('-1.jpg') or filename.endswith('-1.jpeg'):
                    shutil.move(filename, os.path.join('top', filename))
        if len([name for name in os.listdir() if os.path.isfile(name)]) > 19:
            if not os.path.exists('extra'):
                os.mkdir('extra')
            for filename in os.listdir():
                if filename.endswith('-8.jpg'):
                    shutil.move(filename, os.path.join('extra', filename))
        os.chdir('top')
        get_images(brand)
