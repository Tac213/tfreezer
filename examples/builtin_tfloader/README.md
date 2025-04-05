# basic_check

Test builtin tfloader.

Freeze command:

```bash
# cwd: root of tfreezer
python -m tfreezer --variant debug --workpath build/builtin_tfloader --entry-module examples/builtin_tfloader/builtin_tfloader.py --builtin-tfloader
```

Or:

```bash
# cwd: root of tfreezer
python -m tfreezer --variant debug --workpath build/builtin_tfloader --builtin-tfloader examples/builtin_tfloader/freeze_config.py
```

Note that if you want to freeze the application with a free threading build of python, and you don't want to use the config file, you should run the following command:

```bash
# cwd: root of tfreezer
python -m tfreezer --variant debug --workpath build/builtin_tfloader --entry-module examples/builtin_tfloader/builtin_tfloader.py --builtin-tfloader --excludes _testlimitedcapi,_tkinter
```

You need to exclude `_testlimitedcapi` and `_tkinter` manually, since importing these 2 modules will cause the free threading build of the python process to crash.
