"""Guards for Claude API usage.

Incident: email generation called `claude-3-5-sonnet-20241022`, which was retired on
2025-10-28, so every API call failed and users silently got template emails.
These tests check the model setting, the request shape against the real installed SDK,
and that every failure mode (refusal, truncation) still falls back to templates.
"""
import importlib
import importlib.metadata
import inspect
import json
import pathlib
import re
import subprocess
import sys
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RETIRED = re.compile(r"claude-(instant|2|3)[.\-\w]*")
ANY_MODEL_ID = re.compile(r"""["']claude-(opus|sonnet|haiku|fable|mythos|instant|2|3)[\w.\-]*["']""")
SDK_FLOOR = (0, 125, 0)  # first version known to accept `fallbacks` on beta.messages


def _tracked_py_files():
    out = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    return [ROOT / p for p in out]


def _version_tuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


# ── Model setting ─────────────────────────────────────────────────────────────

def test_no_retired_model_ids_in_source():
    hits = []
    for path in _tracked_py_files():
        for n, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if RETIRED.search(line):
                hits.append(f"{path.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not hits, "Retired Claude model IDs found:\n" + "\n".join(hits)


def test_app_code_reads_model_from_config():
    """App code must use config.CLAUDE_MODEL, not a hardcoded model ID."""
    allowed = {"config.py"}
    hits = []
    for path in _tracked_py_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in allowed or rel.startswith(("tests/", ".github/")):
            continue
        for n, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if ANY_MODEL_ID.search(line):
                hits.append(f"{rel}:{n}: {line.strip()}")
    assert not hits, "Hardcoded Claude model IDs (use config.CLAUDE_MODEL):\n" + "\n".join(hits)


def test_default_model_is_current(monkeypatch):
    import config

    monkeypatch.delenv("CLAUDE_MODEL", raising=False)
    try:
        importlib.reload(config)
        assert config.CLAUDE_MODEL == "claude-sonnet-5-5"
    finally:
        monkeypatch.undo()
        importlib.reload(config)


def test_max_tokens_leaves_room_for_thinking():
    import config

    # Thinking counts toward max_tokens on Sonnet 5.5; 1000 (the old value) is too tight.
    assert config.CLAUDE_MAX_TOKENS >= 2000


def test_installed_sdk_meets_floor_and_requirements_pin_it():
    assert _version_tuple(importlib.metadata.version("anthropic")) >= SDK_FLOOR
    req = (ROOT / "requirements.txt").read_text()
    m = re.search(r"^anthropic>=([\d.]+)", req, re.M)
    assert m and _version_tuple(m.group(1)) >= SDK_FLOOR, "requirements.txt anthropic floor too low"


# ── SDK call site (email_generator) ───────────────────────────────────────────

def _resp(stop_reason="end_turn", text="Hi Ada, ...", thinking_first=True):
    content = []
    if thinking_first:
        content.append(types.SimpleNamespace(type="thinking", thinking=""))
    if text is not None:
        content.append(types.SimpleNamespace(type="text", text=text))
    return types.SimpleNamespace(content=content, stop_reason=stop_reason)


class _StrictBetaMessages:
    """Fake that validates kwargs against the real installed SDK method."""

    def __init__(self, response):
        from anthropic.resources.beta.messages import Messages

        self._sig = inspect.signature(Messages.create)
        self._response = response
        self.calls = []

    def create(self, **kwargs):
        self._sig.bind(None, **kwargs)  # TypeError on any kwarg the real SDK rejects
        self.calls.append(kwargs)
        return self._response


class _NonBetaMessages:
    def create(self, **kwargs):
        raise AssertionError("must call client.beta.messages.create (fallbacks need the beta endpoint)")


def _install_fake(monkeypatch, response):
    import anthropic

    beta = _StrictBetaMessages(response)
    client = types.SimpleNamespace(beta=types.SimpleNamespace(messages=beta), messages=_NonBetaMessages())
    monkeypatch.setattr(anthropic, "Anthropic", lambda **kw: client)
    return beta


def test_email_generator_request_shape_and_text_after_thinking(monkeypatch):
    import config
    from email_generator import EmailGenerator

    beta = _install_fake(monkeypatch, _resp())
    assert EmailGenerator(api_key="test")._call_claude_api("prompt") == "Hi Ada, ..."
    call = beta.calls[0]
    assert call["model"] == config.CLAUDE_MODEL
    assert call["max_tokens"] == config.CLAUDE_MAX_TOKENS
    assert config.CLAUDE_FALLBACK_BETA in call["betas"]
    assert call["fallbacks"] == "default"
    assert call["output_config"] == {"effort": config.CLAUDE_EFFORT}
    assert not {"temperature", "top_p", "top_k"} & call.keys()


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_email_generator_refusal_or_truncation_falls_back(monkeypatch, stop_reason):
    from email_generator import EmailGenerator

    # A text block is present, so only the stop_reason branch can return None here.
    _install_fake(monkeypatch, _resp(stop_reason=stop_reason, text="partial or declined text"))
    assert EmailGenerator(api_key="test")._call_claude_api("prompt") is None


# ── Raw HTTP call site (simple_http_client) ───────────────────────────────────

def _run_curl_client(monkeypatch, response_json):
    import simple_http_client

    seen = {}

    def fake_check_output(cmd):
        seen["cmd"] = cmd
        with open(cmd[cmd.index("-d") + 1].lstrip("@")) as f:
            seen["body"] = json.load(f)
        return json.dumps(response_json).encode()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(simple_http_client.subprocess, "check_output", fake_check_output)
    return simple_http_client.call_claude_api_via_curl("prompt"), seen


def test_curl_client_request_shape_and_text_after_thinking(monkeypatch):
    import config

    out, seen = _run_curl_client(monkeypatch, {
        "stop_reason": "end_turn",
        "content": [{"type": "thinking", "thinking": ""}, {"type": "text", "text": "Hello"}],
    })
    assert out == "Hello"
    body, cmd = seen["body"], seen["cmd"]
    assert body["model"] == config.CLAUDE_MODEL
    assert body["max_tokens"] == config.CLAUDE_MAX_TOKENS
    assert body["fallbacks"] == "default"
    assert body["output_config"] == {"effort": config.CLAUDE_EFFORT}
    assert not {"temperature", "top_p", "top_k"} & body.keys()
    assert "anthropic-beta: " + config.CLAUDE_FALLBACK_BETA in cmd


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_curl_client_refusal_or_truncation_falls_back(monkeypatch, stop_reason):
    out, _ = _run_curl_client(monkeypatch, {
        "stop_reason": stop_reason,
        "content": [{"type": "text", "text": "partial or declined text"}],
    })
    assert out is None
