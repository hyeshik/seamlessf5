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

from . import __version__
import os
import sys
import logging
import tarfile
import h5py
from io import BytesIO
from progressbar import progressbar
from distutils.version import LooseVersion
from ont_fast5_api import fast5_file
from ont_fast5_api.conversion_tools import conversion_utils

TARFILE_SUFFIXES = ['.tar', '.tar.gz', '.tar.bz2', '.tgz', '.tbz2']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('single_to_multi_fast5')

pbar = None
file_contents = {}


class TarFAST5Retriever:

    def __init__(self, fname):
        self.tarf = tarfile.open(fname, 'r')
        self.tariter = iter(self.tarf)
        self.nread = 0

    def __iter__(self):
        return self

    def __next__(self):
        global tarentry

        for el in self.tariter:
            if el.isfile() and el.name.lower().endswith('.fast5'):
                file_contents[el.name] = BytesIO(self.tarf.extractfile(el).read())
                self.nread += 1
                if pbar is not None:
                    pbar.maxval = self.nread
                return el

        raise StopIteration


class SLFast5File(fast5_file.Fast5File):

    def __init__(self, fname, mode='r'):
        if isinstance(fname, tarfile.TarInfo):
            tarinfo = fname
            fname = tarinfo.name
        return super(SLFast5File, self).__init__(fname, mode)


class SLHDF5File(h5py.File):

    def __init__(self, fname, *args, **kwds):
        if fname in file_contents:
            kwds['driver'] = 'fileobj'
            fname = file_contents[fname]
        super(SLHDF5File, self).__init__(fname, *args, **kwds)


def sl_get_fast5_file_list(input_path, recursive, ofun=conversion_utils.get_fast5_file_list):
    if os.path.isfile(input_path) and any(
            input_path.endswith(sufx) for sufx in TARFILE_SUFFIXES):
        return TarFAST5Retriever(input_path)
    else:
        return ofun(input_path, recursive)

def sl_batcher(iterable, n=1, ofun=conversion_utils.batcher):
    try:
        l = len(iterable)
    except TypeError:
        l = None # Iteration-only object

    if l is not None:
        for ndx in range(0, l, n):
            yield iterable[ndx:min(ndx + n, l)]
    else:
        buf = []
        for el in iterable:
            buf.append(el)
            if len(buf) >= n:
                yield buf
                file_contents.clear() # Clear up the cached fast5 contents from a tar file.
                buf = []

        if buf:
            yield buf

def sl_get_progress_bar(num_reads, ofun=conversion_utils.get_progress_bar):
    global pbar
    pbar = ofun(num_reads)
    return pbar

def sl_len(obj):
    if isinstance(obj, TarFAST5Retriever):
        return None
    else:
        return len(obj)

def check_compatibility():
    return LooseVersion(h5py.__version__) >= LooseVersion('2.9.0')

def show_banner():
    print("""\
SeamlessF5 {} activated!
""".format(__version__))

def install_hooks():
    conversion_utils.get_fast5_file_list = sl_get_fast5_file_list
    conversion_utils.batcher = sl_batcher
    conversion_utils.get_progress_bar = sl_get_progress_bar

    fast5_file.Fast5File = SLFast5File
    h5py.File = SLHDF5File

    from ont_fast5_api.conversion_tools import single_to_multi_fast5
    single_to_multi_fast5.len = sl_len

def run_single2multi():
    if not check_compatibility():
        logger.error('The tar input support requires a minimum H5PY version 2.9.0 at least.')
        sys.exit(1)

    show_banner()
    install_hooks()

    from ont_fast5_api.conversion_tools import single_to_multi_fast5
    single_to_multi_fast5.main()

if __name__ == '__main__':
    run_single2multi()
