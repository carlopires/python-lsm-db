.. _quickstart:

Quick-start
===========

Create a database by passing its path to :py:class:`lsm.LSM`:

.. code-block:: pycon

    >>> from lsm import LSM
    >>> db = LSM('test.ldb')

Keys and values
---------------

The database has a dictionary-like API:

.. code-block:: pycon

    >>> db['foo'] = 'bar'
    >>> db['foo']
    b'bar'
    >>> 'foo' in db
    True
    >>> del db['foo']
    >>> 'foo' in db
    False

Strings are encoded as UTF-8. Retrieved keys and values are always
:class:`bytes`. Other input objects are converted to strings before encoding;
use bytes directly when an exact binary representation matters.

Missing exact lookups raise :class:`KeyError`. Use :data:`lsm.SEEK_LE` and
:data:`lsm.SEEK_GE` for nearest-key searches:

.. code-block:: pycon

    >>> from lsm import SEEK_GE, SEEK_LE
    >>> db.update({'k0': '0', 'k1': '1', 'k2': '2'})
    >>> db['k1xx', SEEK_LE]
    b'1'
    >>> db['k1xx', SEEK_GE]
    b'2'

Each call to :py:meth:`lsm.LSM.insert` is its own transaction unless it is
already inside an explicit transaction. Wrap :py:meth:`lsm.LSM.update` in a
transaction when the complete batch must be atomic.

Slices and iteration
--------------------

Iteration yields ``(key, value)`` byte pairs in bytewise key order:

.. code-block:: pycon

    >>> list(db)
    [(b'k0', b'0'), (b'k1', b'1'), (b'k2', b'2')]

Slices return generators and include both bounds:

.. code-block:: pycon

    >>> list(db['k0':'k2'])
    [(b'k0', b'0'), (b'k1', b'1'), (b'k2', b'2')]
    >>> list(db['k1':])
    [(b'k1', b'1'), (b'k2', b'2')]
    >>> list(db[:'k1'])
    [(b'k0', b'0'), (b'k1', b'1')]

A descending pair of bounds selects reverse order. For an open-ended reverse
slice, use ``True`` as the step:

.. code-block:: pycon

    >>> list(db['k2':'k0'])
    [(b'k2', b'2'), (b'k1', b'1'), (b'k0', b'0')]
    >>> list(db['k1'::True])
    [(b'k1', b'1'), (b'k0', b'0')]

Slice deletion excludes the boundary keys:

.. code-block:: pycon

    >>> del db['k0':'k2']
    >>> list(db)
    [(b'k0', b'0'), (b'k2', b'2')]

Cursors
-------

Cursors provide explicit control over ordered traversal:

.. code-block:: python

    with db.cursor() as cursor:
        for key, value in cursor:
            print(key, value)

    with db.cursor() as cursor:
        cursor.seek('k0', SEEK_GE)
        rows = list(cursor.fetch_until('k99'))

Always close cursors. A database cannot close while any of its cursors remain
open, so using the :py:meth:`lsm.LSM.cursor` context manager is recommended.

Transactions
------------

Transactions may be nested:

.. code-block:: python

    with db.transaction():
        db['k1'] = 'outer'

        with db.transaction() as nested:
            db['k2'] = 'nested'
            nested.rollback()

    assert db['k1'] == b'outer'
    assert 'k2' not in db

:py:meth:`lsm.LSM.transaction` can also decorate a function. A normal return
commits and an exception rolls back:

.. code-block:: python

    @db.transaction()
    def store_pair(key1, value1, key2, value2):
        db[key1] = value1
        db[key2] = value2

Explicit :py:meth:`lsm.LSM.begin`, :py:meth:`lsm.LSM.commit`, and
:py:meth:`lsm.LSM.rollback` methods are available when a context manager is
not suitable.

Maintenance
-----------

Automatic flushing, merging, and checkpointing are enabled by default.
Applications that disable automatic work should schedule
:py:meth:`lsm.LSM.flush`, :py:meth:`lsm.LSM.work`, and
:py:meth:`lsm.LSM.checkpoint` themselves. ``checkpoint()`` returns the number
of KB made durable in the database file.
