#!/usr/bin/env python3
"""Smoke test para YOLO + YuNet + ArcFace (Camada 1) em vídeo de bancada.

Uso:
    python3 scripts/smoke_test.py --video path/to/video.mp4
    python3 scripts/smoke_test.py --video path/to/video.mp4 --max-frames 300

Saída:
    - Estatísticas de detecção por frame (YOLO pessoas, faces detectadas, matches ArcFace)
    - Arquivo smoke_test_results.json com métricas
    - Código de saída 0 se todos os modelos carregaram e processaram pelo menos 1 frame

Pré-requisitos:
    pip install ultralytics opencv-python insightface onnxruntime
    scripts/download_models.sh  # baixa os modelos
"""

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


def check_dependencies() -> list[str]:
    missing = []
    for pkg in ["ultralytics", "cv2", "insightface", "numpy"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    return missing


def load_yolo(models_dir: Path):  # type: ignore[no-untyped-def]
    from ultralytics import YOLO

    yolo_path = models_dir / "yolo11n.pt"
    if not yolo_path.exists():
        # Ultralytics baixa automaticamente na primeira vez
        print(f"[YOLO] yolo11n.pt não encontrado em {yolo_path}, baixando...")
    model = YOLO(str(yolo_path) if yolo_path.exists() else "yolo11n.pt")
    print(f"[YOLO] Modelo carregado: yolo11n")
    return model


def load_yunet(models_dir: Path):  # type: ignore[no-untyped-def]
    import cv2

    yunet_path = models_dir / "face_detection_yunet_2023mar.onnx"
    if not yunet_path.exists():
        print(f"[YuNet] Modelo não encontrado: {yunet_path}")
        print("        Execute: scripts/download_models.sh")
        sys.exit(1)
    detector = cv2.FaceDetectorYN.create(
        str(yunet_path),
        "",
        (320, 320),
        score_threshold=0.6,
        nms_threshold=0.3,
    )
    print(f"[YuNet] Modelo carregado: {yunet_path.name}")
    return detector


def load_arcface():  # type: ignore[no-untyped-def]
    import insightface

    app = insightface.app.FaceAnalysis(
        name="buffalo_l",
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
    )
    app.prepare(ctx_id=0)  # ctx_id=0 → GPU se disponível, -1 → CPU only
    print("[ArcFace] buffalo_l carregado")
    return app


def run_smoke_test(video_path: Path, max_frames: int) -> dict:  # type: ignore[return]
    import cv2
    import numpy as np

    print(f"\n{'='*60}")
    print(f"Smoke Test SINC — {video_path.name}")
    print(f"{'='*60}\n")

    missing = check_dependencies()
    if missing:
        print(f"[ERRO] Dependências faltando: {', '.join(missing)}")
        print("       pip install ultralytics opencv-python insightface onnxruntime")
        sys.exit(1)

    yolo = load_yolo(MODELS_DIR)
    yunet = load_yunet(MODELS_DIR)
    arcface = load_arcface()

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[ERRO] Não foi possível abrir: {video_path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"Vídeo: {width}x{height} @ {fps:.1f}fps, {total_frames} frames total")
    print(f"Processando até {max_frames} frames...\n")

    stats = {
        "video": str(video_path),
        "resolution": f"{width}x{height}",
        "fps": fps,
        "frames_processed": 0,
        "yolo": {"total_detections": 0, "frames_with_person": 0, "avg_latency_ms": 0.0},
        "yunet": {"total_faces": 0, "frames_with_face": 0, "avg_latency_ms": 0.0},
        "arcface": {"embeddings_generated": 0, "avg_latency_ms": 0.0},
    }

    yolo_times, yunet_times, arcface_times = [], [], []
    frame_idx = 0

    while frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        # ── YOLO: detecção de pessoas ──────────────────────────────────────
        t0 = time.perf_counter()
        results = yolo(frame, classes=[0], verbose=False)  # classe 0 = pessoa
        yolo_ms = (time.perf_counter() - t0) * 1000
        yolo_times.append(yolo_ms)

        persons = results[0].boxes
        n_persons = len(persons) if persons is not None else 0
        stats["yolo"]["total_detections"] += n_persons
        if n_persons > 0:
            stats["yolo"]["frames_with_person"] += 1

        # ── YuNet: detecção facial ─────────────────────────────────────────
        t0 = time.perf_counter()
        yunet.setInputSize((width, height))
        _, faces = yunet.detect(frame)
        yunet_ms = (time.perf_counter() - t0) * 1000
        yunet_times.append(yunet_ms)

        n_faces = len(faces) if faces is not None else 0
        stats["yunet"]["total_faces"] += n_faces
        if n_faces > 0:
            stats["yunet"]["frames_with_face"] += 1

        # ── ArcFace: embedding para cada face detectada ────────────────────
        if n_faces > 0:
            t0 = time.perf_counter()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_objs = arcface.get(rgb)
            arcface_ms = (time.perf_counter() - t0) * 1000
            arcface_times.append(arcface_ms)
            stats["arcface"]["embeddings_generated"] += len(face_objs)

        frame_idx += 1
        if frame_idx % 30 == 0:
            print(
                f"  Frame {frame_idx:4d} | pessoas={n_persons} | faces={n_faces} "
                f"| YOLO={yolo_ms:.1f}ms YuNet={yunet_ms:.1f}ms"
            )

    cap.release()

    stats["frames_processed"] = frame_idx
    stats["yolo"]["avg_latency_ms"] = round(sum(yolo_times) / len(yolo_times), 2) if yolo_times else 0
    stats["yunet"]["avg_latency_ms"] = round(sum(yunet_times) / len(yunet_times), 2) if yunet_times else 0
    stats["arcface"]["avg_latency_ms"] = round(sum(arcface_times) / len(arcface_times), 2) if arcface_times else 0

    print(f"\n{'='*60}")
    print("Resultados:")
    print(f"  Frames processados:          {stats['frames_processed']}")
    print(f"  YOLO  — detecções totais:    {stats['yolo']['total_detections']}  "
          f"| latência média: {stats['yolo']['avg_latency_ms']} ms")
    print(f"  YuNet — faces totais:        {stats['yunet']['total_faces']}  "
          f"| latência média: {stats['yunet']['avg_latency_ms']} ms")
    print(f"  ArcFace — embeddings:        {stats['arcface']['embeddings_generated']}  "
          f"| latência média: {stats['arcface']['avg_latency_ms']} ms")

    # Aviso sobre viabilidade de throughput
    avg_pipeline_ms = stats["yolo"]["avg_latency_ms"] + stats["yunet"]["avg_latency_ms"]
    max_fps = 1000 / avg_pipeline_ms if avg_pipeline_ms > 0 else 0
    print(f"\n  Pipeline estimado (YOLO+YuNet): {avg_pipeline_ms:.1f} ms/frame → {max_fps:.0f} fps máx")
    if max_fps < fps:
        print(f"  [AVISO] Throughput abaixo do FPS do vídeo ({fps:.0f}). "
              f"Considerar pular frames ou usar GPU.")
    print(f"{'='*60}\n")

    out_path = PROJECT_ROOT / "smoke_test_results.json"
    out_path.write_text(json.dumps(stats, indent=2))
    print(f"Resultados salvos em: {out_path}")
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test YOLO + YuNet + ArcFace")
    parser.add_argument("--video", required=True, help="Caminho para o vídeo de bancada (.mp4/.avi)")
    parser.add_argument("--max-frames", type=int, default=300, help="Máximo de frames a processar (padrão: 300)")
    args = parser.parse_args()

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"[ERRO] Vídeo não encontrado: {video_path}")
        sys.exit(1)

    results = run_smoke_test(video_path, args.max_frames)

    # Falha se nenhum frame foi processado
    if results["frames_processed"] == 0:
        print("[ERRO] Nenhum frame processado.")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
