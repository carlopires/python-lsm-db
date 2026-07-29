.. _api:

API Documentation
=================

.. py:module:: lsm

.. autoclass:: LSM
    :members:
      __init__,
      open,
      close,
      page_size,
      block_size,
      multiple_processes,
      readonly,
      write_safety,
      autoflush,
      autowork,
      automerge,
      autocheckpoint,
      mmap,
      transaction_log,
      pages_written,
      pages_read,
      checkpoint_size,
      tree_size,
      __enter__,
      insert,
      update,
      fetch,
      fetch_bulk,
      fetch_range,
      delete,
      delete_range,
      __getitem__,
      __setitem__,
      __delitem__,
      __contains__,
      __iter__,
      __reversed__,
      keys,
      values,
      incr,
      flush,
      work,
      checkpoint,
      begin,
      commit,
      rollback,
      transaction,
      cursor


.. autoclass:: Cursor
    :members:
      open,
      close,
      __enter__,
      __iter__,
      compare,
      seek,
      is_valid,
      first,
      last,
      next,
      previous,
      fetch_until,
      fetch_range,
      key,
      value,
      keys,
      values


.. autoclass:: Transaction
    :members:
      commit,
      rollback

Constants
---------

Seek methods, can be used when fetching records or slices.

``SEEK_EQ``
  Match the key exactly. If the key does not exist, the cursor is left at EOF
  (invalidated) and :py:meth:`Cursor.is_valid` returns ``False``.

``SEEK_LE``
  Match the key exactly or leave the cursor pointing to the largest key that
  precedes it. If the database contains no such key, the cursor is left at
  EOF.

``SEEK_GE``
  Match the key exactly or leave the cursor pointing to the smallest key that
  follows it. If the database contains no such key, the cursor is left at
  EOF.

If the fourth parameter is ``SEEK_LEFAST``, this function searches the
database in a similar manner to ``SEEK_LE``, with two differences:

Even if a key can be found (the cursor is not left at EOF), the
lsm_csr_value() function may not be used (attempts to do so return
LSM_MISUSE).

The key that the cursor is left pointing to may be one that has
been recently deleted from the database. In this case it is
guaranteed that the returned key is larger than any key currently
in the database that is less than or equal to (pKey/nKey).

``SEEK_LEFAST`` requests are intended to be used to allocate database
keys.

Values accepted by the :py:attr:`LSM.write_safety` property:

* ``SAFETY_OFF``
* ``SAFETY_NORMAL``
* ``SAFETY_FULL``
