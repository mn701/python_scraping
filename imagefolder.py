from PIL import Image
import os
import shutil

SQUARE_SIZE = 1536
SQUARE_HALF = 768
LOGO_FILENAME = 'catlogo.png'

def create_top(images):
    new_im = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE))
    if(len(images) > 2 and len(images) < 5):
        new_im = create_im_from_4(images)
        new_im = add_logo_center(new_im)
    elif(len(images) == 1):
        new_im = create_im_1(images[0])
        new_im = add_logo_center(new_im)

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

def add_shop_logo(image):
    # Adding logo image

    logo_im = Image.open(LOGO_FILENAME)
    logo_im = logo_im.resize((200, 200))
    logoWidth, logoHeight = logo_im.size
    width, height = image.size

    # Paste logo on botom left
    image.paste(logo_im, (width-logoWidth, height-logoHeight), logo_im)

    return image

def add_logo_center(image):
    # Adding logo image
    LOGO_FILENAME = 'logo.png'
    logo_im = Image.open(LOGO_FILENAME)
    logo_im = logo_im.resize((200, 200))
    logoWidth, logoHeight = logo_im.size
    width, height = image.size

    # Paste logo on botom left
    image.paste(logo_im, (int(width/2) - int(logoWidth/2), int(height/2) - int(logoHeight/2)), logo_im)

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
