#!/usr/bin/env python3
import sys
from PIL import Image, ExifTags
import os
import face_recognition as face_rec
from face_recognition.cli import scan_known_people
import scipy.misc
import pickle
import click
import config
import db
import tags

ORIENTATION_EXIF_TAG = 274


def _scale_image_if_large(scipy_image):
    # taken directly from http://tinyurl.com/momhalb
    if scipy_image.shape[1] > 1600:
        scale_factor = 1600.0 / scipy_image.shape[1]
        return scipy.misc.imresize(scipy_image, scale_factor)
    return scipy_image


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
        if os.path.exists(config.KNOWN_PEOPLE_CACHE):
            with open(config.KNOWN_PEOPLE_CACHE, "rb") as f:
                return pickle.loads(f.read())
        known_people = cls(*scan_known_people(config.KNOWN_FACES_DIR))
        with open(config.KNOWN_PEOPLE_CACHE, "wb") as f:
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
        return list(set([self.identify_encoding(encoding)
                         for encoding in face_rec.face_encodings(image)]))


@click.command("get-tags")
@click.argument("filenames", nargs=-1)
def get_tags(filenames):
    for filename in filenames:
        print(filename, tags.get(filename))


@click.command("identify")
@click.argument("filenames", nargs=-1)
def identify(filenames):
    known_people = KnownPeople.load()
    for filename in filenames:
        names = known_people.identify_all(filename)
        print(filename, names)


@click.command("tag")
@click.argument("filenames", nargs=-1)
def tag(filenames):
    known_people = KnownPeople.load()
    for filename in filenames:
        names = known_people.identify_all(filename)
        if "Unknown" in names:
            print(filename, "has unknown person(people)")
            names.remove("Unknown")
        tags.add(filename, names)


@click.group()
def cli():
    pass

cli.add_command(get_tags)
cli.add_command(identify)
cli.add_command(tag)

if __name__ == "__main__":
    cli()
