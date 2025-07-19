"""
Prompt Architecture for Carlos III Research Prioritization System

This package provides a modular, extensible prompt architecture that enables:
- Clean separation of concerns
- Easy registration of new prompts
- Consistent handling of LLM interactions
- Type-safe model definitions
"""

from .base_prompt import BasePrompt
from .prompter import Prompter, register_prompt
from .exceptions import (
    PromptError,
    PromptNotFoundError,
    PromptValidationError,
    PromptFormattingError,
    PromptRegistrationError
)

__all__ = [
    "BasePrompt",
    "Prompter", 
    "register_prompt",
    "PromptError",
    "PromptNotFoundError", 
    "PromptValidationError",
    "PromptFormattingError",
    "PromptRegistrationError"
] 