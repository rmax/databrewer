==========
DataBrewer
==========

.. image:: https://readthedocs.org/projects/databrewer/badge/?version=latest
        :target: https://readthedocs.org/projects/databrewer/?badge=latest
        :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/databrewer.svg
        :target: https://pypi.python.org/pypi/databrewer

.. image:: https://img.shields.io/travis/rolando/databrewer.svg
        :target: https://travis-ci.org/rolando/databrewer

.. image:: https://codecov.io/github/rolando/databrewer/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/rolando/databrewer

.. image:: https://landscape.io/github/rolando/databrewer/master/landscape.svg?style=flat
    :target: https://landscape.io/github/rolando/databrewer/master
    :alt: Code Quality Status

.. image:: https://requires.io/github/rolando/databrewer/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/rolando/databrewer/requirements/?branch=master

The missing datasets manager.

* Free software: MIT license
* Documentation: https://databrewer.readthedocs.org.

.. image:: http://i.imgur.com/FBsIV7g.gif
    :alt: DataBrewer preview


Databrewer let you search and discover datasets. Inspired by Homebrew, it
creates and index of known datasets that you can download with a single
command. It will provide an API to allow to do the same in, for example, a
IPython notebook so you no longer have to manually download datasets.


Quickstart
----------

Install ``databrewer``::

  pip install databrewer

Update the recipes index::

  databrewer update

Search for some keywords::

  databrewer search nyc taxi

Example output::

  andresmh-nyc-taxi-trips - NYC Taxi Trips. Data obtained through a FOIA request
  nyc-tlc-taxi            - This dataset includes trip records from all trips
                            completed in yellow and green taxis in NYC in 2014 and
                                                      select months of 2015.

Let's check the ``nyc-tlc-taxi`` dataset::

  databrewer info nyc-tlc-taxi


We can either download the entire dataset (which is huge!)::

  databrewer download nyc-tlc-taxi

Or just a few files in the dataset, or select a subset::

  databrewer download "nyc-tlc-taxi[green][2014-*]"

.. note::

  Note that ``*`` is the standard glob operator and ``[green]`` acts as selector.
  The selectors depends on how the recipe if defined. When using selectors you
  must enclose the name in quotes in most shells.

Finally you need to know where the files are located for further processing::

  databrewer download "nyc-tlc-taxi[green][2014-*]"

Example output::

  /Users/rolando/.databrewer/datasets/nyc-tlc-taxi/green_tripdata_2014-01.csv
  /Users/rolando/.databrewer/datasets/nyc-tlc-taxi/green_tripdata_2014-02.csv
  /Users/rolando/.databrewer/datasets/nyc-tlc-taxi/green_tripdata_2014-03.csv
  /Users/rolando/.databrewer/datasets/nyc-tlc-taxi/green_tripdata_2014-04.csv
  /Users/rolando/.databrewer/datasets/nyc-tlc-taxi/green_tripdata_2014-05.csv
  /Users/rolando/.databrewer/datasets/nyc-tlc-taxi/green_tripdata_2014-06.csv
  /Users/rolando/.databrewer/datasets/nyc-tlc-taxi/green_tripdata_2014-07.csv
  /Users/rolando/.databrewer/datasets/nyc-tlc-taxi/green_tripdata_2014-08.csv
  /Users/rolando/.databrewer/datasets/nyc-tlc-taxi/green_tripdata_2014-09.csv
  /Users/rolando/.databrewer/datasets/nyc-tlc-taxi/green_tripdata_2014-10.csv
  /Users/rolando/.databrewer/datasets/nyc-tlc-taxi/green_tripdata_2014-11.csv
  /Users/rolando/.databrewer/datasets/nyc-tlc-taxi/green_tripdata_2014-12.csv

Datasets
--------

The aim is to index known and not-so-known datasets. There is no plans to
standarize the dataset format as we want to keep it as published by the
authors.

Recipes
~~~~~~~

Datasets are defined in recipes which contains information about the dataset
and where to find it.

These recipes are community maintained and hosted in the `databrewer-recipes`_
repository.

Roadmap
-------

* Include an API. For now it only provides a CLI-interface but in the near
  future it will include an API so you can search, download and load datasets
  directly in your Python code.

Contributing
------------

You can help by the following means:

* Spread the word!
* `Request missing features <https://github.com/rolando/databrewer/issues/new?title=Feature%20Request:>`_
* `Report usability issues or bugs <https://github.com/rolando/databrewer/issues/new>`_
* `Request missing datasets <https://github.com/rolando/databrewer-recipes/issues/new?title=Dataset%20Request:&body=URL:>`_

See `CONTRIBUTING.rst <https://github.com/rolando/databrewer/blob/master/CONTRIBUTING.rst>`_ for more information.


.. _`databrewer-recipes`: https://github.com/rolando/databrewer-recipes/blob/master/README.rst
