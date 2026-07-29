# Python LSM-DB

Fast Python bindings for SQLite's
[LSM1 key/value store](https://sqlite.org/src/dir?ci=trunk&name=ext/lsm1).
LSM1 originated in the experimental SQLite4 project and now lives in the
SQLite source tree. This package builds the engine and its Cython wrapper into
a single native Python extension.

Features:

- Embedded, zero-configuration key/value database.
- Ordered traversal and nearest-key lookups using cursors.
- Nested transactions.
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
python -m pip install lsm-db
```

Building from source requires a C compiler. Cython is installed automatically
in pip's isolated build environment:

```console
git clone https://github.com/coleifer/python-lsm-db
cd python-lsm-db
python -m pip install .
```

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

`update()` inserts a dictionary of records:

```python
db.update({"alpha": "a", "beta": "b"})
```

Each insertion is its own transaction unless `update()` is wrapped in an
explicit transaction.

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

Build the documentation with:

```console
python -m pip install -r docs/requirements.txt
sphinx-build -W -b html docs docs/_build/html
```

The complete API reference is available at
https://lsm-db.readthedocs.io/en/latest/api.html.

## License

The Python wrapper is distributed under the MIT License. The vendored SQLite
LSM1 sources are in the public domain. See `LICENSE` and `SQLITE_LICENSE`.
