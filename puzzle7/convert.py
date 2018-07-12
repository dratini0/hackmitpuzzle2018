#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import numpy
from PIL import Image
from scipy import ndimage
import cv2
from scipy.misc import imsave, imread
import os.path

INFILE = "raw.mp4"
OUTFILE = "out.mp4"
MASK = "mask.png"
MANUAL_PATH = "gimp/{:03}.png"

WIDTH = 1280
HEIGHT = 720
CHANNELS = 3
FRAMESIZE = WIDTH * HEIGHT * CHANNELS
FPS = 29.93

PROBLEMFRAME = 61

INPUT_COMMAND = [
    "ffmpeg",
    "-i", INFILE,
    "-c:v", "rawvideo",
    "-f", "rawvideo",
    "-pix_fmt", "rgb24",
    "pipe:"
]

OUTPUT_COMMAND = [
    'ffmpeg',
    #'ffplay',
    '-y',
    '-f', 'rawvideo',
    '-video_size', '{}x{}'.format(WIDTH, HEIGHT),
    '-pixel_format', 'rgb24',
    '-r', str(FPS), # frames per second
    '-i', 'pipe:', # The imput comes from a pipe
    '-r', str(FPS), # frames per second
    '-b:v', '15M',
    OUTFILE,
]

filterAreaYX = (slice(570, 720), slice(0, 150))
filterCopyAreaYX = (slice(570, 720), slice(150, 300))

kernel = numpy.asarray([
    [1, 1, 0, 0, 0, 1, 1],
    [1, 1, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 1, 1],
    [1, 1, 0, 0, 0, 1, 1],
]) / 16
kernel.shape = (7, 7, 1)

dilateKernel = numpy.ndarray((3, 3))
dilateKernel[:, :] = 1

def main():
    mask = Image.open(MASK)
    mask = mask.convert("RGB")
    mask = numpy.ndarray((HEIGHT, WIDTH, CHANNELS), 'uint8', mask.tobytes()).copy()
    mask = mask[filterAreaYX]
    mask //= 255
    mask *= 50
    with subprocess.Popen(INPUT_COMMAND, stdout=subprocess.PIPE) as input:
        with subprocess.Popen(OUTPUT_COMMAND, stdin=subprocess.PIPE) as output:
            i = 0
            while True:
                frame = input.stdout.read(FRAMESIZE)
                if frame == b'':
                    break
                if len(frame) < FRAMESIZE:
                    print("Warning, leftover data")
                    break
                if i > 10:
                    i += 1
                    continue
                frame = numpy.ndarray((HEIGHT, WIDTH, CHANNELS), 'uint8', frame).copy()
                filterArea = frame[filterAreaYX]
                filterArea -= mask
                #frame[filterCopyAreaYX] = filterArea
                filterAreaFloat = numpy.asarray(filterArea, 'float32')
                blurredForEdge = ndimage.gaussian_filter(filterArea, (5, 5, 0))
                #blurredForFix = ndimage.gaussian_filter(filterArea, (5, 5, 0))
                #blurred = ndimage.convolve(filterArea, kernel)
                #frame[filterCopyAreaYX] = blurred
                difference = filterAreaFloat - blurredForEdge
                difference = numpy.linalg.norm(difference, axis=2)
                #problematic = difference > 80.0
                if 0 <= i < 6:
                #    problematic = filterArea[:, :, 0] - 10 > filterArea[:, :, 2]
                    problematic = difference > 150.0
                    yellow1 = filterArea[:, :, 2] < 95
                    yellow2 = (filterArea[:, :, 0] - 20) > filterArea[:, :, 2]
                    yellow2 = False
                    problematic = numpy.logical_or(numpy.logical_or(problematic, yellow1), yellow2)
                #elif 47 <= i < 116:
                #    problematic = numpy.logical_and(filterArea[:, :, 0] < 100, filterArea[:, :, 2] > 100)
                elif 48 <= i < 67:
                    #blurredForBlack = ndimage.gaussian_filter(filterArea, (3, 3, 0))
                    #differenceBlack = filterAreaFloat - blurredForBlack
                    #differenceBlack = numpy.linalg.norm(differenceBlack, axis=2)

                    #problematic = difference > 150.0
                    #cyan = numpy.logical_and(numpy.logical_and(filterArea[:, :, 0] < 0x70, filterArea[:, :, 1] > 0x70), filterArea[:, :, 2] > 0x40)
                    #black = numpy.logical_and(numpy.logical_and(filterArea[:, :, 0] < 0x40, filterArea[:, :, 1] < 0x20), filterArea[:, :, 2] < 0x20)
                    #black = numpy.logical_and(black, differenceBlack > 80.0)
                    #problematic = numpy.logical_or(problematic, black)
                    manual_path = MANUAL_PATH.format(i)
                    if not os.path.exists(manual_path):
                        imsave(manual_path, filterArea)
                        problematic = numpy.ndarray((150, 150), "bool")
                        problematic[:, :] = False
                    else:
                        problematic = difference > 50.0
                        problematic[:, :25] = False
                        problematic[:, -27:] = False
                        problematic[-25:, :] = False
                        problematic[:27, :] = False
                        loaded = imread(manual_path)[:, :, :3]
                        if i != PROBLEMFRAME:
                            filterArea[problematic] = loaded[problematic]
                            #print(filterArea.shape)
                            filterAreaFloat = numpy.asarray(filterArea, 'float32')
                            blurredForEdge = ndimage.gaussian_filter(filterArea, (2, 2, 0))
                            difference = filterAreaFloat - blurredForEdge
                            difference = numpy.linalg.norm(difference, axis=2)
                            problematic = difference > 50.0
                        else:
                            filterArea = loaded
                            problematic = numpy.ndarray((150, 150), "bool")
                            problematic[:, :] = False

                elif 67 <= i < 77:
                    problematic = difference > 80.0
                elif 77 <= i < 85:
                    problematic = difference > 120.0
                elif 85 <= i < 88:
                    problematic = difference > 80.0
                elif 88 <= i < 93:
                    problematic = difference > 100.0
                elif 93 <= i < 98:
                    problematic = difference > 80.0
                elif 98 <= i < 116:
                    problematic = difference > 100.0
                elif 124 <= i < 126:
                    problematic = difference > 150.0
                else:
                    problematic = numpy.ndarray((150, 150), "bool")
                    problematic[:, :] = False
                problematic[:, :25] = False
                problematic[:, -27:] = False
                problematic[-25:, :] = False
                problematic[:27, :] = False
                problematic = numpy.asarray(problematic, "uint8")
                #problematic = cv2.Laplacian(mask[:, :, 0], 8)
                #grayscale = cv2.cvtColor(filterArea, cv2.COLOR_RGB2GRAY)
                #grayscale = numpy.asarray(grayscale, "int32")
                #problematic = numpy.abs(cv2.Laplacian(grayscale, 32)) > 30
                problematic = cv2.dilate(problematic, dilateKernel)
                #problematic = numpy.asarray(problematic, "bool")
                #filterArea[problematic] = [255, 0, 0]
                #filterArea[problematic] = blurredForFix[problematic]
                filterArea = cv2.inpaint(filterArea, problematic, 3, cv2.INPAINT_TELEA)
                frame[filterAreaYX] = filterArea
                #cv2.putText(frame, str(i), (100, 100), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 2, [0, 255, 0])
                output.stdin.write(frame)
                imsave("explode/{:03}.png".format(i), frame)
                i += 1

if __name__ == "__main__":
    main()

