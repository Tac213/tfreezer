# mypyc_demo

Basic project for testing freezing modules with mypyc.

Freeze command:

```bash
# cwd: root of tfreezer
python -m tfreezer --variant debug --workpath build/mypyc_demo examples/mypyc_demo/freeze_config.py
```
