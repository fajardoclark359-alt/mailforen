import pytest

from mailforen.core.config import settings
from mailforen.core.safety import UnsafeModeRequired, require_unsafe


class TestRequireUnsafe:
    def test_raises_without_unsafe_mode(self, monkeypatch):
        monkeypatch.setattr(settings, "allow_unsafe", False)

        with pytest.raises(UnsafeModeRequired, match="--unsafe"):
            require_unsafe("smtp open-relay probe")

    def test_error_names_the_action(self, monkeypatch):
        monkeypatch.setattr(settings, "allow_unsafe", False)

        with pytest.raises(UnsafeModeRequired, match="smtp open-relay probe"):
            require_unsafe("smtp open-relay probe")

    def test_passes_with_unsafe_mode(self, monkeypatch):
        monkeypatch.setattr(settings, "allow_unsafe", True)

        require_unsafe("smtp open-relay probe")  # must not raise
