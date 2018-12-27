#
# Copyright (c) 2018 Hyeshik Chang
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
import subprocess
import h5py
import importlib.machinery
import shutil
from ont_fast5_api.multi_fast5 import MultiFast5File
from ont_fast5_api.conversion_tools import multi_to_single_fast5
from ont_fast5_api import fast5_info
from albacore import read_metadata, input_utils, time_utils, log_utils

READID_SEPARATOR = '___read_'
FAST5_SUFFIX = '.fast5'

def is_mf5read(enc):
    return enc.lower().endswith(FAST5_SUFFIX) and READID_SEPARATOR in enc

def split_mf5read(enc):
    if not enc.lower().endswith(FAST5_SUFFIX):
        return enc, None

    fname, read_id = enc[:-len(FAST5_SUFFIX)].rsplit(READID_SEPARATOR, 1)
    return fname + enc[-len(FAST5_SUFFIX):], read_id

def join_mf5read(filename, read_id):
    if not filename.lower().endswith(FAST5_SUFFIX):
        return filename

    return ''.join([
        filename[:-len(FAST5_SUFFIX)], READID_SEPARATOR,
        read_id, filename[-len(FAST5_SUFFIX):]])

class SLReadMetadata(read_metadata.ReadMetadata):
    def _read_fast5(self):
        if is_mf5read(self.filename) and not os.path.isfile(self.filename):
            return self._read_fast5_multi()
        else:
            return super(read_metadata.ReadMetadata, self)._read_fast5()

    def _get_readinfo(self, read):
        readattrs = read.handle['Raw'].attrs

        read_id = readattrs['read_id'].decode()
        start_time = int(readattrs['start_time'])
        duration = int(readattrs['duration'])
        mux = int(readattrs.get('start_mux', 0))
        median_before = float(readattrs.get('median_before', -1.0))
        return fast5_info.ReadInfo(0, read_id, start_time, duration, mux, median_before)

    def _read_fast5_multi(self):
        fname, read_id = split_mf5read(self.filename)
        if read_id is None:
            raise ValueError('A multi-read fast5 is expected.')

        with MultiFast5File(fname, 'r') as fh:
            read = fh.get_read(read_id)

            read_info = self._get_readinfo(read)
            tracking_id = read.get_tracking_id()
            channel_data = read.get_channel_info()
            context_tags = read.get_context_tags()

            self.read_number = 0
            self.raw = read.get_raw_data(start=0, end=read_info.duration, scale=True)

        self.data_id = os.path.basename(self.filename)
        self.read_id = read_info.read_id
        self.start_time = read_info.start_time
        self.channel_id = channel_data['channel_number']
        self.sampling_rate = channel_data['sampling_rate']
        self.run_id = tracking_id['run_id']
        self.label = os.path.splitext(os.path.basename(self.filename))[0]
        self.mux = read_info.start_mux
        self.flowcell_id = tracking_id['flow_cell_id']
        self.device_id = tracking_id['device_id']
        self.hostname = tracking_id['hostname']
        self.exp_start_time = tracking_id['exp_start_time']
        self.median_before = read_info.median_before
        if 'sample_id' not in tracking_id:
            tracking_id['sample_id'] = 'none'
        self.sample_id = tracking_id['sample_id']
        self.tracking_id = tracking_id
        self.context_tags = context_tags

        offset_seconds = self.start_time / self.sampling_rate
        start_utc = time_utils.compute_start_timestamp(self.exp_start_time,
                                                       offset_seconds)
        self.start_time_utc = start_utc

        self.section = {}  # for fastq handler to store section data
        self.section_sam_output = {}

def sl_find_input_files(opts, ofun=input_utils._find_input_files):
    files = ofun(opts)
    files_expanded = []

    for fname in files:
        try:
            with h5py.File(fname, 'r') as f5:
                for nodename in f5.keys():
                    if not nodename.startswith('read_'):
                        continue

                    read_id = nodename.split('_', 1)[1]
                    encoded_fname = join_mf5read(fname, read_id)
                    files_expanded.append(encoded_fname)
        except:
            files_expanded.append(fname)

    return files_expanded

def fix_converted_fast5(fname):
    with h5py.File(fname, 'a') as hf:
        if 'Analyses' not in hf:
            hf.create_group('Analyses')

def sl_copyfile(src, dest, ofun=shutil.copyfile):
    if is_mf5read(src):
        filename, read_id = split_mf5read(src)
        try:
            with MultiFast5File(filename, 'r') as mf5:
                read = mf5.get_read(read_id)
                multi_to_single_fast5.create_single_f5(dest, read)
                fix_converted_fast5(dest)
        except:
            import traceback
            traceback.print_exc()
            raise
    else:
        ofun(src, dest)

def sl_initialise_logger(*args, ofun=log_utils.initialise_logger, **kwds):
    import logging
    # Suppress logs from stdout which was turned on by ont_fast5_api
    logging.getLogger('albacore').propagate = False
    logger = ofun(*args, **kwds)
    logger.info('+ SeamlessF5 add-on {} for multi-read fast5 accession. '
                'https://github.com/hyeshik/seamlessf5'.format(__version__))
    return logger

def get_executable_path(name):
    if os.name == 'posix':
        return subprocess.check_output(['which', name]).decode().strip()
    else:
        raise NotImplementedError

def show_banner():
    print("""\
SeamlessF5 {} activated!
""".format(__version__))

def install_hooks():
    input_utils._find_input_files = sl_find_input_files
    read_metadata.ReadMetadata = SLReadMetadata
    shutil.copyfile = sl_copyfile
    log_utils.initialise_logger = sl_initialise_logger

def run_albacore(script_name):
    show_banner()
    install_hooks()

    executable_path = get_executable_path(script_name)
    loader = importlib.machinery.SourceFileLoader('__main__', executable_path)
    exec(loader.load_module())

def read_fast5_basecaller():
    run_albacore('read_fast5_basecaller.py')

def full_1dsq_basecaller():
    run_albacore('full_1dsq_basecaller.py')

def paired_read_basecaller():
    run_albacore('paired_read_basecaller.py')


if __name__ == '__main__':
    read_fast5_basecaller()
