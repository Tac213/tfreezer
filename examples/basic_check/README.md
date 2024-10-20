# basic_check

Basic project to test if tfreezer works.

Freeze command:

```bash
# cwd: root of tfreezer
python -m tfreezer --variant debug --workpath build/basic_check --entry-module examples/basic_check/basic_check.py
```

Or:

```bash
# cwd: root of tfreezer
python -m tfreezer --variant debug --workpath build/basic_check examples/basic_check/freeze_config.py
```

Note that if you want to freeze the application with a free threading build of python, and you don't want to use the config file, you should run the following command:

```bash
# cwd: root of tfreezer
python -m tfreezer --variant debug --workpath build/basic_check --entry-module examples/basic_check/basic_check.py --excludes _testlimitedcapi,_tkinter
```

You need to exclude `_testlimitedcapi` and `_tkinter` manually, since importing these 2 modules will cause the free threading build of the python process to crash.
