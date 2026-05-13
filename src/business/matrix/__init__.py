"""matrix 模块 - 多账号人设隔离"""
from src.business.matrix.persona_isolator import (
    PersonaIsolator,
    PersonaType,
    PersonaConfig,
    AccountProfile,
    AccountIsolationResult,
    get_persona_isolator
)

__all__ = [
    "PersonaIsolator",
    "PersonaType",
    "PersonaConfig",
    "AccountProfile",
    "AccountIsolationResult",
    "get_persona_isolator"
]