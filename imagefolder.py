from PIL import Image
import os
import shutil

SQUARE_SIZE = 1536
SQUARE_HALF = 768

def create_top(images):
    newImage = Image.new('RGBA', (SQUARE_SIZE, SQUARE_SIZE))

    # Create a list for quaretersized images.
    quarterImages = []
    for imgfile in images:
        copyIm = Image.open(imgfile).copy()
        crop_rectangle = (0, 192, 1152, 1344)
        cropped_im = copyIm.crop(crop_rectangle)
        quartersizedIm = cropped_im.resize((SQUARE_HALF, SQUARE_HALF))
        quarterImages.append(quartersizedIm)

    # Create a list of coordinates.
    coords = []
    for left in [0, SQUARE_HALF]:
        for top in [0, SQUARE_HALF]:
            coords.append((left, top))
            
    # Paste each quartersized image to newImage
    for quarterIm in quarterImages:
        newImage.paste(quarterIm, coords[quarterImages.index(quarterIm)])

    add_logo(newImage)

def add_logo(image):
    # Adding logo image
    LOGO_FILENAME = 'catlogo.png'
    logoIm = Image.open(LOGO_FILENAME)
    logoIm = logoIm.resize((200, 200))
    logoWidth, logoHeight = logoIm.size

    image.paste(logoIm, (SQUARE_SIZE-logoWidth, SQUARE_SIZE-logoHeight), logoIm)
    
    image.save('imageWithLogo.png')

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
