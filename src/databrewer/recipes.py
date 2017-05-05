import glob
import os
import re
import shutil

import jsonschema

from fnmatch import fnmatchcase
from urllib.parse import urlparse, unquote

from .utils import load_yaml, download_file, ensure_dir


def url_filename(url):
    path = urlparse(url).path
    return os.path.basename(unquote(path))


def match_files(recipe, pattern):
    # Escape glob's meta chars.
    pattern = re.sub(r'([\[\]])', r'[\1]', pattern)
    # Translate range patterns.
    pattern = re.sub(r'(\{.+?\})', r'[\1]', pattern)
    for spec in iter_files(recipe):
        if fnmatchcase(spec['name'], pattern):
            yield spec


def iter_files(spec, parent=None):
    name = spec['name']
    if parent:
        name = '%s[%s]' % (parent, name)
    url = spec.get('url')
    if url:
        yield make_file_spec(**dict(spec, name=name))
    else:
        for obj in spec.get('files', []):
            for out in iter_files(obj, parent=name):
                yield out


def list(root):
    """Returns list of datasets found in given root directory."""
    pattern = os.path.join(root, "*.yaml")
    for filename in glob.glob(pattern):
        recipe = load_meta(filename)
        recipe['_file'] = filename
        yield recipe


def load_meta(filename, schema=None):
    meta = load_yaml(filename)
    if schema:
        jsonschema.validate(meta, schema)
    return meta


def make_file_spec(name, url, **kwargs):
    spec = kwargs
    spec.update({
        'name': name,
        'url': url,
    })
    if not spec.get('filename'):
        spec['filename'] = url_filename(url)
    if not spec.get('filename'):
        raise ValueError("Could not find filename for '%s'" % url)

    return spec


def download(file_spec, dest_dir, quiet=False):
    ensure_dir(dest_dir)
    dest_filename = os.path.join(dest_dir, file_spec['filename'])
    part_filename = dest_filename + '.part'
    # TODO: verify checksum.
    download_file(file_spec['url'], part_filename, quiet=quiet,
                  reporthook_kwargs={
                      'desc': "%(name)s - %(filename)s" % file_spec,
                  })
    shutil.move(part_filename, dest_filename)
