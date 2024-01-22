#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

install_requires = ['neo4j', 'torch']
setup_requires = []
tests_require = []

classifiers = [
    'Development Status :: 3 - Alpha',
    'Programming Language :: Python :: 3',
]

setup(
    name="graphDBInterface",
    version="0.0.1",
    author="BUPT-GAMMA LAB",
    author_email="jixy2314@bupt.edu.cn",
    maintainer="Xingyuan Ji",
    description="Graph Database Interface",
    url="https://github.com/xy-Ji/graphDBInterface",
    download_url="https://github.com/xy-Ji/graphDBInterface",
    python_requires='>=3.9',
    packages=find_packages(),
    install_requires=install_requires,
    include_package_data=True,
    classifiers=classifiers
)
