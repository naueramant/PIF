#!/usr/bin/env python3

from setuptools import setup

setup(name='pif',
	version='1.0',
	description='Python Information Flow interpreter',
	zip_safe=True,
	packages=['pifcore'],
	scripts=['pif'],
	install_requires=['termcolor'])