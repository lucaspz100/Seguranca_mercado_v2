#!/usr/bin/env bash
# Download dos modelos de IA utilizados pelo SINC.
# Execute uma vez após clonar o repositório.
# Os arquivos são salvos em models/ que está no .gitignore.
#
# TODO(KAN): confirmar disponibilidade de GPU e versões finais dos modelos
#            antes de ativar este script em produção.

set -euo pipefail

MODELS_DIR="$(dirname "$0")/../models"
mkdir -p "$MODELS_DIR"

echo "[SINC] download_models.sh — pendente de implementação"
echo "Modelos necessários:"
echo "  - YOLOv11n   (Ultralytics): ultralytics/assets"
echo "  - YuNet       (OpenCV):     opencv_zoo/models/face_detection_yunet"
echo "  - buffalo_l   (InsightFace): insightface model zoo"
echo "  - osnet_x1_0  (Torchreid):  kaiyangzhou/deep-person-reid"
echo "  - RTMPose-m   (MMPose):     open-mmlab/mmpose"
echo ""
echo "Execute após reunião com o Kan para confirmar GPU disponível."
