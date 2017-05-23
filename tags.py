import pyexiv2

TAG_KEY = "Iptc.Application2.Keywords"


def get(filename=None, metadata=None):
    if filename:
        metadata = pyexiv2.ImageMetadata(filename)
        metadata.read()
    try:
        return metadata[TAG_KEY].raw_value
    except KeyError:
        return []


def add(filename, tags):
    if not tags:
        return
    metadata = pyexiv2.ImageMetadata(filename)
    metadata.read()
    existing_tags = get(metadata=metadata)
    for tag in tags:
        if tag not in existing_tags:
            existing_tags.append(tag)
            metadata[TAG_KEY] = pyexiv2.IptcTag(TAG_KEY, existing_tags)
            metadata.write()
