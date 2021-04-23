import csv
from PIL import Image

def write_mask(look_path: str, put_path: str, size: int, splash: bool=True):
    """ Writes a set of vertices (x, y) to a black and white image and fills in a bit around them. """
    size_minus = size - 1
    mask = Image.new('1', (size, size), color='white') # creates a binary image (all 1s and 0s)
    with open(look_path, newline='\n') as csvfile:
        reading = csv.reader(csvfile, delimiter=',')
        for (x, y) in reading:
            x = int(x)
            y = int(y)
            true_y = size_minus - y # Blender origin is bottom left. Pillow origin is top right. We listen to Pillow
            if x in range(0, size) and y in range(0, size):
                mask.putpixel((x, true_y), 0)
                if splash and x in range(1, size - 1) and y in range(1, size - 1):
                    for (u, v) in [(1, 0), (-1, 0), (0, 1), (0, -1)]: # puts a s
                        mask.putpixel((x + u, true_y - v), 0)
    csvfile.close()
    mask.save(put_path)