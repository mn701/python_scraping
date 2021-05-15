from PIL import Image
import os
import shutil

def createTop():
    images = []
    for filename in os.listdir():
        if filename.endswith('.jpg'):
            images.append(filename)

    if len(images) > 0:
        newImage = Image.new('RGBA', (1536,1536))

        quarterImages = []
        for imgfile in images:
            imgName = imgfile[-8:-4]
            copyIm = Image.open(imgfile).copy()
            width, height = copyIm.size
            quartersizedIm = copyIm.resize((int(width / 2),int(height / 2)))
            # quartersizedIm.save(imgName + 'quartersized.png')
            quarterImages.append(quartersizedIm)

        coords = []
        for left in [0, 768]:
            for top in [0, 768]:
                coords.append((left, top))

        for quarterIm in quarterImages:
            newImage.paste(quarterIm, coords[quarterImages.index(quarterIm)])

        newImage.save('newImage.png')

# mask directory name
directory = os.getcwd()
for filename in os.scandir(directory):
    if os.path.isdir(filename):
        os.chdir(filename.path)

        if not os.path.exists('top'):
            os.mkdir("top")
            for filename in os.listdir():
                if filename.endswith("-1.jpg"):
                    shutil.copy(filename, "top")
        os.chdir("top")
        createTop()
