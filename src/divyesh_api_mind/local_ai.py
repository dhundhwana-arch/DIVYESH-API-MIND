"""Offline hardware inventory and an explicit loopback-only Ollama client.

No models are downloaded or servers started. Runtime requests are made only
when an application calls ``OllamaLocalClient`` methods explicitly.
"""

from __future__ import annotations

import json
import math
import os
import platform
import shutil
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

_MAX_BODY = 2 * 1024 * 1024
_MAX_REQUEST = 1024 * 1024
_DEFAULT_URL = "http://127.0.0.1:11434"


class LocalRuntimeError(RuntimeError):
    """Safe error from an explicitly requested local inference operation."""


def _memory_bytes() -> int | None:
    # Linux /proc is read locally and avoids a mandatory psutil dependency.
    try:
        for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
            if line.startswith("MemTotal:"):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    return int(parts[1]) * 1024
    except (OSError, UnicodeError):
        pass
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        if isinstance(pages, int) and isinstance(page_size, int) and pages > 0 and page_size > 0:
            return pages * page_size
    except (ValueError, OSError, AttributeError):
        pass
    return None


def detect_hardware(*, disk_path: str | Path | None = None) -> dict[str, Any]:
    """Read basic local CPU/RAM/disk metadata; accelerator remains UNKNOWN.

    This is an inventory, not a model compatibility guarantee. It neither
    probes a GPU nor contacts any service.
    """
    memory = _memory_bytes()
    disk = None
    try:
        disk = shutil.disk_usage(Path(disk_path).expanduser() if disk_path else Path.home()).free
    except (OSError, RuntimeError):
        pass
    return {
        "architecture": platform.machine() or "UNKNOWN",
        "operating_system": platform.system() or "UNKNOWN",
        "python_version": platform.python_version(),
        "logical_cpu_cores": os.cpu_count(),
        "system_memory_bytes": memory,
        "system_memory_gib": round(memory / (1024**3), 2) if memory is not None else None,
        "free_disk_bytes": disk,
        "free_disk_gib": round(disk / (1024**3), 2) if disk is not None else None,
        "gpu_or_accelerator": "UNKNOWN (not queried; install vendor-specific tooling and review privacy first)",
        "network_used": False,
        "limitations": [
            "RAM is total system memory, not necessarily available memory.",
            "GPU/accelerator model, VRAM, shared memory, drivers, quantization and context length were not assessed.",
            "Model-fit estimates are rough planning aids, not compatibility or performance guarantees.",
        ],
    }


def estimate_model_memory(model_size_gib: float, *, profile: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Give a conservative rule-of-thumb estimate without claiming fit.

    The estimate budgets 1.3x the advertised model file plus 2 GiB for runtime
    overhead. Real inference needs can be much higher depending on precision,
    context, KV cache, concurrency, runtime and accelerator.
    """
    if (
        isinstance(model_size_gib, bool) or not isinstance(model_size_gib, (int, float))
        or not math.isfinite(model_size_gib) or model_size_gib <= 0
    ):
        raise ValueError("model_size_gib must be a positive number")
    hardware = dict(profile) if profile is not None else detect_hardware()
    total = hardware.get("system_memory_gib")
    required = float(model_size_gib) * 1.3 + 2.0
    if isinstance(total, (int, float)) and not isinstance(total, bool):
        status = "POSSIBLE_BUT_UNVERIFIED" if total >= required else "LIKELY_INSUFFICIENT_BY_RULE_OF_THUMB"
    else:
        status = "UNKNOWN"
    return {
        "model_file_size_gib": float(model_size_gib),
        "rough_ram_budget_gib": round(required, 2),
        "observed_total_ram_gib": total,
        "status": status,
        "confidence": "LOW; not a benchmark or compatibility test",
        "limitations": [
            "Does not account for usable/free RAM, GPU memory, quantization, context/KV cache, OS overhead, runtime, or model-specific constraints.",
            "Never download or launch a model solely based on this estimate; check official hardware guidance and local device capacity.",
        ],
    }


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, newurl):  # type: ignore[no-untyped-def]
        return None


class OllamaLocalClient:
    """Call an already-running Ollama server on loopback only.

    The client does not install Ollama, pull models, start a service, or contact
    hosted providers. Chat is an explicit local request; prompts are sent to
    the user's local process and are never printed or persisted here.
    """

    def __init__(self, base_url: str = _DEFAULT_URL, *, timeout: float = 30.0) -> None:
        if (
            isinstance(timeout, bool) or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout) or timeout <= 0 or timeout > 120
        ):
            raise ValueError("timeout must be greater than 0 and no more than 120 seconds")
        try:
            parsed = urlsplit(base_url)
            port = parsed.port
        except (TypeError, ValueError):
            raise ValueError("Ollama URL must be http://127.0.0.1:11434") from None
        if (
            parsed.scheme != "http"
            or parsed.hostname != "127.0.0.1"
            or port != 11434
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ValueError("Ollama client is restricted to http://127.0.0.1:11434")
        self.base_url = f"http://{parsed.hostname}:11434"
        self.timeout = float(timeout)
        # Local calls must not be forwarded through a configured HTTP proxy.
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())

    def _request(self, path: str, *, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if path not in {"/api/tags", "/api/chat"}:
            raise ValueError("unsupported local Ollama route")
        data = None
        headers = {"Accept": "application/json"}
        method = "GET"
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            if len(data) > _MAX_REQUEST:
                raise ValueError("local Ollama request exceeds the safe size limit")
            headers["Content-Type"] = "application/json"
            method = "POST"
        request = urllib.request.Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            response = self._opener.open(request, timeout=self.timeout)
        except urllib.error.HTTPError as exc:
            raise LocalRuntimeError(f"local Ollama request returned HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            reason = getattr(exc, "reason", None)
            category = type(reason).__name__ if reason is not None else type(exc).__name__
            raise LocalRuntimeError(f"local Ollama is unavailable ({category}); no fallback was attempted") from None
        with response:
            final = urlsplit(response.geturl())
            if final.scheme != "http" or final.hostname != "127.0.0.1" or final.port != 11434:
                raise LocalRuntimeError("local Ollama response left the fixed loopback origin")
            raw = response.read(_MAX_BODY + 1)
        if len(raw) > _MAX_BODY:
            raise LocalRuntimeError("local Ollama response exceeded the safe size limit")
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            raise LocalRuntimeError("local Ollama returned invalid JSON") from None
        if not isinstance(result, dict):
            raise LocalRuntimeError("local Ollama returned an unexpected response shape")
        return result

    def list_models(self) -> list[dict[str, Any]]:
        """List models already installed in the local Ollama runtime."""
        document = self._request("/api/tags")
        models = document.get("models")
        if not isinstance(models, list) or any(not isinstance(item, dict) for item in models):
            raise LocalRuntimeError("local Ollama model-list response is invalid")
        return models

    def chat(self, model: str, messages: Sequence[Mapping[str, str]], *, stream: bool = False) -> dict[str, Any]:
        """Send an explicit prompt to the specified local model; never downloads it."""
        if not isinstance(model, str) or not model.strip() or len(model) > 256:
            raise ValueError("model must be a non-empty local model name")
        if stream is not False:
            raise ValueError("streaming is not supported by this bounded client")
        if not isinstance(messages, Sequence) or isinstance(messages, (str, bytes)) or not messages:
            raise ValueError("messages must contain at least one role/content object")
        clean_messages = []
        for message in messages:
            if not isinstance(message, Mapping):
                raise ValueError("each message must use system, user, or assistant role")
            role = message.get("role")
            if not isinstance(role, str) or role not in {"system", "user", "assistant"}:
                raise ValueError("each message must use system, user, or assistant role")
            content = message.get("content")
            if not isinstance(content, str):
                raise ValueError("message content must be text")
            clean_messages.append({"role": role, "content": content})
        return self._request("/api/chat", payload={"model": model, "messages": clean_messages, "stream": False})
