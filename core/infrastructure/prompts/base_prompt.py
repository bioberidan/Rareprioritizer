"""
Abstract base class for all prompts in the Carlos III research system.

This module defines the interface that all prompt implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Type, Any
from pydantic import BaseModel


class BasePrompt(ABC):
    """
    Abstract base class for all prompts.
    
    All prompt implementations must inherit from this class and implement
    the required abstract properties and methods.
    """
    
    @property
    @abstractmethod
    def alias(self) -> str:
        """
        Unique identifier for this prompt.
        
        Used for registration and lookup in the prompt registry.
        Should follow the pattern: {domain}_{version} (e.g., "socioeconomic_v1")
        
        Returns:
            str: Unique prompt alias
        """
        pass
    
    @property
    @abstractmethod
    def template(self) -> str:
        """
        Raw prompt template string for LLM input.
        
        This should be the complete prompt text that will be sent to the LLM.
        Can include format placeholders (e.g., {disease_name}, {orphacode})
        that will be filled in by the application.
        
        Returns:
            str: Complete prompt template
        """
        pass
    
    @property
    @abstractmethod
    def model(self) -> Type[BaseModel]:
        """
        Pydantic model for response validation.
        
        This model will be used to validate and parse the LLM response.
        Should be a Pydantic BaseModel class (not instance).
        
        Returns:
            Type[BaseModel]: Pydantic model class for response validation
        """
        pass
    
    def parser(self, response: str) -> Any:
        """
        Parse LLM response before model validation.
        
        Default implementation is passthrough (returns response as-is).
        Override this method for custom parsing logic, such as:
        - Extracting JSON from markdown code blocks
        - Converting XML to JSON
        - Multi-part response parsing
        - Response cleaning/formatting
        
        Args:
            response (str): Raw LLM response
            
        Returns:
            Any: Parsed response (usually str or dict)
        """
        return response
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}(alias='{self.alias}')"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"alias='{self.alias}', "
            f"model={self.model.__name__}, "
            f"template_length={len(self.template)}"
            f")"
        ) 