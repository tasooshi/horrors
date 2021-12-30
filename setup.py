# -*- coding: utf-8 -*-
#######################################################################
# License: MIT License                                                #
# Homepage: https://github.com/tasooshi/horrors/                      #
# Version: 0.5                                                        #
#######################################################################

from distutils.core import setup


setup(
    name='horrors',
    version='0.5',
    package_dir={'horrors': 'horrors'},
    packages=[
        'horrors',
        'horrors/services',
        'horrors/services/complete',
        'horrors/services/simple',
        'horrors/services/utility',
    ],
    author='tasooshi',
    author_email='tasooshi@pm.me',
    description='A micro-framework for writing attack scenarios starring multiple vulnerabilities',
    license='MIT License',
    url='https://github.com/tasooshi/horrors/',
    install_requires=(
        'aiohttp==3.8.1',
        'beautifulsoup4==4.10.0',
        'sanic==21.9.3',
        'tinydb==4.5.2',
    ),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
    ]
)
