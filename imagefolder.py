import os
import shutil

directory = "/Users/MN1/mycodes/images"
for filename in os.scandir(directory):
    if os.path.isdir(filename):
        os.chdir(filename.path)

        cwd = os.getcwd()
        if not os.path.exists('top'):
            os.mkdir("top")
            for filename in os.listdir(cwd):
                if filename.endswith("-1.jpg"):
                    shutil.copy(filename, "top")
