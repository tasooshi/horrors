# -*- coding: utf-8 -*-
#######################################################################
# License: GNU General Public License v3.0                            #
# Homepage: https://github.com/tasooshi/horrors/                      #
# Version: 0.1                                                        #
#######################################################################

from distutils.core import setup


setup(
    name='horrors',
    version='0.1',
    package_dir={'horrors': 'horrors'},
    packages=['horrors'],
    author='tasooshi',
    author_email='tasooshi@pm.me',
    description='A micro-framework for writing attack scenarios starring multiple vulnerabilities',
    license='GNU General Public License v3.0',
    url='https://github.com/tasooshi/horrors/',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.9',
    ]
)
