"""CI baseline smoke test: every core src module must import without error.

Excludes modules that depend on optional integration extras (README:
"OpenAI, xu ly audio va Twilio la cac nhom tich hop tuy chon, khong bat
buoc doi voi luong HTTP cot loi") since the CI baseline only installs the
`dev` extra, not `llm-openai`/`audio`/`telephony-twilio`.
"""

from __future__ import annotations

import importlib
import pkgutil

import pytest

import src

_OPTIONAL_MODULES = {
    "src.telephony.providers.twilio",
    "src.telephony.providers.stringee",
    "src.services.stt_service",
    "src.services.tts_service",
    "src.services.llm_service",
}


def _core_module_names() -> list[str]:
    return sorted(
        module_info.name
        for module_info in pkgutil.walk_packages(src.__path__, prefix="src.")
        if module_info.name not in _OPTIONAL_MODULES
    )


@pytest.mark.smoke
@pytest.mark.parametrize("module_name", _core_module_names())
def test_core_module_imports(module_name: str) -> None:
    importlib.import_module(module_name)
