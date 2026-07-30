.. sqlite-lsm1 documentation master file, created by
   sphinx-quickstart on Mon Aug  3 01:29:51 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

sqlite-lsm1
===========

Fast Python bindings for `SQLite's LSM1 key/value store
<https://sqlite.org/src/dir?ci=trunk&name=ext/lsm1>`_. LSM1 originated in the
experimental SQLite4 project and now lives in the SQLite source tree.

Features:

* Embedded zero-conf database.
* Keys support in-order traversal using cursors.
* Atomic, streaming bulk upserts, deletes, and mixed operations.
* Sorted-input acceleration and direct immutable-run ingestion.
* Transactional (including nested transactions).
* Single writer/multiple reader MVCC based transactional concurrency model.
* Checksummed transaction log and crash recovery.
* Data is durable in the face of application or power failure.
* Thread-safe.
* Python 3.9 and newer.

The durable database is stored in one main file. While it is open, LSM1 also
uses ``-log`` and ``-shm`` sidecar files for recovery and shared state.

The source for ``sqlite-lsm1`` is `hosted on GitHub
<https://github.com/carlopires/python-lsm-db>`_.

.. note::
  If you encounter any bugs in the library, please `open an issue
  <https://github.com/carlopires/python-lsm-db/issues/new>`_, including a
  description of the bug and any related traceback.

Contents:

.. toctree::
   :maxdepth: 2
   :glob:

   installation
   quickstart
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
