# SeamlessF5
SeamlessF5 adds useful missing features for the easier transition to
Oxford Nanopore Technologies'
[new multi-read FAST5 format](https://community.nanoporetech.com/posts/fast5-file-format-change).

## Installation
SeamlessF5 can be installed using [pip](http://pypi.python.org/pypi/pip)
for Python 3.5+.

```bash
pip install seamlessf5
```

## Conversion from single FAST5 files in `tar` to multi-read FAST5
With the `sf5_single_to_multi_fast5` wrapper, ONT's `single_to_multi_fast5`
becomes capable of loading single-read FAST5 files from `tar` or compressed
`tar` files.

```bash
sf5_single_to_multi_fast5 -i fast5.tar.gz -s save_path --recursive
```

## Running albacore for multi-read FAST5
This package also installs wrappers, `sf5_read_fast5_basecaller.py`,
`sf5_full_1dsq_basecaller.py`, and `sf5_paired_read_basecaller.py` which
enable loading multi-read FAST5 files for ONT's albacore. Just add
`sf5_` before your old command lines.

```bash
sf5_read_fast5basecaller.py -i multiread-fast5-dir ...
```
