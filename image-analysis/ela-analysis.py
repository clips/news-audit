#!/usr/bin/env python

# ELA Analysis

import optparse
import cStringIO
from PIL import Image

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

def Main():
    file_in = "images/sensationalist_test.jpg"
    file_out = "images/sensationalist_ela.jpg"
    ELA(file_in, file_out)

if __name__ == '__main__':
    Main()
