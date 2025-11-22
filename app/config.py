import json
import os
import base64
import hashlib
from typing import Any, Dict, Optional

DATA_DIR = os.environ.get("DATA_DIR", "/data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
RECORDS_PATH = os.path.join(DATA_DIR, "records.json")


class ConfigManager:
    def __init__(self, secret: Optional[str] = None):
        self.config_path = CONFIG_PATH
        self.records_path = RECORDS_PATH
        self.secret = secret
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(self.config_path):
            self._write_json(self.config_path, {"token_encrypted": None, "settings": {}})
        if not os.path.exists(self.records_path):
            self._write_json(self.records_path, {"records": []})

    def _write_json(self, path: str, data: Dict[str, Any]):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _read_json(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_token(self, token: str):
        payload = token
        if self.secret:
            payload = self._obfuscate(token)
        cfg = self._read_json(self.config_path)
        cfg["token_encrypted"] = payload
        self._write_json(self.config_path, cfg)

    def save_polling_interval(self, interval: int):
        cfg = self._read_json(self.config_path)
        cfg["settings"]["polling_interval"] = interval
        self._write_json(self.config_path, cfg)

    def load_polling_interval(self) -> int:
        cfg = self._read_json(self.config_path)
        return cfg.get("settings", {}).get("polling_interval", 300)

    def load_token(self) -> Optional[str]:
        cfg = self._read_json(self.config_path)
        tok = cfg.get("token_encrypted")
        if not tok:
            return None
        if self.secret:
            try:
                return self._deobfuscate(tok)
            except Exception:
                # If deobfuscation fails, token may have been saved plaintext
                # (e.g. CONFIG_SECRET changed or was not provided when saved).
                # Return raw token as fallback so the app can still use it.
                return tok
        return tok

    def save_records(self, records: Dict[str, Any]):
        self._write_json(self.records_path, records)

    def load_records(self) -> Dict[str, Any]:
        return self._read_json(self.records_path)

    def _derive_key(self) -> bytes:
        # derive a repeating key from secret
        h = hashlib.sha256(self.secret.encode("utf-8")).digest()
        return h

    def _obfuscate(self, text: str) -> str:
        key = self._derive_key()
        data = text.encode("utf-8")
        out = bytearray()
        for i, b in enumerate(data):
            out.append(b ^ key[i % len(key)])
        return base64.b64encode(bytes(out)).decode("utf-8")

    def _deobfuscate(self, blob: str) -> str:
        key = self._derive_key()
        raw = base64.b64decode(blob)
        out = bytearray()
        for i, b in enumerate(raw):
            out.append(b ^ key[i % len(key)])
        return out.decode("utf-8")
