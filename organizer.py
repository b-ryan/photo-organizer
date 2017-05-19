#!/usr/bin/env python3
import sys
from PIL import Image, ExifTags
import pyexiv2
import os
import face_recognition as face_rec
from face_recognition.cli import scan_known_people
import scipy.misc
import pickle

TAG_KEY = "Iptc.Application2.Keywords"
KNOWN_FACES_DIR = os.path.expanduser("~/Pictures/face_recog_known_people")
ORIENTATION_EXIF_TAG = 274


def _scale_image_if_large(image):
    # taken directly from http://tinyurl.com/momhalb
    if image.shape[1] > 1600:
        scale_factor = 1600.0 / image.shape[1]
        return scipy.misc.imresize(image, scale_factor)
    return image


def _rotate_accordingly(pil_image):
    exif = dict(pil_image._getexif().items())
    orientation = exif[ORIENTATION_EXIF_TAG]
    rotation = {
        3: 180,
        6: 270,
        8: 90,
    }.get(orientation)
    if not rotation:
        return pil_image
    return pil_image.rotate(rotation, expand=True)


class KnownPeople(object):
    def __init__(self, names, encodings):
        self.names = names
        self.encodings = encodings

    @classmethod
    def load(cls):
        if os.path.exists("known-people-cache"):
            with open("known-people-cache", "rb") as f:
                return pickle.loads(f.read())
        known_people = cls(*scan_known_people(KNOWN_FACES_DIR))
        with open("known-people-cache", "wb") as f:
            f.write(pickle.dumps(known_people))
        return known_people

    def identify_encoding(self, encoding):
        result = face_rec.compare_faces(self.encodings, encoding)
        try:
            idx = result.index(True)
        except ValueError:
            return "Unknown"
        return self.names[idx]

    def identify_all(self, filename):
        pil_img = _rotate_accordingly(Image.open(filename))
        image = scipy.misc.fromimage(pil_img, mode="RGB")
        image = _scale_image_if_large(image)
        return [self.identify_encoding(encoding)
                for encoding in face_rec.face_encodings(image)]


def _add_tags(filename, tags):
    metadata = pyexiv2.ImageMetadata(filename)
    metadata.read()
    try:
        image_tags = metadata[TAG_KEY].raw_value
    except KeyError:
        image_tags = []
    for tag in tags:
        if tag not in image_tags:
            image_tags.append(tag)
            metadata[TAG_KEY] = pyexiv2.IptcTag(TAG_KEY, image_tags)
            metadata.write()


def main(args):
    known_people = KnownPeople.load()
    for filename in args:
        names = known_people.identify_all(filename)
        _add_tags(filename, names)

if __name__ == "__main__":
    main(sys.argv[1:])
