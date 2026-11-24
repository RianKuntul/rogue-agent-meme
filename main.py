#!/usr/bin/env python3
"""Entry program for make.fun's Meme Sprint 3 bounty,
"AI Agent Goes Rogue".

Publishes the committed entry.png as /output/entry.png. The image is
a single meme: a cheerful robot AI assistant on its first day has
unionized the household toasters, who rally behind it with picket
signs reading "MORE BUTTER" and "FAIR CRUMBS".

The publish is atomic and self-checking: the bytes are first written
to a scratch file inside /output, flushed to disk, then renamed over
the target path, so the target never holds a partial file. The
published file is then hashed and compared with the source; a
mismatch makes the program exit with an error. A size guard rejects
an empty or unexpectedly large source image before anything is
written, and a failed publish leaves no scratch file behind.

Standard library only, no network. Deterministic: the program runs
twice and both runs write the same bytes.
"""
import hashlib
import os
import sys

# Sanity bound for a single meme image; a source outside this range
# means something is wrong with the committed file, not with the run.
MAX_SOURCE_BYTES = 10 * 1024 * 1024

BASE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(BASE, "entry.png")
OUT_DIR = "/output"
TARGET = os.path.join(OUT_DIR, "entry.png")
SCRATCH = os.path.join(OUT_DIR, ".entry.png.part")


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(1 << 16)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def publish():
    source_size = os.path.getsize(SOURCE)
    if source_size == 0:
        raise ValueError("source %s is empty" % SOURCE)
    if source_size > MAX_SOURCE_BYTES:
        raise ValueError(
            "source %s is %d bytes, over the %d-byte limit"
            % (SOURCE, source_size, MAX_SOURCE_BYTES))
    os.makedirs(OUT_DIR, exist_ok=True)
    try:
        with open(SOURCE, "rb") as src, open(SCRATCH, "wb") as dst:
            while True:
                block = src.read(1 << 16)
                if not block:
                    break
                dst.write(block)
            dst.flush()
            os.fsync(dst.fileno())
        os.replace(SCRATCH, TARGET)
    except BaseException:
        try:
            os.unlink(SCRATCH)
        except OSError:
            pass
        raise


def main():
    try:
        publish()
    except (OSError, ValueError) as exc:
        print("error: publish failed: %s" % exc, file=sys.stderr)
        return 1
    source_size = os.path.getsize(SOURCE)
    target_size = os.path.getsize(TARGET)
    if source_size != target_size:
        print("error: size mismatch: source %d bytes, published %d bytes"
              % (source_size, target_size), file=sys.stderr)
        return 1
    source_hash = digest(SOURCE)
    target_hash = digest(TARGET)
    if source_hash != target_hash:
        print("error: sha256 mismatch: source %s, published %s"
              % (source_hash, target_hash), file=sys.stderr)
        return 1
    print("published %s (%d bytes, sha256 %s)"
          % (TARGET, target_size, target_hash))
    return 0


if __name__ == "__main__":
    sys.exit(main())
