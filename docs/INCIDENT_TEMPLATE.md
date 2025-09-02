# 🚨 Mac VibeVoice Issue Report Template

## 📋 Incident Breadcrumbs (Paste at top of every issue)

### **System Diagnostic**
```bash
./vvctl_final diag --json
```
<details><summary>Diagnostic Output</summary>

```json
[PASTE OUTPUT HERE]
```

</details>

### **Acceptance Test Result**
```bash
make accept
```
<details><summary>Acceptance Test Output</summary>

```
[PASTE OUTPUT HERE]
```

</details>

### **Recent Server Logs**
```bash
tail -50 logs/server.err
```
<details><summary>Error Logs</summary>

```
[PASTE OUTPUT HERE]
```

</details>

### **Cache Integrity Check**
```bash
./vvctl_final verify-cache --all
```
<details><summary>Cache Verification</summary>

```
[PASTE OUTPUT HERE]
```

</details>

---

## 📝 Issue Description

**What were you trying to do?**


**What happened instead?**


**What error message did you see?**


**When did this start happening?**


## 🔬 Reproduction Steps

1. 
2. 
3. 

**Expected result:**


**Actual result:**


## 🎯 Environment Details

**Model used:** 1.5B / 7B

**Command run:**
```bash
[PASTE COMMAND HERE]
```

**Text input:**
```
[PASTE TEXT HERE]
```

**Voice file:** `[path/to/voice.wav]`

## 📊 Performance Context

**Recent benchmark result:**
```bash
make bench
```

**Golden path check:**
```bash
./scripts/check_golden.sh
```

---

## 🛠️ Troubleshooting Attempted

- [ ] Ran `make health`
- [ ] Ran `make accept` 
- [ ] Checked `./vvctl_final diag`
- [ ] Verified voice file format
- [ ] Checked available disk space
- [ ] Restarted after `./vvctl_final warmup`
- [ ] Re-synced models from toddllm

**What did you try?**


**What was the result?**


---

## 🎯 Additional Context

**Anything else that might be relevant:**


**Screenshots or additional files:** [If any]

---

*Generated with Mac VibeVoice diagnostic tools*