import os
import sys
import shutil
import argparse
from PIL import Image, ImageOps, ImageEnhance

# constants in px
SQUARE_SIZE = 210
BORDER_SIZE = 10
PADDING = 30

# constants which are integer values
NUM_BATCHES = 4
NUM_SQUARES = 3

COMIC_FORMAT = 'JPEG'


def generate_square(img, pos, padding):
    width, height = img.size

    if width >= height:
        left = int(SQUARE_SIZE * (pos + 1) + padding)
        upper = int(SQUARE_SIZE * (pos + 1))
        right = int(SQUARE_SIZE * pos + padding)
        lower = int(SQUARE_SIZE * pos)
    else:
        left = int(SQUARE_SIZE * pos)
        upper = int(SQUARE_SIZE * pos + padding)
        right = int(SQUARE_SIZE * (pos + 1))
        lower = int(SQUARE_SIZE * (pos + 1) + padding)

    return img.crop((left, upper, right, lower))


def store_square_batches(img, file_name, extension):
    larger_dimension = max(img.size)

    padding = (larger_dimension - SQUARE_SIZE * NUM_SQUARES) / NUM_BATCHES
    for i in range(NUM_BATCHES):
        # get the name of the current dir, create dirs for squares
        batch_dir = os.path.join(os.path.dirname(os.path.abspath('{}.{}'.format(file_name, extension))), 'squares_batch{}'.format(i))
        os.mkdir(batch_dir)
        for j in range(NUM_SQUARES):
            square = generate_square(img, j, padding * i)
            ImageOps.expand(square, border=BORDER_SIZE, fill='black').save(os.path.join(batch_dir, '{}_square{}{}'.format(file_name, j, extension)))


def create_comic(path, format='horizontal'):
    for i, d in enumerate(sorted([x for x in os.listdir(path) if 'squares_batch' in x])):
        if format == 'horizontal':
            # | pad b    b pad b    b pad b    b pad |
            # | pad b sq b pad b sq b pad b sq b pad |
            # | pad b    b pad b    b pad b    b pad |
            size = ((SQUARE_SIZE + BORDER_SIZE * 2 + PADDING) * NUM_SQUARES + PADDING,
                    SQUARE_SIZE + BORDER_SIZE * 2 + PADDING * 2)
            comic = Image.new('RGB', size, color='white')
        else:
            size = (SQUARE_SIZE + BORDER_SIZE * 2 + PADDING * 2,
                    (SQUARE_SIZE + BORDER_SIZE * 2 + PADDING) * NUM_SQUARES + PADDING)
            comic = Image.new('RGB', size, color='white')
        for j, f in enumerate(sorted(os.listdir(os.path.join(path, d)))):
            square = load_img(os.path.join(path, d, f))
            if format == 'horizontal':
                block = BORDER_SIZE * 2 + SQUARE_SIZE + PADDING
                comic.paste(square, (PADDING + block * j, PADDING))
            else:
                block = BORDER_SIZE * 2 + SQUARE_SIZE + PADDING
                comic.paste(square, (PADDING, PADDING + block * j))

        comic.save(os.path.join(path, '{}{}_{}.{}'.format('asw', i, format, COMIC_FORMAT)))


def edit_img_for_slides(img, path):
    padding = (max(img.size) - SQUARE_SIZE * NUM_SQUARES) / NUM_BATCHES
    for i in range(NUM_BATCHES):
        background = ImageEnhance.Color(img).enhance(0.3)
        background = ImageEnhance.Contrast(background).enhance(0.3)
        for j in range(NUM_SQUARES):
            width, height = img.size

            if width >= height:
                left = int(SQUARE_SIZE * (j + 1) + padding * i)
                upper = int(SQUARE_SIZE * (j + 1))
                right = int(SQUARE_SIZE * j + padding * i)
                lower = int(SQUARE_SIZE * j)
            else:
                left = int(SQUARE_SIZE * j)
                upper = int(SQUARE_SIZE * j + padding * i)
                right = int(SQUARE_SIZE * (j + 1))
                lower = int(SQUARE_SIZE * (j + 1) + padding * i)

            square = img.crop((left, upper, right, lower))
            square.load()
            background.paste(square, (left, upper, right, lower))

        background.save(os.path.join(path, 'demo{}.{}'.format(i, COMIC_FORMAT)))


def load_img(path):
    return Image.open(path)


def resize(img):
    width, height = img.size
    ratio = max(SQUARE_SIZE/width*NUM_SQUARES, SQUARE_SIZE/height*NUM_SQUARES)
    return img.resize((int(width*ratio), int(height*ratio)), Image.LANCZOS)


def clean(path):
    dirs = os.listdir(path)
    for d in [x for x in dirs if 'squares_batch' in x]:
        shutil.rmtree(d)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create "A Softer World"-style comic from image.')
    parser.add_argument('--img', metavar='FILE PATH', nargs=1, dest='img_path',
                        help='path to the image')
    args = parser.parse_args(sys.argv[1:])

    img_path = args.img_path.pop()
    img = load_img(img_path)

    clean(os.path.dirname(os.path.abspath(img_path)))

    new_img = resize(img)
    file_name, extension = os.path.splitext(img_path)
    new_img.save('{}_resized{}'.format(file_name, extension))

    store_square_batches(new_img, file_name, extension)

    # create_comic(os.path.dirname(os.path.abspath(img_path)), format='vertical')
    edit_img_for_slides(new_img, os.path.dirname(os.path.abspath(img_path)))