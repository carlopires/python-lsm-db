# Repository Overview

This is a compact, mature Cython binding around SQLite’s experimental LSM1
key/value engine, distributed as ``sqlite-lsm1``. The checkout was reviewed
on `master` and prepared for its first fork release as version 0.8.0. It
contains 32 tracked files, about 25K lines, and 103 commits dating from 2015
to January 2026.

Most of the database implementation is vendored C from SQLite. The
Python-facing layer is concentrated in [`lsm.pyx`](lsm.pyx).

## Mental model

```text
Python API
  → Cython wrapper
  → transaction log + MVCC in-memory B-tree
  → immutable sorted disk segments
  → background merging
  → checkpointed database file
```

A write is UTF-8/bytes encoded, logged, applied to the live in-memory tree,
and committed. When the tree reaches the autoflush threshold, it becomes
immutable and is flushed as a sorted segment. Worker activity merges
segments; checkpointing records the durable layout in one of two metadata
pages.

Reads use a multi-cursor that merges the live tree, old tree, and disk
segments into one ordered view. Opening a cursor acquires a snapshot,
providing MVCC behavior while another connection writes.

Relevant engine components:

- [`src/lsm_main.c`](src/lsm_main.c): public C API, writes, cursors, and
  transactions.
- [`src/lsm_tree.c`](src/lsm_tree.c): order-4 MVCC B-tree and nested rollback.
- [`src/lsm_log.c`](src/lsm_log.c): checksummed transaction log and recovery.
- [`src/lsm_sorted.c`](src/lsm_sorted.c): cursors, sorted runs, flushing,
  merging, and maintenance.
- [`src/lsm_ckpt.c`](src/lsm_ckpt.c): checkpoint serialization and recovery
  position.
- [`src/lsm_file.c`](src/lsm_file.c): pages, blocks, cache, mmap, and file
  layout.
- `src/lsm_shared.c`: snapshots, locks, shared state, and multi-process
  coordination.
- `src/lsm_unix.c` / `src/lsm_win32.c`: platform I/O environments.

## Storage behavior

The main file begins with two fixed 4KB metadata pages, followed by
configurable database pages arranged into blocks. Defaults are:

- Page size: 4KB
- Block size: 1MB
- Autoflush: 1MB
- Autocheckpoint: 2MB
- Automerge: four segments
- Transaction log: enabled
- Safety: normal
- Multi-process coordination: enabled
- mmap: enabled by default on 64-bit systems

Despite the “single-file database” description, an active database uses
three files:

- `database`
- `database-log`
- `database-shm`

A runtime probe confirmed that the log and shared-memory sidecars are removed
after the final clean close. They may remain after a crash and are part of
recovery.

Deletes are tombstones in the in-memory tree rather than physical removal.
Range deletion excludes both boundary keys.

## Python API

The wrapper exposes three main types:

- `LSM`: connection, dictionary operations, transactions, configuration,
  and maintenance.
- `Cursor`: ordered traversal and nearest-key seeking.
- `Transaction`: context manager and decorator.

Notable behavior:

- Inputs accept `bytes`, strings, and most other objects via string
  conversion.
- Returned keys and values are always `bytes`, even when strings were
  inserted.
- Ordering is raw bytewise ordering: `memcmp`, then key length.
- Slices are inclusive and automatically reverse when the start exceeds the
  end.
- `SEEK_EQ`, `SEEK_LE`, `SEEK_GE`, and `SEEK_LEFAST` are exposed.
- Individual writes automatically get their own transaction.
- `insert_many()` streams a mapping or iterable of pairs through one atomic
  nested transaction and returns the inserted row count.
- `update()` delegates mappings to the same atomic bulk path.
- Nested transactions are implemented with tree and log marks.
- `incr()` stores a signed 64-bit big-endian integer, but its declared return
  type is only a C `int`.

The configuration/property machinery, dictionary/range behavior, and
transaction implementation all live in [`lsm.pyx`](lsm.pyx).

## Concurrency

The underlying model is single-writer/multiple-reader with file locks and
shared-memory snapshots across processes.

The build enables SQLite LSM1's pthread mutexes on Unix and native mutexes on
Windows. Potentially blocking database, cursor, and maintenance operations
release the GIL. Each Python connection also has a re-entrant lock, and an
open transaction retains ownership of that lock until its outermost commit or
rollback. This prevents calls on another thread from interleaving with a
transaction or racing connection lifetime.

Separate connections are still recommended for worker threads that need
actual overlap. The engine permits concurrent readers but retains its
single-writer model.

## Verification

An isolated PEP 517 wheel was built on Python 3.14.4:

- The wheel built successfully.
- The native extension imported successfully.
- All 42 tests passed after the bulk-write and concurrency changes.
- The working checkout remained untouched during exploration.

The tests cover dictionary behavior, atomic bulk writes, range traversal,
cursors, nested transactions, transaction ownership, configuration,
information counters, and an eight-thread write test. CI runs them on Linux
with Python 3.9, 3.10, 3.12, and 3.14 through
[`.github/workflows/tests.yaml`](.github/workflows/tests.yaml). Tagged
releases build Linux, macOS, and Windows wheels and publish directly to PyPI
through [`.github/workflows/wheels.yaml`](.github/workflows/wheels.yaml).

A strict Sphinx build now succeeds without warnings.

## Weaknesses identified during the audit

The first six items below were addressed in the maintenance commit that added
this overview. They are retained here as an audit trail.

### 1. Packaging metadata was stale

Resolved: [`pyproject.toml`](pyproject.toml) now declares Python 3.9 or newer,
uses current Python classifiers, identifies the MIT license, and includes both
project and SQLite license notices.

### 2. The source-distribution story was inconsistent

Resolved: the build now consistently requires Cython, the obsolete `lsm.c`
fallback was removed, the missing license files were added, the manifest
matches the checkout, and the release workflow builds sdists through PEP 517.

### 3. Some native failures were mishandled

Resolved: cursor creation, seeking, and key/value extraction now check and
propagate native return codes. Partially opened database handles are also
closed if initialization fails.

### 4. Transaction depth could desynchronize on begin errors

Resolved: a failed `begin()` no longer increments Python's transaction depth.
Commit and rollback update Python state after the native call while preserving
the native engine's documented close-on-commit-error behavior.

### 5. The checkpoint API required a meaningless argument

Resolved: `checkpoint()` now takes no required argument and returns the
number of KB written. The legacy ignored argument remains accepted for
compatibility.

### 6. Documentation was noticeably stale

Resolved: the README and Sphinx quick-start now document Python 3, byte
results, sidecar files, atomic update guidance, maintenance behavior, and
modern installation. The API reference includes `incr()`, correct seek
semantics, and the current project version.

### 7. Important reliability scenarios are untested

There are still no tests for crash recovery, power-loss simulations,
multi-process access, or sustained flush/merge workloads. Release-tag wheel
builds run the suite on Linux, macOS, and Windows, but non-Linux platforms are
not tested on every push.

## Overall assessment

The core engine is sophisticated and the public wrapper is pleasantly small.
The happy path is solid and fast, including current Python 3.14 support. The
maintenance pass resolved the main wrapper-boundary, packaging, licensing,
bulk-write, GIL, mutex, and documentation issues found during the audit. The
remaining reliability test gaps deserve further work.
