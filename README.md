# cronaudit

> Parses and visualizes cron schedules to detect conflicts and overlapping jobs.

---

## Installation

```bash
pip install cronaudit
```

Or install from source:

```bash
git clone https://github.com/youruser/cronaudit.git && cd cronaudit && pip install .
```

---

## Usage

Point `cronaudit` at a crontab file and let it do the rest:

```bash
cronaudit --file /etc/crontab
```

**Example output:**

```
Loaded 12 jobs from /etc/crontab

[WARNING] Overlap detected:
  backup.sh      (*/15 * * * *)
  sync_data.sh   (0,15,30,45 * * * *)
  → Both scheduled to run at 00:15, 00:30, 00:45 ...

[OK] No conflicts found for remaining 10 jobs.
```

You can also pass a raw cron expression to inspect a single schedule:

```bash
cronaudit --expr "*/5 * * * *" --visualize
```

### Options

| Flag            | Description                              |
|-----------------|------------------------------------------|
| `--file`        | Path to a crontab file                   |
| `--expr`        | Single cron expression to analyze        |
| `--visualize`   | Print an ASCII timeline of the schedule  |
| `--hours`       | Lookahead window in hours (default: 24)  |
| `--json`        | Output results as JSON                   |

---

## License

This project is licensed under the [MIT License](LICENSE).