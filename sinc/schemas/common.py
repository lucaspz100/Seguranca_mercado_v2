from enum import Enum


class Role(str, Enum):
    OPERATOR = "OPERATOR"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


class CameraLayer(str, Enum):
    ENTRANCE = "ENTRANCE"  # Camada 1: filtro facial ArcFace
    SALON = "SALON"  # Camada 2: análise comportamental RTMPose


class AlertType(str, Enum):
    FACIAL_MATCH = "FACIAL_MATCH"  # Camada 1: match contra watchlist
    BEHAVIOR = "BEHAVIOR"  # Camada 2: pose suspeita / ocultação
    TRACKING = "TRACKING"  # Camada 3: Re-ID dirigido (OSNet)


class AlertStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class TrackingConfidence(str, Enum):
    # ADR-004: status explícito exibido ao operador — nunca esconder degradação
    HIGH = "HIGH"  # 0–30 s desde última detecção
    MEDIUM = "MEDIUM"  # 30 s – 3 min
    LOW = "LOW"  # 3 – 10 min
    LOST = "LOST"  # > 10 min
