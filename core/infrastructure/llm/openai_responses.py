"""
OpenAI Web Responses implementation for handling OpenAI API calls with web search.
"""
import os
os.environ["DEFER_PYDANTIC_BUILD"] = "false"  # do this first!
import json
from typing import Optional, Any, Dict
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

from .base_llm import BaseLLM, BaseResponse


class WebResponses(BaseLLM):
    """
    OpenAI Web Responses class for handling API calls with web search capabilities.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model: str = "o4-mini",
                 **kwargs):
                 # TODO: config: **LLMconfig or dict, llmconfig pass at init
        """
        Initialize the WebResponses instance.
        
        Args:
            api_key: OpenAI API key. If None, will load from environment variable
            model: Model name to use (default: "o4-mini")
            **kwargs: Configuration parameters passed to configure()
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # Load API key from environment variable if not provided
        if api_key is None:
            api_key = os.getenv('OAI_API_KEY')
        
        if not api_key:
            raise ValueError("OAI_API_KEY environment variable is not set and no api_key provided")
        
        super().__init__(api_key, model)
        
        # Initialize client with API key
        self.client = OpenAI(api_key=api_key)
        
        # Initialize default configuration parameters
        # TODO: this should be **LLMconfig or dict, llmconfig pass at init
        self.params = {
            "model": self.model,
            "reasoning": {"effort": "medium"},
            "tools": [{"type": "web_search_preview"}],
            "max_output_tokens": 20000,
            "text_format": None
        }
        
        # Configure with any provided kwargs
        if kwargs:
            self.configure(**kwargs)
    
    def configure(self, **params):
        """
        Update configuration parameters.
        
        Args:
            **params: Configuration parameters to update
        """
        self.params.update(params)
    
    def generate_raw(self, prompt: str, **kwargs) -> Any:
        """
        Generate a response and return the raw response object.
        This is the core method that all other methods build upon.
        
        Args:
            prompt: Input prompt for the model
            **kwargs: Parameters to temporarily override for this call only
            
        Returns:
            Raw response object from OpenAI
        """
        # Build parameters starting with current configuration
        params = self.params.copy()
        params["input"] = prompt
        
        # Temporarily override with kwargs (does not modify self.params)
        params.update(kwargs)
        

        response = self.client.responses.parse(**params)
        return response

    def chat(self, prompt: str, **kwargs) -> str:
        """
        Generate a chat response and return only the output text.
        
        Args:
            prompt: Input prompt for the model
            **kwargs: Additional parameters for the API call
            
        Returns:
            The output text from the model
        """
        raw_response = self.generate_raw(prompt, **kwargs)
        return getattr(raw_response, 'output_parsed', '') or ''
    
    def generate(self, prompt: str, **kwargs) -> BaseResponse:
        """
        Generate a response and return a standardized response object.
        
        Args:
            prompt: Input prompt for the model
            **kwargs: Additional parameters for the API call
            
        Returns:
            Standardized BaseResponse object
        """
        raw_response = self.generate_raw(prompt, **kwargs)
        
        # Extract token usage information
        usage = getattr(raw_response, 'usage', None)
        total_tokens = getattr(usage, 'total_tokens', 0) if usage else 0
        input_tokens = getattr(usage, 'input_tokens', 0) if usage else 0
        output_tokens = getattr(usage, 'output_tokens', 0) if usage else 0
        
        # Extract error information
        error = getattr(raw_response, 'error', None)
        error_str = str(error) if error else None
        
        # Extract output text
        output_text = getattr(raw_response, 'output_parsed', None)
        
        return BaseResponse(
            total_tokens=total_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            error=error_str,
            output=output_text
        ) 