# Troubleshooting: Resources and Ports

Time: 2026-05-22

## Safe local ports

```text
Backend API: 127.0.0.1:8020
Frontend:    127.0.0.1:6310
Riva gRPC:   127.0.0.1:50051
Audio2Face gRPC: 127.0.0.1:8040
Audio2Face HTTP: 127.0.0.1:8041
```

If a port is busy, do not kill the owner process. Ask for a new port and update `.env`/frontend env explicitly.

## Read-only checks

```bash
bash scripts/setup.sh --check-ports
bash scripts/setup.sh --check-resources
bash scripts/setup.sh --check-gpu-light
bash scripts/setup.sh --check-docker-space
bash scripts/setup.sh --dry-run-nvidia-full
bash scripts/setup.sh --list-containers
```

These commands must not start containers, download assets, prune Docker, kill processes or free ports.

To stop only containers created for this project:

```bash
bash scripts/setup.sh --stop-containers
```

This command filters by `com.facespeed.project=NVIDIARiva-Audio2Face-facespeed` and does not touch unrelated containers.

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
ss -ltnp | grep -E ':(8020|6310|50051|8040|8041)\\b'
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

### Project container status

Check project containers:

```bash
docker ps -a --filter label=com.facespeed.project=NVIDIARiva-Audio2Face-facespeed
```

The Services page can show container metadata through `/api/services`. Set `SERVICE_MANAGER_MODE=docker` only when the backend should start, stop or restart the project-labeled Riva/A2F containers.

### VS Code port forwarding disconnect

If the browser disconnects but the service is still listening on localhost, reconnect the VS Code forwarded port. Verify with:

```bash
ss -ltnp | grep -E ':(8020|6310)\\b'
```
