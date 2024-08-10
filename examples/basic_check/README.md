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
