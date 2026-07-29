import glob
import sys

from Cython.Build import cythonize
from setuptools import setup
from setuptools.extension import Extension

library_source = glob.glob('src/*.c')
if sys.platform == 'win32':
    define_macros = [('LSM_MUTEX_WIN32', '1')]
    thread_args = []
else:
    define_macros = [('LSM_MUTEX_PTHREADS', '1')]
    thread_args = ['-pthread']

lsm_extension = Extension(
    'lsm',
    sources=['lsm.pyx'] + library_source,
    define_macros=define_macros,
    extra_compile_args=thread_args,
    extra_link_args=thread_args)

setup(ext_modules=cythonize([lsm_extension], language_level=3))
