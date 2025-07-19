"""
Custom exceptions for the prompt architecture system.
"""


class PromptError(Exception):
    """Base exception for all prompt-related errors."""
    pass


class PromptNotFoundError(PromptError):
    """Raised when a requested prompt alias is not found in the registry."""
    
    def __init__(self, message: str, available_prompts: list = None):
        super().__init__(message)
        self.available_prompts = available_prompts or []


class PromptValidationError(PromptError):
    """Raised when prompt validation fails."""
    pass


class PromptFormattingError(PromptError):
    """Raised when prompt template formatting fails."""
    pass


class PromptRegistrationError(PromptError):
    """Raised when prompt registration fails."""
    pass 