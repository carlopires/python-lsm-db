"""Simple end-to-end benchmark for sqlite-lsm1 bulk write paths."""

import argparse
import os
import tempfile
import time

from lsm import LSM


def insert_one_by_one(db, rows):
    for key, value in rows:
        db.insert(key, value)


def benchmark(label, rows, write):
    filename = tempfile.mktemp()
    db = LSM(filename)
    started = time.perf_counter()
    try:
        write(db, rows)
        db.flush()
        db.checkpoint()
        elapsed = time.perf_counter() - started
    finally:
        db.close()
        for suffix in ("", "-log", "-shm"):
            try:
                os.unlink(filename + suffix)
            except FileNotFoundError:
                pass
    rate = len(rows) / elapsed
    print(f"{label:24} {elapsed:8.3f}s  {rate:12,.0f} ops/s")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--rows", type=int, default=50_000)
    parser.add_argument("--batch-size", type=int, default=4096)
    args = parser.parse_args()
    rows = [
        (f"key-{i:09d}".encode(), f"value-{i:09d}".encode())
        for i in range(args.rows)
    ]

    benchmark(
        "insert() per row",
        rows,
        insert_one_by_one,
    )
    benchmark(
        "upsert_many()",
        rows,
        lambda db, values: db.upsert_many(
            values, batch_size=args.batch_size
        ),
    )
    benchmark(
        "upsert_many(sorted=True)",
        rows,
        lambda db, values: db.upsert_many(
            values, batch_size=args.batch_size, sorted=True
        ),
    )
    benchmark(
        "ingest_sorted()",
        rows,
        lambda db, values: db.ingest_sorted(values),
    )


if __name__ == "__main__":
    main()
