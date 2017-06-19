#!/usr/bin/env python

# ELA Analysis

import optparse
import cStringIO
from PIL import Image
import os
import glob


class elaAnalsys():
    def __init__(self, trigger, enhance, coloronly):
        self.trigger = trigger
        self.enhance = enhance

    def CalculateELA(self, pixelA, pixelB):
        pixelDiff = map(lambda x, y: abs(x - y), pixelA, pixelB)
        if sum(pixelDiff) > self.trigger and (pixelDiff[0] != pixelDiff[1] or pixelDiff[0] != pixelDiff[2]):
            return tuple([x * self.enhance for x in pixelDiff])
        else:
            return (0, 0, 0)


def ELA(filenameInput, filenameOutput):
    coloronly = False
    trigger = 10
    enhance = 20
    quality = 95

    oELA = elaAnalsys(trigger, enhance, coloronly)
    imOriginal = Image.open(filenameInput)
    oStringIO = cStringIO.StringIO()
    imOriginal.save(oStringIO, 'JPEG', quality=quality)
    oStringIO.seek(0)
    imJPEGSaved = Image.open(oStringIO)
    imNew = Image.new('RGB', imOriginal.size)
    imNew.putdata(map(oELA.CalculateELA, imOriginal.getdata(), imJPEGSaved.getdata()))
    imNew.save(filenameOutput)


if __name__ == '__main__':
    f = []
    path = 'images/ps-battles/originals'
    out_path = os.path.join(path, 'ela')

    for root, dirs, files in os.walk(path):
        for idx, f in enumerate(files):
            if not f.find('.jpg'): 
                continue
            else:
                print("Processing file: {} / {}".format(idx, len(files)))
                file_in = os.path.join(path, f)
                file_out = os.path.join(out_path, f)

                ELA(file_in, file_out)
