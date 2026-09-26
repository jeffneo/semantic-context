"""Settings: the method's defaults (defaults.yaml) merged with one estate's config file.

The estate's file says where to read (the warehouse connector and its settings), how to name
things, where the graph lives, and which designed models to align. Paths in it are relative to
the file. Secrets never live in either YAML: they come from the environment or a .env file.

The config file is found from --config, else QLSC_CONFIG (environment or .env).
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

DEFAULTS = Path(__file__).with_name("defaults.yaml")
PROMPTS = Path(__file__).resolve().parents[2] / "prompts"


class ConfigError(RuntimeError):
    pass


def _dotenv(start: Path) -> dict[str, str]:
    """The nearest .env at or above `start`."""
    for d in (start, *start.parents):
        f = d / ".env"
        if f.is_file():
            out = {}
            for line in f.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    out[k.strip()] = v.strip()
            return out
    return {}


def secret(name: str, default: str | None = None) -> str:
    """A secret or setting from the environment, else the nearest .env file."""
    value = os.environ.get(name) or _dotenv(Path.cwd()).get(name, default)
    if value is None:
        raise ConfigError(f"{name} is not set (environment or .env)")
    return value


def _merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


class Settings(dict):
    """The merged config, as a dict, plus the paths and groups the stages use."""

    def __init__(self, path: Path):
        self.path = path.resolve()
        self.root = self.path.parent
        super().__init__(
            _merge(yaml.safe_load(DEFAULTS.read_text()), yaml.safe_load(self.path.read_text()) or {})
        )

    def resolve(self, relative: str) -> Path:
        return self.root / relative

    @property
    def work(self) -> Path:
        """Where every stage writes: extracts, parse records, reports, the LLM and embedding caches."""
        p = self.resolve(self.get("work_dir", "work"))
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def params(self) -> dict:
        return self["parameters"]

    @property
    def business(self) -> dict[str, str]:
        """How the prompts refer to the organization: {business}'s warehouse, the {kind}'s queries."""
        return {"business": self["business"]["name"], "kind": self["business"]["kind"]}


def load(path: str | Path | None = None) -> Settings:
    path = path or secret("QLSC_CONFIG", "") or None
    if not path:
        raise ConfigError("no config file: pass --config or set QLSC_CONFIG")
    p = Path(path)
    if not p.is_file():
        raise ConfigError(f"config file not found: {p}")
    return Settings(p)
