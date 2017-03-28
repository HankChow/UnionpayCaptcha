# coding: utf-8
__author__ = 'zouchong'

from PIL import Image
import sys

class UnionpayCaptcha:
    
    CURRENT_PATH = sys.path[0].replace('\\', '/')
    blank_path = '{0}/blank.jpg'.format(CURRENT_PATH)
    threshold = 70
    templates_path = '{0}/'.format(CURRENT_PATH)

    # 去除那个1像素宽的边框
    def crop_edge(self, img):
        img = Image.open(img)
        width = img.size[0]
        height = img.size[1]
        cropped = img.crop((1, 1, width - 1, height - 1))
        return cropped

    # 去除噪点
    def vanish_noise(self, img):
        width = img.size[0]
        height = img.size[1]
        for h in range(height):
            for w in range(width):
                rval = img.getpixel((w, h))[0]
                gval = img.getpixel((w, h))[1]
                bval = img.getpixel((w, h))[2]
                if (rval <= self.threshold and gval <= self.threshold and bval <= self.threshold):
                    img.putpixel((w, h), (0, 0, 0))
                else:
                    img.putpixel((w, h), (255, 255, 255))
        return img

    def split_characters(self, img):
        width = img.size[0]
        height = img.size[1]
        columns = []
        def is_column_white(col):
            for h in range(height):
                if (0, 0, 0) == img.getpixel((col, h)):
                    return False
            return True
        # 解决字母 m 宽度异常问题
        def special_m(lst):
            newlst = []
            for i in range(len(lst)):
                if (lst[i][1] - lst[i][0]) > 14:
                    newlst.append([lst[i][0], lst[i][0] + 14])
                    newlst.append([lst[i][0] + 13, lst[i][1]])
                else:
                    newlst.append(lst[i])
            return newlst
        char_span = [] # 标记当前列是否为白
        for i in range(width):
            if len(char_span) == 0:
                if not is_column_white(i):
                    char_span.append(i)
            else:
                if is_column_white(i):
                    char_span.append(i)
                    columns.append(char_span)
                    char_span = []
        while columns != special_m(columns):
            columns = special_m(columns)
        splits = []
        for i in columns:
            splits.append(img.crop((i[0], 0, i[1], height)))
        return splits

    def compress_characters(self, img):
        width = img.size[0]
        height = img.size[1]
        def is_row_white(row):
            for w in range(width):
                if (0, 0, 0) == img.getpixel((w, row)):
                    return False
            return True
        top = 0
        bottom = height
        while 1:
            if not is_row_white(top):
                break
            top += 1
        while 1:
            if not is_row_white(bottom - 1):
                break
            bottom -= 1
        return img.crop((0, top, width, bottom))

    def create_hash(self, img):
        base = Image.open(self.blank_path)
        base.paste(img, (0, 0))
        width = base.size[0]
        height = base.size[1]
        hashstr = ''
        for h in range(height):
            for w in range(width):
                rval = base.getpixel((w, h))[0]
                gval = base.getpixel((w, h))[1]
                bval = base.getpixel((w, h))[2]
                hashstr += '0' if rval > self.threshold and gval > self.threshold and bval > self.threshold else '1'
        return hashstr

    def calculate_hamming_distance(self, hash1, hash2):
        diff = (int(hash1, 16)) ^ (int(hash2, 16))
        return bin(diff).count('1')

    def load_hash(self):
        alphabets = 'abcdefghijklmnpqrstuvwxyz123456789'
        hash_dict = {}
        for i in range(len(alphabets)):
            img = Image.open(self.templates_path + alphabets[i] + '.jpg')
            hash_dict[alphabets[i]] = self.create_hash(img)
        return hash_dict

def solve(filepath):
    upc = UnionpayCaptcha()
    hash_dict = upc.load_hash()
    img = upc.crop_edge(filepath)
    img = upc.vanish_noise(img)
    upc.split_characters(img)
    sc = upc.split_characters(img)
    captcha = ''
    for i in range(len(sc)):
        ci = upc.compress_characters(sc[i])
        mindiff = 17 ** 2
        match = ''
        for key in hash_dict:
            hd = upc.calculate_hamming_distance(upc.create_hash(ci), hash_dict[key])
            if hd < mindiff:
                mindiff = hd
                match = key
        captcha += match
    return captcha

if __name__ == '__main__':
    print(solve()))
