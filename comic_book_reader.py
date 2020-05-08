# -*- coding: utf-8 -*-

import cv2
import enchant
import numpy
import os
import pytesseract
import re

from autocorrect import Speller
from PIL import Image

d = enchant.Dict("en_US")
spell = Speller(lang='en')

# Crop image by removing a number of pixels
def shrinkByPixels(im, pixels):
    h = im.shape[0]
    w = im.shape[1] 
    return im[pixels:h-pixels, pixels:w-pixels]

# Adjust the gamma in an image by some factor
def adjust_gamma(image, gamma=1.0):
   invGamma = 1.0 / gamma
   table = numpy.array([((i / 255.0) ** invGamma) * 255
      for i in numpy.arange(0, 256)]).astype("uint8")
   return cv2.LUT(image, table)

# Comparison function for sorting contours
def get_contour_precedence(contour, cols):
    tolerance_factor = 200
    origin = cv2.boundingRect(contour)
    return ((origin[1] // tolerance_factor) * tolerance_factor) * cols + origin[0]

# Find all speech bubbles in the given comic page and return a list of their contours
def findSpeechBubbles(image):
    # Convert image to gray scale
    imageGray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Recognizes rectangular/circular bubbles, struggles with dark colored bubbles 
    binary = cv2.threshold(imageGray,225,255,cv2.THRESH_BINARY)[1]
    # Find contours and document their heirarchy for later
    contours, hierarchy = cv2.findContours(binary,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    contourMap = {}
    finalContourList = []

    contourMap = filterContoursBySize(contours)
    contourMap = filterContainingContours(contourMap, hierarchy)

    # Sort final contour list
    finalContourList = list(contourMap.values())
    finalContourList.sort(key=lambda x:get_contour_precedence(x, binary.shape[1]))

    return finalContourList

def filterContoursBySize(contours):
    # We could pass this in and update it by reference, but I prefer this sort of 'immutable' handling.
    contourMap = {}

    for i in range(len(contours)):
        # Filter out speech bubble candidates with unreasonable size
        if cv2.contourArea(contours[i]) < 100000 and cv2.contourArea(contours[i]) > 4000:
            # Smooth out contours that were found
            epsilon = 0.0025*cv2.arcLength(contours[i], True)
            approximatedContour = cv2.approxPolyDP(contours[i], epsilon, True)
            contourMap[i] = approximatedContour

    return contourMap

# Sometimes the contour algorithm identifies entire panels, which can contain speech bubbles already
#  identified causing us to parse them twice via OCR. This method attempts to remove contours that 
#  contain other speech bubble candidate contours completely inside of them.
def filterContainingContours(contourMap, hierarchy):
    # I really wish there was a better way to do this than this O(n^2) removal of all parents in
    #  the heirarchy of a contour, but with the number of contours found this is the only way I can
    #  think of to do this.
    for i in list(contourMap.keys()):
        currentIndex = i
        while hierarchy[0][currentIndex][3] > 0:
            if hierarchy[0][currentIndex][3] in contourMap.keys():
                contourMap.pop(hierarchy[0][currentIndex][3])
            currentIndex = hierarchy[0][currentIndex][3]

    # I'd prefer to handle this 'immutably' like above, but I'd rather not make an unnecessary copy of the dict.
    return contourMap

# Given a list of contours, return a list of cropped images based on the bounding rectangles of the contours
def cropSpeechBubbles(image, contours, padding = 0):
    croppedImageList = []
    for contour in contours:
        rect = cv2.boundingRect(contour)
        [x, y, w, h] = rect
        croppedImage = image[y-padding:y+h+padding, x-padding:x+w+padding]
        croppedImageList.append(croppedImage)
    return croppedImageList

# Process a line of text based on some "business" rules
def processScript(script):
    # Some modern comics have this string on their cover page
    if "COMICS.COM" in script:
        return ''

    # Tesseract sometimes picks up 'I' chars as '|'
    script = script.replace('|','I')
    # We want new lines to be spaces so we can treat each speech bubble as one line of text
    script = script.replace('\n',' ')
    # Remove multiple spaces from our string
    words = script.split()
    script = ' '.join(words)

    for char in script:
        # Comic books tend to be written in upper case, so we remove anything other than upper case chars
        if char not in ' -QWERTYUIOPASDFGHJKLZXCVBNM,.?!""\'’1234567890':
            script = script.replace(char,'')

    # This line removes "- " and concatenates words split on two lines
    #  One notable edge case we don't handle here, hyphenated words split on two lines
    script = re.sub(r"(?<!-)- ", "", script)
    words = script.split()
    for i in range(0, len(words)):
        # Spellcheck all words
        if not d.check(words[i]):
            alphaWord = ''.join([j for j in words[i] if j.isalpha()])
            if alphaWord and not d.check(alphaWord):
                words[i]=spell(words[i].lower()).upper()
        # Remove single chars other than 'I' and 'A'
        if len(words[i]) == 1:
            if (words[i] != 'I' and words[i] != 'A'):
                words[i] = ''

    # Remove any duplicated spaces
    script = ' '.join(words)
    words = script.split()
    final = ' '.join(words)

    # Remove all two char lines other than 'NO' and 'OK'
    if len(final) == 2 and script != "NO" and script != "OK":
        return ''

    return final

# Apply the ocr engine to the given image and return the recognized script where illegitimate characters are filtered out
def tesseract(image):
    # We could consider using tessedit_char_whitelist to limit the recognition of Tesseract. 
    #   Doing that degraded OCR performance in practice
    script = pytesseract.image_to_string(image, lang = 'eng')
    return processScript(script)

def segmentPage(image, shouldShowImage = False):
    contours = findSpeechBubbles(image)
    croppedImageList = cropSpeechBubbles(image, contours)

    cv2.drawContours(image, contours, -1, (0, 0, 0), 2)
    if shouldShowImage:
        cv2.imshow('Speech Bubble Identification', image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return croppedImageList

def parseComicSpeechBubbles(croppedImageList, shouldShowImage = False):
    scriptList = []

    for croppedImage in croppedImageList:
        # Enlarge cropped image
        croppedImage = cv2.resize(croppedImage, (0,0), fx = 2, fy = 2)
        # # Denoise
        croppedImage = cv2.fastNlMeansDenoisingColored(croppedImage, None, 10, 10, 7, 15)

        if shouldShowImage:
            cv2.imshow('Cropped Speech Bubble', croppedImage)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        # Pass cropped image to the ocr engine
        script = tesseract(croppedImage)
    
        # If we don't find any characters, try shrinking the cropped area. 
        #  This occasionally helps tesseract recognize single word lines, but increases processing time.
        count = 0
        while (script == '' and count < 3):
            count+=1
            croppedImage = shrinkByPixels(croppedImage, 5)
            script = tesseract(croppedImage)

        if script != '' and script not in scriptList:
            scriptList.append(script)

    return scriptList