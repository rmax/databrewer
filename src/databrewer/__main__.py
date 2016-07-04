import sys

import toolz

from .cli import main
from .utils import debugger


if __name__ == "__main__":
    _main = toolz.partial(main, prog_name='python -m databrewer')
    if '--pdb' in sys.argv:
        sys.argv.remove('--pdb')
        with debugger():
            _main()
    else:
        _main()
