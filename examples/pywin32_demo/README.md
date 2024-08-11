# pywin32_demo

Example to test if pywin32 is freezable.

Freeze command:

```bash
# cwd: root of tfreezer
python -m tfreezer --variant debug --workpath build/pywin32_demo --entry-module examples/pywin32_demo/pywin32_demo.py
```

Or:

```bash
# cwd: root of tfreezer
python -m tfreezer --variant debug --workpath build/pywin32_demo examples/pywin32_demo/freeze_config.py
```
