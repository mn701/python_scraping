from PIL import Image
import os
import shutil

SQUARE_SIZE = 1536
SQUARE_HALF = 768
LOGO_SHOP = 'logo_200x200.png'
PEDRO_LOGO = 'logo.png'

def create_top(images):
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE))
    if(len(images) > 2 and len(images) < 5):
        new_im = create_im_from_4(images)
        new_im = add_logo_center(new_im)
    elif(len(images) > 1):
        new_im = create_im_2_ver(images)
    elif(len(images) > 0):
        new_im = create_im_1(images[0])
        new_im = add_logo_top(new_im)

    im_with_logo = add_shop_logo(new_im)
    im_with_logo.save('with_logo.png')

def create_im_1(image):
    copy_im = Image.open(image).copy()
    crop_rectangle = (0, 192, 1152, 1344)
    cropped_im = copy_im.crop(crop_rectangle)
    resized = cropped_im.resize((SQUARE_SIZE, SQUARE_SIZE))
    return resized

def create_im_from_4(images):
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE))
    # Create a list for quaretersized images.
    quarter_images = []
    for imgfile in images:
        copy_im = Image.open(imgfile).copy()
        crop_rectangle = (0, 192, 1152, 1344)
        cropped_im = copy_im.crop(crop_rectangle)
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

    return new_im

def create_im_2_ver(images):
    X_CROP = 100
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE))

    # Create a list for two vertical images.
    resized_images = []
    for imgfile in images:
        copy_im = Image.open(imgfile).copy()
        x, y = copy_im.size
        crop_rectangle = (X_CROP, 0, int(x - 100), y)
        cropped_im = copy_im.crop(crop_rectangle)
        cropped_x, cropped_y = cropped_im.size
        new_width  = SQUARE_HALF
        new_height = int(SQUARE_HALF * cropped_y / cropped_x)
        resized_im = cropped_im.resize((new_width, new_height))
        resized_im.save('resized' + imgfile)
        resized_images.append(resized_im)

    # Create a list of coordinates.
    coords = []
    for left in [0, SQUARE_HALF]:
        top = SQUARE_HALF - int(new_height / 2)
        coords.append((left, top))

    # Paste each quartersized image to new_im
    for im in resized_images:
        new_im.paste(im, coords[resized_images.index(im)])

    return new_im

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

def add_logo_center(image):
    # Adding logo image
    logo_im = Image.open(PEDRO_LOGO).convert("RGBA")
    logo_im = logo_im.resize((600, 112))
    logoWidth, logoHeight = logo_im.size
    width, height = image.size

    # Paste logo on botom left
    image.paste(logo_im, ((int(width/2) - int(logoWidth/2)), (int(height/2) - int(logoHeight/2))), logo_im)

    return image

def get_images():
    images = []
    for filename in os.listdir():
        if filename.endswith('.jpg'):
            images.append(filename)

    if len(images) > 0:
        create_top(images)


# mask directory name
directory = os.getcwd()
for filename in os.scandir(directory):
    if os.path.isdir(filename) and 'PW' in str(filename):
        os.chdir(filename.path)

        if not os.path.exists('top'):
            os.mkdir('top')
            for filename in os.listdir():
                if filename.endswith('-1.jpg'):
                    shutil.copy(filename, 'top')
        os.chdir('top')
        get_images()
