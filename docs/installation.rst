.. _installation:

Installation
============

You can use ``pip`` to install ``sqlite-lsm1``:

.. code-block:: console

    pip install sqlite-lsm1

The project is hosted at https://github.com/carlopires/python-lsm-db and can
be installed from source:

.. code-block:: console

    git clone https://github.com/carlopires/python-lsm-db
    cd python-lsm-db
    python -m pip install .

.. note::
    Building from source requires a C compiler. Cython is declared as a build
    dependency and is installed automatically by modern versions of ``pip``
    in an isolated build environment.

After installing ``sqlite-lsm1``, run the unit tests from a source checkout:

.. code-block:: console

    python tests.py
