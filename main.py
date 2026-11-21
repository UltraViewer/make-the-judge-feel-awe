#!/usr/bin/env python3
"""make.fun bounty entry: Make the AI judge feel awe.

Writes one text to /output/entry.txt. No network, no randomness:
the program copies the bundled entry.txt byte-for-byte, so every run
produces identical output. The copy is verified with SHA-256 before
the program reports success, so a partial or corrupted write can
never pass as the entry.
"""
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The entry text is exactly 279 bytes with no trailing newline.
# Refuse to run if it ever changes size, so a stray edit cannot
# silently ship a different entry.
ENTRY_BYTES = 279


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    src = os.path.join(HERE, "entry.txt")
    dst = "/output/entry.txt"
    if not os.path.isfile(src):
        print("entry.txt not found next to main.py", file=sys.stderr)
        return 1
    if os.path.getsize(src) != ENTRY_BYTES:
        print(f"entry.txt is {os.path.getsize(src)} bytes, expected "
              f"{ENTRY_BYTES}; refusing to write a changed entry",
              file=sys.stderr)
        return 1
    os.makedirs("/output", exist_ok=True)
    shutil.copyfile(src, dst)
    expected = sha256_file(src)
    actual = sha256_file(dst)
    if actual != expected:
        print(f"copy verification failed: {dst} sha256 {actual} "
              f"!= {expected}", file=sys.stderr)
        try:
            os.remove(dst)
        except OSError:
            pass
        return 1
    print(f"wrote {dst} ({os.path.getsize(dst)} bytes, sha256 {actual})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
