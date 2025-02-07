# !/usr/bin/env python

from setuptools import setup
import re

with open('requirements.txt', 'r') as f:
    txt = f.read().split('\n')
requires = []
for line in txt:
    req = re.search(r'^(?![#-])(\S+)\s*#*.*?$', line.strip())
    if not req:
        continue
    requires.append(req.groups()[0])

setup(
    name='propnet',
    packages=['propnet'],
    version='0.0',
    author='Propnet Development Team',
    author_email='matt@mkhorton.net',
    description='Materials Science models, pre-alpha.',
    url='https://github.com/materialsintelligence/propnet',
    download_url='https://github.com/materialsintelligence/propnet/archive/0.0.tar.gz',
    entry_points={"console_scripts": ["propnet = propnet.cli:main"]},
    install_requires=requires
)
