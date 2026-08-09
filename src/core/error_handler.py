import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    BOT_CHECK = 'bot_check'
    AGE_RESTRICTION = 'age'
    UNAVAILABLE = 'unavailable'
    CANCELLED = 'cancelled'
    BROWSER_LOCKED = 'browser_locked'
    UNKNOWN = 'unknown'


def classify_error(error_msg: str) -> ErrorCategory:
    if not error_msg:
        return ErrorCategory.UNKNOWN
    msg = error_msg.lower()

    # CANCELLED (most specific, check first)
    if 'cancelada' in msg or 'cancel' in msg:
        return ErrorCategory.CANCELLED

    # BROWSER_LOCKED (database lock errors)
    if ('locked' in msg and 'database' in msg) or ('sqlite' in msg and 'locked' in msg):
        return ErrorCategory.BROWSER_LOCKED

    # BOT_CHECK (explicit "not a bot" marker — very specific)
    if 'not a bot' in msg:
        return ErrorCategory.BOT_CHECK

    # AGE_RESTRICTION (must include "age" with a context word, or explicit markers)
    if 'age-restricted' in msg or 'age-gate' in msg:
        return ErrorCategory.AGE_RESTRICTION
    if 'age' in msg and ('confirm' in msg or 'verify' in msg):
        return ErrorCategory.AGE_RESTRICTION
    if 'restricted' in msg and 'age' in msg:
        return ErrorCategory.AGE_RESTRICTION

    # Generic "sign in" (without age context) → BOT_CHECK
    if 'sign in' in msg or 'login' in msg:
        return ErrorCategory.BOT_CHECK

    # UNAVAILABLE
    if any(w in msg for w in [
        'private', 'removed', 'deleted', 'copyright', 'blocked',
        'no disponible', 'no est\u00e1 disponible', 'unavailable',
    ]):
        return ErrorCategory.UNAVAILABLE

    return ErrorCategory.UNKNOWN


def user_message_for_category(category: ErrorCategory, original_msg: str = '') -> str:
    messages = {
        ErrorCategory.BOT_CHECK: (
            "YouTube pidi\u00f3 una verificaci\u00f3n adicional para este video. "
            "Puedes reintentar, o si el problema persiste, "
            "iniciar sesi\u00f3n con tu navegador."
        ),
        ErrorCategory.AGE_RESTRICTION: (
            "Este video requiere verificaci\u00f3n de edad. "
            "Puedes intentar iniciar sesi\u00f3n con tu navegador para descargarlo."
        ),
        ErrorCategory.UNAVAILABLE: (
            "Este video no est\u00e1 disponible (puede ser privado, "
            "haber sido eliminado, o no estar disponible en tu pa\u00eds)."
        ),
        ErrorCategory.CANCELLED: "Descarga cancelada",
        ErrorCategory.BROWSER_LOCKED: (
            "No se pudieron leer las cookies del navegador porque "
            "la base de datos est\u00e1 bloqueada. "
            "Cierra el navegador por completo e int\u00e9ntalo de nuevo."
        ),
        ErrorCategory.UNKNOWN: (
            "No se pudo descargar este video. Intenta de nuevo m\u00e1s tarde."
        ),
    }
    return messages.get(category, messages[ErrorCategory.UNKNOWN])


def actions_for_category(category: ErrorCategory) -> list[str]:
    actions = {
        ErrorCategory.BOT_CHECK: ['retry', 'use_browser'],
        ErrorCategory.AGE_RESTRICTION: ['use_browser'],
        ErrorCategory.UNAVAILABLE: [],
        ErrorCategory.CANCELLED: [],
        ErrorCategory.BROWSER_LOCKED: [],
        ErrorCategory.UNKNOWN: ['retry'],
    }
    return actions.get(category, [])
