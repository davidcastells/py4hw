# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

                         
setup(
    name='py4hw',
    version='2025.1',
    author='David Castells-Rufas',
    author_email='david.castells@uab.cat',
    description='py4hw is a library to model, and simulate digital logic circuits. It promotes the use of structural and behavioural design styles to build hardware.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/davidcastells/py4hw',
    install_requires=open('requires.txt').readlines(),
    tests_require=open('requires.txt').readlines(),
    packages=find_packages(),
    package_data={'': ['*.png']}
)
