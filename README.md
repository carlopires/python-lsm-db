# sqlite-lsm1

Fast Python bindings for SQLite's
[LSM1 key/value store](https://sqlite.org/src/dir?ci=trunk&name=ext/lsm1).
LSM1 originated in the experimental SQLite4 project and now lives in the
SQLite source tree. This package builds the engine and its Cython wrapper into
a single native Python extension.

Features:

- Embedded, zero-configuration key/value database.
- Ordered traversal and nearest-key lookups using cursors.
- Nested transactions.
- Atomic streaming upserts, deletes, and mixed write batches.
- Validated sorted-write acceleration and direct sorted-run ingestion.
- Single-writer/multiple-reader MVCC concurrency.
- Checksummed transaction log and crash recovery.
- Linux, macOS, and Windows wheel builds.
- Python 3.9 and newer.

The durable database is stored in one main file. While a database is open,
LSM1 also uses `-log` and `-shm` sidecar files for recovery and shared state.
The sidecars are normally removed when the final connection closes cleanly.

## Installation

Install a published wheel with pip:

```console
python -m pip install sqlite-lsm1
```

Building from source requires a C compiler. Cython is installed automatically
in pip's isolated build environment:

```console
git clone https://github.com/carlopires/python-lsm-db
cd python-lsm-db
python -m pip install .
```

The distribution is named `sqlite-lsm1`; the import remains `lsm` for
compatibility with applications using the original package.

## Quick start

Create a database by passing its path to `LSM`:

```python
from lsm import LSM

db = LSM("test.ldb")
```

### Keys and values

The database has a dictionary-like API:

```python
db["foo"] = "bar"
assert db["foo"] == b"bar"

for i in range(4):
    db[f"k{i}"] = str(i)

assert "k3" in db
assert "k4" not in db

del db["k3"]
```

Strings are encoded as UTF-8. Retrieved keys and values are always `bytes`.
Other input objects are converted to strings before being encoded; use
`bytes` directly when an exact binary representation matters.

Missing exact lookups raise `KeyError`. Nearest-key searches use `SEEK_LE`
and `SEEK_GE`:

```python
from lsm import SEEK_GE, SEEK_LE

assert db["k1xx", SEEK_LE] == b"1"
assert db["k1xx", SEEK_GE] == b"2"
```

`upsert_many()` atomically inserts or replaces either a mapping or an
iterable of `(key, value)` pairs. `insert_many()` is a compatibility alias:

```python
rows = ((f"key-{i}", f"value-{i}") for i in range(10_000))
inserted = db.upsert_many(rows, batch_size=4096)
assert inserted == 10_000
```

The input is streamed through bounded native chunks while one outer
transaction preserves all-or-nothing behavior. If conversion or a native
write fails, every chunk is rolled back. `update()` provides the same
behavior for mappings. Point deletes and ordered mixed operations have
matching APIs:

```python
db.update({"alpha": "a", "beta": "b"})
db.delete_many(["old-1", "old-2"])

db.apply_batch([
    ("put", "account:1", "active"),
    ("delete", "stale-key"),
    ("delete_range", "session:0000", "session:9999"),
])
```

For incrementally assembled mixed batches, use the context manager. It
flushes bounded chunks internally but commits them as one atomic unit:

```python
with db.write_batch(batch_size=4096) as batch:
    batch.put("a", "1")
    batch.delete("b")
    batch.delete_range("cache:0000", "cache:9999")
```

When point-operation keys are strictly increasing, pass `sorted=True`.
Ordering is validated across chunk boundaries and the native engine uses its
right-edge append path once possible:

```python
db.upsert_many(sorted_rows, sorted=True)
db.delete_many(sorted_keys, sorted=True)
```

For a large, already sorted initial load, `ingest_sorted()` bypasses the live
tree and writes one immutable disk run:

```python
db.ingest_sorted(sorted_rows)
```

This direct path materializes the input before writing, requires strictly
increasing keys, and cannot run with an open transaction or cursor. It
publishes the completed run atomically and checkpoints it before returning.

### Slices and iteration

Iteration yields `(key, value)` byte pairs in bytewise key order:

```python
list(db)
# [(b"alpha", b"a"), (b"beta", b"b"), (b"foo", b"bar"),
#  (b"k0", b"0"), (b"k1", b"1"), (b"k2", b"2")]
```

Slices return generators and include both bounds:

```python
list(db["k0":"k9"])
# [(b"k0", b"0"), (b"k1", b"1"), (b"k2", b"2")]

list(db["k0":])
list(db[:"k2"])
```

A descending pair of bounds selects reverse order. For an open-ended reverse
slice, use `True` as the step:

```python
list(db["k2":"k0"])
# [(b"k2", b"2"), (b"k1", b"1"), (b"k0", b"0")]

list(db["k2"::True])
```

Slice deletion excludes the boundary keys:

```python
del db["k0":"k9"]
```

### Cursors

Cursors provide explicit control over traversal:

```python
with db.cursor() as cursor:
    for key, value in cursor:
        print(key, value)

with db.cursor() as cursor:
    cursor.seek("k0", SEEK_GE)
    rows = list(cursor.fetch_until("k99"))
```

Always close cursors. A database cannot close while any of its cursors remain
open, so using the cursor context manager is recommended.

### Transactions

Transactions may be nested:

```python
with db.transaction():
    db["k1"] = "outer"

    with db.transaction() as nested:
        db["k2"] = "nested"
        nested.rollback()

assert db["k1"] == b"outer"
assert "k2" not in db
```

`transaction()` can also decorate a function. A normal return commits and an
exception rolls back:

```python
@db.transaction()
def store_pair(key1, value1, key2, value2):
    db[key1] = value1
    db[key2] = value2
```

Explicit `begin()`, `commit()`, and `rollback()` methods are available when a
context manager is not suitable.

### Threads

Potentially blocking database, cursor, and maintenance operations release the
GIL. Each connection serializes access with a re-entrant lock. A transaction
owns its connection until its outermost commit or rollback, so another thread
cannot interleave work with it.

Use one `LSM` connection per worker thread when actual overlap is desired.
LSM1 permits concurrent readers but still has a single-writer model.

### Maintenance and tuning

The most commonly used tuning properties are:

- `autoflush`: live in-memory tree limit in KB; default 1024.
- `autocheckpoint`: automatic checkpoint interval in KB; default 2048.
- `automerge`: target number of segments merged at once; default 4.
- `autowork`: automatically flush and merge during writes; enabled by
  default.
- `write_safety`: `SAFETY_OFF`, `SAFETY_NORMAL`, or `SAFETY_FULL`.
- `transaction_log`: enable the recovery log; enabled by default.
- `multiple_processes`: enable file locking and shared state; enabled by
  default.
- `mmap`: configure memory-mapped reads.

Applications that disable automatic work should schedule `flush()`, `work()`,
and `checkpoint()` themselves. `checkpoint()` returns the number of KB made
durable in the database file.

## Development

Run the tests from an installed source checkout:

```console
python tests.py
```

Compare the write paths with the end-to-end durable bulk benchmark:

```console
python benchmarks/bulk_ops.py --rows 50000 --batch-size 4096
```

Build the documentation with:

```console
python -m pip install -r docs/requirements.txt
sphinx-build -W -b html docs docs/_build/html
```

The complete API reference is maintained in the
[project documentation](https://github.com/carlopires/python-lsm-db/tree/master/docs).

## License

The Python wrapper is distributed under the MIT License. The vendored SQLite
LSM1 sources are in the public domain. See `LICENSE` and `SQLITE_LICENSE`.
