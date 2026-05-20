# Troubleshooting: Resources and Ports

Time: 2026-05-20

## Safe local ports

```text
Backend API: 127.0.0.1:8020
Frontend:    127.0.0.1:6210
Riva gRPC:   127.0.0.1:50100
Audio2Face:  127.0.0.1:8040
```

If a port is busy, do not kill the owner process. Ask for a new port and update `.env`/frontend env explicitly.

## Read-only checks

```bash
bash scripts/setup.sh --check-ports
bash scripts/setup.sh --check-resources
bash scripts/setup.sh --check-gpu-light
bash scripts/setup.sh --check-docker-space
bash scripts/setup.sh --dry-run-nvidia-full
```

These commands must not start containers, download assets, prune Docker, kill processes or free ports.

## Hard gates

Heavy NVIDIA work is blocked if any gate fails:

- Free RAM below 10%.
- Memory commit headroom below 10%.
- Disk free below 10%.
- GPU free VRAM below 10%.
- Target port conflict.
- Docker daemon or NVIDIA runtime unavailable.

## Common issues

### Port conflict

Check owner:

```bash
ss -ltnp | grep -E ':(8020|6210|50100|8040)\\b'
```

Resolution: choose a different port with the user. Do not kill the process.

### Memory commit pressure

Check:

```bash
cat /proc/meminfo | grep -E 'MemAvailable|CommitLimit|Committed_AS|SwapFree'
```

If commit headroom is below 10%, do not run GPU/container smoke tests.

### Docker disk pressure

Check:

```bash
docker system df
```

Cleanup policy: only stopped/unused resources after explicit confirmation. Do not remove active containers/images/volumes.

### VS Code port forwarding disconnect

If the browser disconnects but the service is still listening on localhost, reconnect the VS Code forwarded port. Verify with:

```bash
ss -ltnp | grep -E ':(8020|6210)\\b'
```
