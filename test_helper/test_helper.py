import hashlib
from PIL import Image
import numpy as np


class TestFailure(Exception):
    pass
class PrivateTestFailure(Exception):
    pass

class Test(object):
    passed = 0
    numTests = 0
    failFast = False
    private = False

    @classmethod
    def setFailFast(cls):
        cls.failFast = True

    @classmethod
    def setPrivateMode(cls):
        cls.private = True

    @classmethod
    def assertTrue(cls, result, msg="", msg_success=""):
        cls.numTests += 1
        if result == True:
            cls.passed += 1
            print "1 test passed. " + msg_success
        else:
            print "1 test failed. " + msg
            if cls.failFast:
                if cls.private:
                    raise PrivateTestFailure(msg)
                else:
                    raise TestFailure(msg)

    @classmethod
    def assertEquals(cls, var, val, msg="", msg_success=""):
        cls.assertTrue(var == val, msg, msg_success)

    @classmethod
    def assertEqualsHashed(cls, var, hashed_val, msg="", msg_success=""):
        cls.assertEquals(cls._hash(var), hashed_val, msg, msg_success)

    @classmethod
    def assertEqualsImagesHashed(cls, img_path, hashed_img, hashed_img_mode, hashed_img_size, msg="", msg_success=""):
        # We show the correct image size and mode without hashing
        assert cls._img_mode(img_path) == hashed_img_mode, "Different kinds of images. The image mode should be {}.".format(hashed_img_mode)
        assert cls._img_size(img_path) == hashed_img_size, "Different sizes. The image size should be {}.".format(hashed_img_size)
        cls.assertEquals(cls._dhash(img_path), hashed_img, msg, msg_success)

    @classmethod
    def printStats(cls):
        print "{0} / {1} test(s) passed.".format(cls.passed, cls.numTests)

    @classmethod
    def _hash(cls, x):
        return hashlib.sha1(str(x)).hexdigest()

    @classmethod
    def _dhash(cls, image_path, hash_size=8):
        # Grayscale and shrink the image in one step.
        image = Image.open(image_path)
        image = image.convert('L').resize(
            (hash_size + 1, hash_size),
            Image.ANTIALIAS,
        )
        # Compare adjacent pixels.
        difference = []
        for row in xrange(hash_size):
            for col in xrange(hash_size):
                pixel_left = image.getpixel((col, row))
                pixel_right = image.getpixel((col + 1, row))
                difference.append(pixel_left > pixel_right)
        # Convert the binary array to a hexadecimal string.
        decimal_value = 0
        hex_string = []
        for index, value in enumerate(difference):
            if value:
                decimal_value += 2**(index % 8)
            if (index % 8) == 7:
                hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
                decimal_value = 0
        return ''.join(hex_string)

    @classmethod
    def _img_mode(cls, image_path):
        image = Image.open(image_path)
        return image.mode

    @classmethod
    def _img_size(cls, image_path):
        image = Image.open(image_path)
        return image.size
    
    # Some specific cases:
    # Lab 3.1 Ex. 4
    @classmethod
    def euclideanDistMatrix(cls, a, b, det, msg="", msg_success=""):
        if type(a) != np.ndarray or type(b) != np.ndarray:
            print 'Arrays "a" and "b" should numpy arrays'
            assertEquals(False, True, msg, msg_success)
        mask = lambda x: len(zip(*np.where((x < -100) | (x > 100)))) == 0 and x.dtype == 'int32'
        if not mask(a) or not mask(b):
            print 'Arrays "a" and "b" should contains integer numbers from -100 to 100'
            assertEquals(False, True, msg, msg_success)
        c = np.sqrt(np.power(a,2) + np.power(b,2))
        assertEquals(det, np.linalg.det(c), msg, msg_success)