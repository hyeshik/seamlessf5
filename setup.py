#!/usr/bin/env python3
#
# Copyright (c) 2018 Institute for Basic Science
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

from setuptools import setup

setup(
    name='seamlessf5',
    packages=['seamlessf5'],
    version='0.1',
    description='Helpers for smoother transitioning to multi-read FAST5 files',
    author='Hyeshik Chang',
    author_email='hyeshik@snu.ac.kr',
    url='https://github.com/hyeshik/seamlessf5',
    download_url='https://github.com/hyeshik/seamlessf5/releases',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    include_package_data=True,
    keywords=['nanopore', 'fast5', 'converter', 'wrapper'],
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Healthcare Industry',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    install_requires=[
        'h5py >= 2.9.0',
        'ont-fast5-api >= 1.0.1',
        'progressbar33 >= 2.4',
    ],
    entry_points={
        'console_scripts': [
            'sf5_read_fast5_basecaller.py = seamlessf5.albacore_hooks:read_fast5_basecaller',
            'sf5_full_1dsq_basecaller.py = seamlessf5.albacore_hooks:full_1dsq_basecaller',
            'sf5_paired_read_basecaller.py = seamlessf5.albacore_hooks:paired_read_basecaller',
            'sf5_single_to_multi_fast5 = seamlessf5.single2multi_hooks:run_single2multi',
        ],
    },
)
