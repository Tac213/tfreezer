# Multiprocessing Example

Demo project to test multiprocessing.

Freeze command:

```bash
# cwd: root of tfreezer
python -m tfreezer --variant debug --workpath build/good_multiprocessing --entry-module examples/multiprocessing/good_multiprocessing.py
python -m tfreezer --variant debug --workpath build/bad_multiprocessing --entry-module examples/multiprocessing/bad_multiprocessing.py
```
