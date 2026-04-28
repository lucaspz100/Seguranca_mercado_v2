#!/usr/bin/env bash
# Download dos modelos de IA utilizados pelo SINC.
# Execute UMA VEZ após clonar o repositório e antes de rodar smoke_test.py.
# Requer: curl, python3 com pip.
#
# TODO(KAN): confirmar disponibilidade de GPU antes de escolher TensorRT vs ONNX.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS_DIR="$SCRIPT_DIR/../models"
mkdir -p "$MODELS_DIR"

log() { echo "[sinc/download_models] $*"; }

# ── YOLOv11n (Ultralytics) ─────────────────────────────────────────────────
# Detector de pessoa — ~5.4 MB
YOLO_PATH="$MODELS_DIR/yolo11n.pt"
if [ ! -f "$YOLO_PATH" ]; then
    log "Baixando YOLOv11n..."
    python3 -c "from ultralytics import YOLO; YOLO('yolo11n.pt')" 2>&1 | tail -3
    # Ultralytics salva em ~/.cache/ultralytics; copiamos para models/
    YOLO_CACHE=$(python3 -c "
from pathlib import Path
import torch
p = Path.home() / '.cache' / 'ultralytics' / 'assets' / 'yolo11n.pt'
print(p)
")
    [ -f "$YOLO_CACHE" ] && cp "$YOLO_CACHE" "$YOLO_PATH" && log "YOLOv11n → $YOLO_PATH"
else
    log "YOLOv11n já presente: $YOLO_PATH"
fi

# ── YuNet — detecção facial (OpenCV) ──────────────────────────────────────
# ~337 KB
YUNET_PATH="$MODELS_DIR/face_detection_yunet_2023mar.onnx"
if [ ! -f "$YUNET_PATH" ]; then
    log "Baixando YuNet..."
    curl -fsSL -o "$YUNET_PATH" \
        "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
    log "YuNet → $YUNET_PATH"
else
    log "YuNet já presente: $YUNET_PATH"
fi

# ── InsightFace buffalo_l (ArcFace) ───────────────────────────────────────
# ~300 MB; baixado automaticamente pelo InsightFace na primeira execução
BUFFALO_DIR="$HOME/.insightface/models/buffalo_l"
if [ ! -d "$BUFFALO_DIR" ]; then
    log "Baixando buffalo_l (ArcFace) via InsightFace — pode demorar ~5 min..."
    python3 -c "
import insightface
app = insightface.app.FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app.prepare(ctx_id=-1)
print('buffalo_l pronto.')
"
else
    log "buffalo_l já presente: $BUFFALO_DIR"
fi

# ── OSNet x1_0 (Torchreid / Re-ID) ────────────────────────────────────────
# ~2.2 MB
OSNET_PATH="$MODELS_DIR/osnet_x1_0_imagenet.pth"
if [ ! -f "$OSNET_PATH" ]; then
    log "Baixando OSNet x1_0..."
    python3 -c "
import torchreid
torchreid.models.build_model(name='osnet_x1_0', num_classes=1000, pretrained=True)
import torch, pathlib
# Torchreid salva em ~/.cache/torch; copiamos
cache = pathlib.Path.home() / '.cache' / 'torch' / 'hub' / 'checkpoints' / 'osnet_x1_0_imagenet.pth'
if cache.exists():
    import shutil; shutil.copy(cache, '$OSNET_PATH')
    print('OSNet → $OSNET_PATH')
else:
    print('Cache não encontrado em', cache)
"
else
    log "OSNet já presente: $OSNET_PATH"
fi

# ── Resumo ─────────────────────────────────────────────────────────────────
log ""
log "Modelos presentes em $MODELS_DIR:"
ls -lh "$MODELS_DIR" 2>/dev/null || log "(diretório vazio)"
log ""
log "Após download, execute: python3 scripts/smoke_test.py --video <caminho_video.mp4>"
