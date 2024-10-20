# requests_demo

Example to test if requests is freezable.

Freeze command:

```bash
# cwd: root of tfreezer
python -m tfreezer --variant debug --workpath build/requests_demo --entry-module examples/requests_demo/requests_demo.py --excludes _testlimitedcapi,_tkinter
```

Or:

```bash
# cwd: root of tfreezer
python -m tfreezer --variant debug --workpath build/requests_demo examples/requests_demo/freeze_config.py
```
