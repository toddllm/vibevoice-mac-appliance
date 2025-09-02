#!/usr/bin/env bash
set -euo pipefail

# Clean HF Cache Sync from toddllm
# Preserves HF cache structure and enables offline model loading

CACHE_ROOT="${HF_HOME:-$HOME/.cache/huggingface}/hub"
mkdir -p "$CACHE_ROOT"

echo "=== VibeVoice Model Cache Sync ==="
echo "Target cache: $CACHE_ROOT"
echo ""

# Check what's available on toddllm
echo "Checking available models on toddllm..."
ssh tdeshane@toddllm "ls -la ~/.cache/huggingface/hub | grep -E 'models--(microsoft--VibeVoice|WestZhang--VibeVoice)' || true"
echo ""

# Sync 1.5B model (primary)
echo "Syncing VibeVoice-1.5B..."
rsync -av --links -H --partial --progress \
  tdeshane@toddllm:~/.cache/huggingface/hub/models--microsoft--VibeVoice-1.5B/ \
  "$CACHE_ROOT/models--microsoft--VibeVoice-1.5B/"

echo ""

# Sync 7B model (optional, larger)
echo "Syncing VibeVoice-7B-Preview..."
rsync -av --links -H --partial --progress \
  tdeshane@toddllm:~/.cache/huggingface/hub/models--WestZhang--VibeVoice-Large-pt/ \
  "$CACHE_ROOT/models--WestZhang--VibeVoice-Large-pt/"

echo ""

# Verify sync
echo "=== Verification ==="
echo "Local VibeVoice models:"
ls -la "$CACHE_ROOT" | grep -E 'VibeVoice' || echo "No VibeVoice models found"

echo ""
echo "1.5B model structure:"
find "$CACHE_ROOT/models--microsoft--VibeVoice-1.5B" -maxdepth 2 -type d -name "snapshots" 2>/dev/null || echo "1.5B not found"

echo ""
echo "7B model structure:"
find "$CACHE_ROOT/models--WestZhang--VibeVoice-Large-pt" -maxdepth 2 -type d -name "snapshots" 2>/dev/null || echo "7B not found"

echo ""
echo "✅ Sync completed! Models ready for offline use."
echo "💡 Set HF_HUB_OFFLINE=1 to force offline-only loading."