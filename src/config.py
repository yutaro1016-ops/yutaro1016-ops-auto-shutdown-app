from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

APP_NAME = "AutoShutdown"
TASK_NAME = "AutoShutdownScheduler"
VERSION = "1.0.0"


def app_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return app_data_dir() / "config.json"


def log_path() -> Path:
    return app_data_dir() / "app.log"


def setup_logging() -> None:
    logging.basicConfig(
        filename=log_path(),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )


def load_config() -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "last_hour": 23,
        "last_minute": 0,
        "force_close": False,
        "scheduled_for": None,
        "version": VERSION,
    }
    path = config_path()
    if not path.exists():
        return defaults
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            defaults.update(data)
    except (OSError, ValueError, TypeError):
        logging.getLogger(__name__).exception("設定ファイルの読み込みに失敗しました")
    return defaults


def save_config(data: dict[str, Any]) -> None:
    payload = dict(data)
    payload["version"] = VERSION
    config_path().write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
