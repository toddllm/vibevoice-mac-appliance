# 🛠️ Mac VibeVoice Day-2 Operations Runbook

## 🎯 Go/No-Go Checklist (15 seconds)

```bash
make health     # ✅ All systems green
make bench      # RTF ~0.13-0.16x, first_chunk_ms < 2s  
make accept     # ✅ "acceptance: ok"
./vvctl warmup  # ✅ After reboot for fast synthesis
```

## 🚨 Troubleshooting Guide

### **Symptom → Fix**

| Issue | Cause | Solution |
|-------|-------|----------|
| `/synthesize` returns 429 "busy" | Expected backpressure | Client retry with `Retry-After` header |
| First request slow after boot | Cold caches | Run `./vvctl warmup --voice <voice>` |
| No audio / 0 chunks | Golden surface drift | Check `./scripts/accept.sh` output |
| Voice validation fails | Wrong format | Ensure 24kHz mono, ≥0.4s duration |
| Ref drift warning | Snapshot changed | Run `./quick_model_sync.sh` |
| Disk full / partial WAV | Atomic write failed | Clean `.tmp` files, check disk space |
| MPS errors | Conv limitations | Keep 1.5B on CPU/FP32 (policy) |

### **Common Issues**

**🔴 "No audio chunks collected"**
```bash
# Check golden path validation
./scripts/accept.sh

# Verify voice file
./vvctl verify-cache --verbose

# Check control surface
grep "control_hash" logs/vv_server.out | tail -5
```

**🔴 "First chunk timeout"**
```bash
# Warmup after boot
./vvctl warmup --voice VibeVoice/demo/voices/en-Carter_man.wav

# Check CPU threading
echo $OMP_NUM_THREADS  # Should be 8
```

**🔴 "Model snapshot incomplete"**
```bash
# Re-sync from toddllm
./scripts/sync_hf_cache_from_toddllm.sh

# Verify integrity
./vvctl verify-cache --all --verbose
```

## 📊 Performance Baselines

### **Target Metrics (M3 Pro + 128GB)**

| Metric | 1.5B CPU Streaming | 7B MPS Offline |
|--------|-------------------|-----------------|
| Load time | 4-8s (first), <1s (cached) | 6-12s (first) |
| First chunk | 800-1500ms | N/A (offline) |
| RTF | 0.13-0.16x | 0.6-0.9x |
| Chunk count | 18-24 (for 3-6s audio) | 1 (complete) |
| Memory | ~2-4GB CPU | ~8-12GB MPS |

### **QC Thresholds**
- **Audio duration**: ≥90% of target seconds
- **Peak level**: ≤0dBFS, normalized to -1dBFS
- **Sample rate**: Exactly 24kHz
- **Quality**: No NaN/Inf, DC offset <0.01

## 🔧 Maintenance Commands

### **Daily Health**
```bash
# Quick validation
make health

# Performance check
make bench

# Full acceptance
make accept
```

### **Model Management**
```bash
# Verify cache integrity
./vvctl verify-cache --all --save-manifest integrity.json

# Sync from toddllm (if needed)
./scripts/sync_hf_cache_from_toddllm.sh

# Pack for backup
make pack
```

### **Voice Management**
```bash
# Import new voice
./vvctl voice import --input ~/voice.wav --name TestVoice --gender woman

# List voices
ls demo/voices/

# Test voice quality
./vvctl synth --model 1.5B --voice demo/voices/en-TestVoice_woman.wav --text "Voice test" --seconds 3
```

## 🎛️ Configuration Tuning

### **CPU Performance** (M3 Pro)
```bash
# Default (recommended)
export OMP_NUM_THREADS=8
export VECLIB_MAXIMUM_THREADS=8

# Lower thermals (if needed)
export OMP_NUM_THREADS=6
export VECLIB_MAXIMUM_THREADS=6
```

### **Memory Management**
```bash
# Conservative (default)
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0

# Aggressive (for large generations)
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.7
```

## 📈 Monitoring & Metrics

### **Log Analysis**
```bash
# Recent performance
tail -20 ~/Library/Logs/vv_server.out | jq '{rtf, first_chunk_ms, duration}'

# Success rate (last 24h)
grep "$(date +%Y-%m-%d)" ~/Library/Logs/vv_server.out | jq -s 'map(select(.success == true)) | length'

# Performance trends
grep rtf ~/Library/Logs/vv_server.out | jq -r '.rtf' | tail -50 | sort -n
```

### **Health Monitoring**
```bash
# Server endpoint
curl -s http://localhost:5001/health | jq '{status, performance}'

# Metrics endpoint  
curl -s http://localhost:5001/metrics | jq '{success_rate, rtf}'
```

## 🔒 Security & Isolation

### **Network Isolation**
- ✅ Server binds to `127.0.0.1` only
- ✅ `HF_HUB_OFFLINE=1` prevents downloads
- ✅ Read-only access to toddllm
- ✅ No credentials stored

### **File System Safety**
- ✅ Atomic writes prevent partial files
- ✅ Temp file cleanup on errors
- ✅ Output directory isolation
- ✅ Cache integrity validation

## 🎯 Upgrade Paths

### **7B MPS Support** (When Ready)
```bash
# 1. Sync 7B model
SYNC_7B=1 ./scripts/sync_hf_cache_from_toddllm.sh

# 2. Test offline generation
./vvctl synth --model 7B --voice demo/voices/en-Carter_man.wav --text "High quality test" --seconds 6

# 3. Enable in server
# (Simulated streaming already implemented)
```

### **Advanced Features**
- Voice variants and cloning
- Custom model fine-tuning
- Real-time streaming interface
- Web UI with live visualization

## 📋 Acceptance Criteria

**System is healthy when:**
- ✅ `make accept` passes all gates
- ✅ RTF consistently 0.13-0.16x for 1.5B
- ✅ First chunk < 2000ms  
- ✅ Audio QC passes (no NaN/clipping)
- ✅ Cache integrity verified
- ✅ Zero failed synthesis in smoke tests

**Fail conditions:**
- ❌ Any acceptance gate fails
- ❌ RTF > 0.25x consistently
- ❌ First chunk > 3000ms
- ❌ Audio contains NaN/Inf
- ❌ Cache integrity failed
- ❌ Multiple synthesis failures

## 🔄 Recovery Procedures

### **Cache Corruption**
```bash
# 1. Verify damage
./vvctl verify-cache --all --verbose

# 2. Re-sync affected models
./scripts/sync_hf_cache_from_toddllm.sh

# 3. Validate fix
make accept
```

### **Performance Degradation**
```bash
# 1. Check system load
top -l 1 | grep "CPU usage"

# 2. Restart server
pkill -f mac_production_server && python production_server_hardened.py

# 3. Warmup
./vvctl warmup --voice VibeVoice/demo/voices/en-Carter_man.wav

# 4. Benchmark
make bench
```

### **Model Issues**
```bash
# 1. Health check
./vvctl health --json

# 2. Verify snapshots
./vvctl verify-cache --all

# 3. Clean reload
rm -rf ~/.cache/huggingface/hub/models--microsoft--VibeVoice-1.5B
./scripts/sync_hf_cache_from_toddllm.sh
```

---

**🎯 Your Mac VibeVoice port is now enterprise-grade reliable!**

*From idea to production-hardened system in one session.* 🎧✨