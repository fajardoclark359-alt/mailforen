"""Safety gate for active (target-contacting) checks.

mailforen is passive-first: DNS lookups and queries to third-party OSINT
sources (crt.sh, ipinfo) run freely, but anything that contacts the
*target* directly requires the operator to pass ``--unsafe`` on the
command line. No active checks are implemented yet; this module is the
single hook they must use, so the gate cannot be forgotten per-command.
"""
from .config import settings
from .logger import logger


class UnsafeModeRequired(RuntimeError):
    """Raised when an active check runs without --unsafe."""


def require_unsafe(action: str) -> None:
    """Raise UnsafeModeRequired unless the session was started with --unsafe.

    Active-check code must call this *before* any target contact.
    """
    if not settings.allow_unsafe:
        raise UnsafeModeRequired(
            f"'{action}' is an active check that may contact the target directly. "
            "Re-run with --unsafe to enable it."
        )
    logger.warning(f"UNSAFE MODE: executing active check '{action}'")
