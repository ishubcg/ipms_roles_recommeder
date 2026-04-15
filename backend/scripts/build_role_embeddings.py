import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.recommendation_service import build_role_embeddings  # noqa: E402


if __name__ == "__main__":
    payload = build_role_embeddings()
    print(f"Generated embeddings for {len(payload['roles'])} roles.")