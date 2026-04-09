# Local Operations Runbook

## Daily commands

### Bring up the platform
```bash
docker compose up -d
```

### Rebuild FastAPI after code changes
```bash
docker compose up -d --build fastapi
```

### Stop containers without removing them
```bash
docker compose stop
```

### Start stopped containers
```bash
docker compose start
```

### Fully shut down the stack
```bash
docker compose down
```

## Monitoring

### Container status
```bash
docker ps
```

### Resource consumption
```bash
docker stats --no-stream
```

### FastAPI logs
```bash
docker logs -f ai-fastapi
```

## Redis checks

### See cache keys
```bash
docker exec -it ai-redis redis-cli KEYS '*'
```

## Ollama checks on Windows

### List models
```powershell
ollama list
```

### Pull a model
```powershell
ollama pull gemma2:2b
```

### Remove a model
```powershell
ollama rm <model>
```

### Restart Ollama
```powershell
taskkill /IM ollama.exe /F
ollama serve
```

## Connectivity check from Ubuntu to Windows-hosted Ollama

```bash
curl http://<windows-ip>:11434/api/tags
```

## Troubleshooting

### FastAPI uses OpenRouter instead of Ollama
- confirm `OLLAMA_BASE_URL` is set in `.env`
- confirm `OLLAMA_BASE_URL` is passed in `docker-compose.yml`
- test connectivity from within the container

### Cache not being used
- confirm Redis is running
- check Redis keys using `redis-cli`
- confirm the same prompt is being sent twice
