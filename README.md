# montagu-db-docs

**[Rendered documenentation](https://vimc.github.io/montagu-db-docs)** - the 
latest version is always available [here](https://vimc.github.io/montagu-db-docs/latest)

Automatically generated documentation for 
[`montagu-db`](https://github.com/vimc/montagu-db) to keep the repository size 
under control and to allow us to easily see multiple versions at once.

This uses the `docker` package which can be installed with

```shell
pip3 install --user -r requirements.txt
```

Generate documentation like

```shell
./generate.py 1343a52
```

This will generate the docs, update the index.html file (and the latest symlink)
and create a commit.  You will still have to push the changes upstream.
