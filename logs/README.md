# Logs

This folder keeps curated project logs, not long-lived runtime noise.

## Keep In Git

- `logs/plans/*.md`: task and release implementation logs.
- `logs/documentation/*.md`: documentation/format task logs.
- `logs/benchmarks/*.md`: benchmark session summaries.
- `logs/README.md`: log policy and maintenance notes.

## Runtime Only

The following files are generated while running the app and can be deleted:

- `logs/*.log`
- `logs/jobs/`
- `logs/runtime/`
- `logs/setup/*.log`
- PID files

Use:

```bash
bash scripts/manage-logs.sh --dry-run
bash scripts/manage-logs.sh --clean
```

`LOG_RETENTION_DAYS` defaults to `14` for age-based review, but `--clean` removes disposable runtime paths immediately.
