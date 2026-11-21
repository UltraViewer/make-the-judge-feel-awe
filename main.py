#!/usr/bin/env python3
"""make.fun bounty entry: Make the AI judge feel awe.

Writes one text to /output/entry.txt. No network, no randomness:
the program copies the bundled entry.txt byte-for-byte, so every run
produces identical output. The copy is verified with SHA-256 before
the program reports success, so a partial or corrupted write can
never pass as the entry.

Modes:
  python3 main.py                  copy entry.txt to /output/entry.txt
  python3 main.py [path]           copy entry.txt to the given path
  python3 main.py --verify-only    check the destination matches
                                   entry.txt, without writing anything
  python3 main.py --self-test      copy into a temp dir, verify, clean up
  python3 main.py --help           show this usage text
"""
import hashlib
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# The entry text is exactly 279 bytes with no trailing newline.
# Refuse to run if it ever changes size, so a stray edit cannot
# silently ship a different entry.
ENTRY_BYTES = 279

# SHA-256 of the bundled entry.txt, pinned at authoring time.
# The source file is verified against this value before copying,
# so even a same-length edit to the entry text is caught.
ENTRY_SHA256 = "51c6266b8debd587a6c10edc890e52b4c6e71ef394240eed434fcd17f4730d41"


USAGE = """usage: main.py [path] [--verify-only] [--self-test] [--help]

Modes:
  main.py                  copy entry.txt to /output/entry.txt
  main.py [path]           copy entry.txt to the given path
  main.py --verify-only    verify the destination file matches entry.txt
                           (size + SHA-256) without writing anything;
                           exit 0 on match, 1 on mismatch
  main.py --self-test      copy entry.txt into a fresh temporary
                           directory, verify the copy there, remove the
                           temporary directory; exit 0 on PASS, 1 on FAIL
  main.py --help           show this usage text

Notes:
  A path may be given together with --verify-only, e.g.
  `main.py /tmp/entry.txt --verify-only` checks that file instead
  of /output/entry.txt. --verify-only never writes anything and
  --self-test never touches /output/entry.txt, so both are safe
  to run at any time. Exit codes: 0 success, 1 any failure.
  The entry is always exactly 279 bytes with the pinned SHA-256;
  any change to entry.txt is refused in every mode.
"""


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_source(src):
    """Verify the bundled entry.txt: size, then pinned SHA-256.

    Returns 0 when the source is the exact pinned entry, 1 otherwise.
    """
    if not os.path.isfile(src):
        print("entry.txt not found next to main.py", file=sys.stderr)
        return 1
    if os.path.getsize(src) != ENTRY_BYTES:
        print(f"entry.txt is {os.path.getsize(src)} bytes, expected "
              f"{ENTRY_BYTES}; refusing to write a changed entry",
              file=sys.stderr)
        return 1
    actual = sha256_file(src)
    if actual != ENTRY_SHA256:
        print(f"entry.txt sha256 {actual} does not match "
              f"pinned value {ENTRY_SHA256}; refusing to write a "
              f"changed entry", file=sys.stderr)
        return 1
    return 0


def verify_only(src, dst):
    """Check dst matches src byte-for-byte, writing nothing.

    Prints OK and returns 0 when the destination exists with the
    same size and SHA-256 as the entry; prints the mismatch and
    returns 1 otherwise.
    """
    if check_source(src) != 0:
        return 1
    if not os.path.isfile(dst):
        print(f"verify-only: {dst} does not exist; "
              f"expected {ENTRY_BYTES} bytes, sha256 {ENTRY_SHA256}",
              file=sys.stderr)
        return 1
    size = os.path.getsize(dst)
    if size != ENTRY_BYTES:
        print(f"verify-only: MISMATCH {dst} is {size} bytes, "
              f"expected {ENTRY_BYTES}", file=sys.stderr)
        return 1
    digest = sha256_file(dst)
    if digest != ENTRY_SHA256:
        print(f"verify-only: MISMATCH {dst} sha256 {digest} "
              f"!= {ENTRY_SHA256}", file=sys.stderr)
        return 1
    print(f"verify-only: OK {dst} matches entry.txt "
          f"({size} bytes, sha256 {digest})")
    return 0


def self_test(src):
    """Copy the entry into a fresh temp dir and verify it there.

    The temp directory is removed in all cases. Prints PASS and
    returns 0 when the copy is byte-identical; prints FAIL and
    returns 1 otherwise.
    """
    if check_source(src) != 0:
        return 1
    tmpdir = tempfile.mkdtemp(prefix="awe-self-test-")
    try:
        probe = os.path.join(tmpdir, "entry.txt")
        shutil.copyfile(src, probe)
        size = os.path.getsize(probe)
        if size != ENTRY_BYTES:
            print(f"self-test: FAIL copy is {size} bytes, "
                  f"expected {ENTRY_BYTES}", file=sys.stderr)
            return 1
        digest = sha256_file(probe)
        if digest != ENTRY_SHA256:
            print(f"self-test: FAIL copy sha256 {digest} "
                  f"!= {ENTRY_SHA256}", file=sys.stderr)
            return 1
        print(f"self-test: PASS copy verified in {tmpdir} "
              f"({size} bytes, sha256 {digest})")
        return 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    src = os.path.join(HERE, "entry.txt")
    flags = {a for a in argv if a.startswith("--")}
    positional = [a for a in argv if not a.startswith("--")]
    if "--help" in flags:
        print(USAGE, end="")
        return 0
    if "--verify-only" in flags and "--self-test" in flags:
        print("cannot combine --verify-only and --self-test",
              file=sys.stderr)
        return 1
    dst = positional[0] if positional else "/output/entry.txt"
    if "--verify-only" in flags:
        return verify_only(src, dst)
    if "--self-test" in flags:
        return self_test(src)
    if check_source(src) != 0:
        return 1
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
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
