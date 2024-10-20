# Multiprocessing Example

Demo project to test multiprocessing.

Freeze command:

```bash
# cwd: root of tfreezer
python -m tfreezer --variant debug --workpath build/multiprocessing_pool --entry-module examples/multiprocessing/multiprocessing_pool.py --excludes _testlimitedcapi,_tkinter
python -m tfreezer --variant debug --workpath build/multiprocessing_simple --entry-module examples/multiprocessing/multiprocessing_simple.py --excludes _testlimitedcapi,_tkinter
python -m tfreezer --variant debug --workpath build/multimodule_multiprocessing examples/multiprocessing/multimodule_freeze_config.py
```
