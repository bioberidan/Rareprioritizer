"""
Base LLM class for handling language model operations.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel


class BaseLLM(ABC):
    """
    Abstract base class for LLM providers.
    """
    
    def __init__(self, api_key: str, model: str = None):
        """
        Initialize the LLM instance.
        
        Args:
            api_key: API key for the LLM provider
            model: Model name to use
        """
        self.api_key = api_key
        self.model = model
        self.client = None
    
    @abstractmethod
    def chat(self, prompt: str, **kwargs) -> str:
        """
        Generate a chat response and return only the output text.
        
        Args:
            prompt: Input prompt for the model
            **kwargs: Additional parameters
            
        Returns:
            The output text from the model
        """
        pass
    
    @abstractmethod
    def generate_raw(self, prompt: str, **kwargs) -> Any:
        """
        Generate a response and return the raw response object.
        
        Args:
            prompt: Input prompt for the model
            **kwargs: Additional parameters
            
        Returns:
            Raw response object from the provider
        """
        pass
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> "BaseResponse":
        """
        Generate a response and return a standardized response object.
        
        Args:
            prompt: Input prompt for the model
            **kwargs: Additional parameters
            
        Returns:
            Standardized response object
        """
        pass


class BaseResponse(BaseModel):
    """
    Base response object to standardize responses across LLM providers.
    """
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    error: Optional[str] = None
    output: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the response object to a dictionary.
        
        Returns:
            Dictionary representation of the response
        """
        return {
            'total_tokens': self.total_tokens,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'error': self.error,
            'output': self.output
        } 