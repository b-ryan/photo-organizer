import sqlite3
import config
import os
import imghdr
import tags


class connection(object):
    def __enter__(self):
        self.conn = sqlite3.connect(config.SQLITE3_FILE)
        return self.conn

    def __exit__(self, *args):
        self.conn.close()


def create():
    with connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                filename text,
                tag text
            )
        """)


def _recursive_filenames(directory):
    directory = os.path.expanduser(directory)
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            full = os.path.join(dirpath, filename)
            yield full


def _save_tag(cursor, filename, tag):
    cursor.execute("INSERT INTO tags (filename, tag) VALUES (?, ?)",
                   [filename, tag])


def index(directory):
    with connection() as conn:
        cursor = conn.cursor()
        for filename in _recursive_filenames(directory):
            if not imghdr.what(filename):
                continue
            for tag in tags.get(filename):
                _save_tag(cursor, filename, tag)
        conn.commit()


if __name__ == "__main__":
    index("~/Pictures/unorganized")
