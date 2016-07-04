from __future__ import division

import contextlib
import os.path
import pdb
import sys
import textwrap
import traceback

import requests
import toolz
import tqdm
import yaml

from six.moves.urllib.request import urlretrieve as _urlretrieve


abspath = toolz.compose(os.path.abspath, os.path.expanduser)


def load_yaml(filename):
    # TODO: Add basic validation.
    with open(filename) as fp:
        return yaml.load(fp)


def dump_yaml(obj):
    return yaml.dump(obj)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def format_results(terminal_width, key_list, separator, text_list,
                   left_align=True, min_factor=3, **kwargs):
    """Returns formatted results in two columns.
    """
    key_width = max(map(len, key_list))
    separator_length = len(separator)
    desc_wrap = toolz.identity
    if terminal_width:
        if key_width / terminal_width > .5:
            key_width = terminal_width // 2 - 3
        text_width = terminal_width - key_width - separator_length
        if text_width * min_factor > terminal_width:
            desc_wrap = toolz.compose(
                ('\n' + ' ' * (key_width + separator_length)).join,
                toolz.partial(textwrap.wrap, width=text_width, **kwargs),
            )

    if left_align:
        fmt = '%-*s%s%s'
    else:
        fmt = '%*s%s%s'

    for key, text in zip(key_list, text_list):
        text = desc_wrap(text)
        if len(key) > key_width:
            yield fmt % (key_width, key, separator, '')
            yield fmt % (key_width, '', ' ' * separator_length, text)
        else:
            yield fmt % (key_width, key, separator, text)


def download_file(url, filename, quiet=True, reporthook_kwargs=None):
    """Downloads a file with optional progress report."""
    if '://' not in url:
        raise ValueError("fully qualified URL required: %s" % url)
    if url.partition('://')[0] not in ('https', 'http', 'ftp'):
        raise ValueError("unsupported URL schema: %s" % url)

    if url.startswith('ftp://'):
        retrieve = _urlretrieve
    else:
        retrieve = _urlretrieve_requests

    if quiet:
        return retrieve(url, filename)

    reporthook_kwargs = reporthook_kwargs or {}
    if filename:
        reporthook_kwargs.setdefault('desc', filename)

    reporthook_kwargs.setdefault('unit', 'b')
    reporthook_kwargs.setdefault('unit_scale', True)

    reporthook = _ReportHook(**reporthook_kwargs)
    retrieve = _urlretrieve if url.startswith('ftp://') else _urlretrieve_requests
    with contextlib.closing(reporthook):
        retrieve(url, filename, reporthook)


def _urlretrieve_requests(url, filename, reporthook=None):
    resp = requests.get(url, stream=True)
    fp = open(filename, 'wb')
    with contextlib.closing(resp), fp:
        chunk_num = 0
        chunk_size = 64 * 1024
        total = int(resp.headers.get('content-length', -1))
        if reporthook:
            reporthook(chunk_num, chunk_size, total)
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:  # skip keep alive chunks
                fp.write(chunk)
                chunk_num += 1
                if reporthook:
                    reporthook(chunk_num, chunk_size, total)


class _ReportHook(object):
    """A reporthook shim for tqdm."""

    def __init__(self, **params):
        self.params = params
        self.pb = None

    def __call__(self, block_number, block_size, total_size):
        if self.pb is None:  # First call.
            self.pb = tqdm.tqdm(**dict(self.params, total=total_size))
        if block_number > 0:
            self.pb.update(block_size)

    def close(self):
        if self.pb is not None:
            self.pb.close()
            self.pb = None


@contextlib.contextmanager
def debugger():
    try:
        yield
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        info = sys.exc_info()
        traceback.print_exception(*info)
        pdb.post_mortem(info[2])
