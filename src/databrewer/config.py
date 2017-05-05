import logging
import os

import six
import jsonschema

from .utils import abspath, load_yaml, dump_yaml


logger = logging.getLogger(__name__)


CONFIG_SCHEMA = {
    '$schema': 'http://json-schema.org/draft-04/schema',
    'type': 'object',
    'properties': {
        'root_dir': {'type': 'string'},
        'datasets_dir': {'type': 'string'},
        'recipes_dir': {
            'oneOf': [
                {'type': 'string'},
                {'type': 'array', 'items': {'type': 'string'}},
            ],
        },
    },
}

CONFIG_DEFAULTS = {
    'root_dir': '~/.databrewer',
    'datasets_dir': '~/.databrewer/datasets',
    'recipes_dir': '~/.databrewer/recipes',
    'recipes_default_url': 'https://github.com/rolando/databrewer-recipes/archive/master.zip',
}

DEFAULT_RECIPES_DIR = abspath(CONFIG_DEFAULTS['recipes_dir'])
DEFAULT_USERRC = '~/.databrewerrc'

_missing = object()


class Config(dict):

    env_prefix = 'DATABREWER_'

    def __getitem__(self, key):
        val = os.getenv(self.env_prefix + key.upper(), _missing)
        if val is not _missing:
            return val
        return super(Config, self).__getitem__(key)


def load_rc(default_rc_path,
            defaults=None,
            envname='DATABREWERRC',
            schema=CONFIG_SCHEMA):
    """Returns runtime configuration."""
    envfile = os.getenv(envname)
    if envfile:
        if os.path.exists(envfile):
            default_rc_path = envfile
        else:
            logger.error("Could not find '%s', using defaults", envfile)

    meta = (defaults or {}).copy()
    if os.path.exists(default_rc_path):
        meta.update(load_yaml(default_rc_path) or {})

    jsonschema.validate(meta, schema)

    return meta


def get_config(path=None, override=None, defaults=CONFIG_DEFAULTS):
    """Returns config object."""
    if path is None:
        path = DEFAULT_USERRC
    values = override or {}
    for key, val in defaults.items():
        values.setdefault(key, val)
    cfg = Config(load_rc(abspath(path), defaults=values))
    cfg['root_dir'] = abspath(cfg['root_dir'])
    cfg['index_dir'] = os.path.join(cfg['root_dir'], 'index')
    cfg['datasets_dir'] = abspath(cfg['datasets_dir'])
    # Ensure recipes dir is a list.
    if isinstance(cfg['recipes_dir'], six.string_types):
        cfg['recipes_dir'] = [cfg['recipes_dir']]
    cfg['recipes_dir'] = [abspath(dir) for dir in cfg['recipes_dir']]
    return cfg


def dump_config(cfg):
    return dump_yaml(dict(cfg))
