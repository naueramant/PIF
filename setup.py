#!/usr/bin/env python3

from setuptools import setup

setup(name='pif',
	version='1.0',
	description='Python + information flow',
	author='David, Jonas, Ulrik',
	author_email='jonastranberg93@gmail.com',
	zip_safe=True,
	scripts=['pif'],
	packages=[],
	install_requires=['astor', 'termcolor'])
