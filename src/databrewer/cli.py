import functools
import itertools
import os
import shutil
import sys
import tempfile
import zipfile

import click
import click.termui
import requests
import toolz

from tqdm import tqdm

from . import recipes
from .config import get_config, dump_config, DEFAULT_RECIPES_DIR
from .search import SearchIndex
from .utils import abspath, ensure_dir, format_results, download_file


CONTEXT_SETTINGS = {
    'default_map': {
    },
}


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--debug/--no-debug', default=False)
@click.option('--pager/--no-pager', default=False)
@click.option('--quiet/--no-quiet', default=False)
@click.option('--rcfile', metavar='<rcfile>')
@click.option('--root-dir', metavar='<path>')
@click.option('--recipes-dir', metavar='<path>')
@click.option('--datasets-dir', metavar='<path>')
@click.pass_context
def cli(ctx, debug, pager, quiet, rcfile, root_dir, recipes_dir, datasets_dir):
    ctx.obj['use_pager'] = pager
    ctx.obj['quiet'] = quiet
    # TODO: add timeout.
    ctx.obj['requests'] = requests.Session()
    override = {}
    if root_dir:
        override['root_dir'] = abspath(root_dir)
    if datasets_dir:
        override['datasets_dir'] = abspath(datasets_dir)
    if recipes_dir:
        override['recipes_dir'] = abspath(recipes_dir)

    rc = ctx.obj['rc'] = get_config(rcfile, override=override)

    ensure_dir(rc['root_dir'])
    ensure_dir(rc['index_dir'])
    ensure_dir(rc['datasets_dir'])


def requires_index(func):
    @functools.wraps(func)
    def wrapper(obj, *args, **kwargs):
        assert isinstance(obj, dict)
        rc = obj['rc']
        if SearchIndex.is_empty(rc['index_dir']):
            _fail("Index is empty. Run 'databrewer update'")
        return func(obj, *args, **kwargs)
    return wrapper


@cli.command(name='update')
@click.option('--recreate/--no-recreate', default=False)
@click.pass_obj
def cli_update(obj, recreate):
    rc = obj['rc']
    # TODO: Handle the defaults recipes downloading in a better way.
    _download_recipes(DEFAULT_RECIPES_DIR, rc['recipes_default_url'], quiet=obj['quiet'])

    recipes_dir = rc['recipes_dir']
    if recipes_dir:
        index = SearchIndex(rc['index_dir'], force_create=recreate)
        specs = itertools.chain.from_iterable(
            recipes.list(dir) for dir in recipes_dir
        )
        if not obj.get('quiet'):
            specs = tqdm(specs, desc='Indexing', unit=' recipes')
        index.update(specs)
    else:
        _fail("No recipes directories found.")


@cli.command(name='list')
@click.pass_obj
@requires_index
def cli_list(obj):
    index = SearchIndex(obj['rc']['index_dir'])
    results = index.list()
    output = _list_format(results)
    if output:
        _echo(output)
    else:
        _fail("No datasets found.")


@cli.command('search')
@click.argument('query', nargs=-1)
@click.pass_obj
@requires_index
def cli_search(obj, query):
    index = SearchIndex(obj['rc']['index_dir'])
    results = index.search(' '.join(query))
    output = _list_format(results)
    if output:
        _echo(output)
    else:
        _fail("No datasets found.")


def _list_format(specs):
    values = list(toolz.pluck(['name', 'description'], specs))
    if values:
        names, descs = zip(*values)
        return '\n'.join(format_results(_terminal_width(), names, ' - ', descs))


@cli.command(name='info')
@click.argument('name_spec')
@click.option('--check/--no-check', default=False)
@click.pass_obj
@requires_index
def cli_info(obj, name_spec, check):
    datasets_dir = obj['rc']['datasets_dir']
    index = SearchIndex(obj['rc']['index_dir'])
    name = name_spec.partition('[')[0]
    recipe = index.get(name)
    fields = ('name', 'description', 'homepage')
    if recipe:
        term_width = _terminal_width()
        output = []
        titles = [f.title() + ":" for f in fields]
        values = [recipe.get(f, '') for f in fields]
        if recipe.get('keywords'):
            titles.append('Keywords:')
            values.append(', '.join(recipe['keywords']))

        output.extend(format_results(term_width, titles, ' ', values))
        # Files section.
        output.append("\nFiles:")
        rows = []
        for spec in tqdm(recipes.iter_files(recipe), unit=" files", leave=False):
            url_info = spec['url']
            if check:
                if spec.get('restricted'):
                    url_extra = 'restricted'
                else:
                    url_extra = 'unknown'
                if not spec.get('restricted') and spec['url'].startswith('http'):  # no ftp support
                    r = obj['requests'].head(spec['url'], timeout=3)
                    if r.ok:
                        if r.status_code == 200:
                            length = r.headers.get('content-length')
                            if length:
                                url_extra = tqdm.format_sizeof(int(length), 'b')
                            else:
                                url_extra = 'unknown'
                        else:
                            url_extra = 'status:%s' % r.status_code
                    else:
                        url_extra = 'check-failed'
                url_info = "%s [%s]" % (url_info, url_extra)
            rows.append(['  %(name)s' % spec, url_info])
            local_path = os.path.join(datasets_dir, name, spec['filename'])
            if os.path.exists(local_path):
                rows.append(['', local_path])
            # TODO: Add checksum fields.
        file_fields, file_values = zip(*rows)
        output.extend(format_results(0, file_fields, ' - ', file_values))
        _echo("\n".join(output) + "\n")
    else:
        _fail("Recipe not found")


@cli.command(name='download')
@click.argument('name_spec')
@click.option('--output-dir')
@click.option('--force/--no-force', default=False)
@click.pass_obj
@requires_index
def cli_download(obj, name_spec, output_dir, force):
    index = SearchIndex(obj['rc']['index_dir'])
    datasets_dir = obj['rc']['datasets_dir']
    name = name_spec.partition('[')[0]
    if name == name_spec:
        # download all files
        name_spec = '*'
    recipe = index.get(name)
    if recipe:
        if not output_dir:
            output_dir = os.path.join(datasets_dir, recipe['name'])
        files = list(recipes.match_files(recipe, name_spec))
        if files:
            file_names = ['  %s' % spec['name'] for spec in files]
            file_urls = [spec['url'] for spec in files]
            click.echo("Selected Files:")
            click.echo('\n'.join(format_results(0, file_names, ' - ', file_urls)) + '\n')
            if recipe.get('restricted'):
                _fail("Dataset is restricted and cannot be downloaded automatically")

            if force or click.confirm("Confirm to download all the listed files", default=True):
                for spec in files:
                    output_file = os.path.join(output_dir, spec['filename'])
                    if not force and os.path.exists(output_file):
                        click.echo("File '%s' already exists. Skipping." % spec['filename'])
                        continue
                    recipes.download(spec, output_dir, quiet=obj['quiet'])
        else:
            _fail("Specified file not found")
    else:
        _fail("Recipe not found")


@cli.command(name='files')
@click.argument('name_spec')
@click.pass_obj
@requires_index
def cli_files(obj, name_spec):
    index = SearchIndex(obj['rc']['index_dir'])
    name = name_spec.partition('[')[0]
    recipe = index.get(name)
    if not recipe:
        _fail("Recipe '%s' not found" % name)

    datasets_dir = obj['rc']['datasets_dir']
    get_location = toolz.partial(os.path.join, datasets_dir, name)

    files = list(recipes.match_files(recipe, name_spec))
    if files:
        for spec in files:
            click.echo(get_location(spec['filename']))
    else:
        _fail("File '%s' not found" % name_spec)


@cli.group(name='config')
@click.pass_obj
def cli_config(obj):
    pass


@cli_config.command(name='show')
@click.pass_obj
def cli_config_show(obj):
    _echo(dump_config(obj['rc']))


def main(*args, **kwargs):
    kwargs.setdefault('obj', {})
    return cli.main(*args, **kwargs)


def _fail(message, retcode=1):
    click.echo(message, sys.stderr)
    click.get_current_context().find_root().exit(retcode)


def _echo(output, min_lines=10):
    ctx = click.get_current_context()
    if ctx.obj.get('use_pager') and output.count('\n') > min_lines:
        _func = click.echo_via_pager
    else:
        _func = click.echo
    _func(output, sys.stdout)


def _terminal_width():
    width, height = click.termui.get_terminal_size()
    return width


def _download_recipes(recipes_dir, url, quiet=True):
    recipes_dir = abspath(recipes_dir)
    ensure_dir(recipes_dir)
    recipes_zip = tempfile.mktemp()
    download_file(
        url, recipes_zip, quiet=quiet, reporthook_kwargs={
            'desc': "Downloading default recipes",
        },
    )
    try:
        _extract_files(recipes_zip, recipes_dir)
    finally:
        os.unlink(recipes_zip)


def _extract_files(archive_zip, target_dir):
    zf = zipfile.ZipFile(archive_zip)
    for name in zf.namelist():
        basename = os.path.basename(name)
        if not basename:  # directories
            continue
        source = zf.open(name)
        target = open(os.path.join(target_dir, basename), 'wb')
        with source, target:
            shutil.copyfileobj(source, target)
