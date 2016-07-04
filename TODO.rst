TODO
====

* General features:
  * rc/ini file
  * default directory (target: OSX, Linux)
  * config options:
    * home dir
* Search feature: keyword in name and description
* Info feature: display dataset info
* Fetch feature:
  * down
* Formula feature:
  * A dataset can have one file or multiple nested files.
  * Can provide scripts to convert formats.
  * A github repository
  * Schema
    name: identifier
    description: short text
    homepage: url
    # single file dataset
    url: URL file
    md5: ...
    sha256: ...
    # multiple file dataset
    files:
      - name: identifier
        url: URL
        md5: ...
        sha256: ...
      - name: identifier
        files:
          - ...

* CLI feature
* API feature
* Recipes guidelines:
  * unique identifier as name (dash-separated lowercase ascii words)
  * if data is hosted in a repository (not original source), then it's
    suggested to use a prefix (i.e. mldata-iris)
