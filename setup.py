#!/usr/bin/env python3

from setuptools import setup, find_packages

import pytelegram

setup(name='pytelegram',
      version='0.1',
      description='Telegram Python bindings',
      author='Goekcen Eraslan',
      author_email='gokcen.eraslan@gmail.com',
      url='http://github.com/gokceneraslan/pytelegram',
      packages=find_packages(),
      install_requires = ['cffi'],
      setup_requires = ['cffi'],
      zip_safe=False,
      ext_package='pytelegram',
      ext_modules=[pytelegram.ffi.verifier.get_extension()]
     )
