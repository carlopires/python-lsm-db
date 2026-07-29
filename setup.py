import glob

from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension

library_source = glob.glob('src/*.c')
lsm_extension = Extension(
    'lsm',
    sources=['lsm.pyx'] + library_source)

setup(ext_modules=cythonize([lsm_extension], language_level=3))
