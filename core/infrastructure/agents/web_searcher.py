"""
WebSearcher: Stateful prompt-based LLM search interface.

This module provides a reusable searcher that maintains prompt and client 
configuration for efficient repeated searches with different data.
"""

from typing import Any, Dict, Optional
import logging
from utils.prompts import Prompter
from utils.llm.openai_responses import WebResponses

logger = logging.getLogger(__name__)


class WebSearcher:
    """
    Stateful prompt-based LLM search interface with persistent configuration.
    
    This class encapsulates the common pattern of:
    1. Getting a prompt from the registry
    2. Configuring an LLM client
    3. Formatting templates with data
    4. Making API calls with structured responses
    
    The configuration is stored once during initialization and reused
    across multiple searches for efficiency and consistency.
    
    Example:
        # Initialize once with configuration
        searcher = WebSearcher(
            prompt_alias="socioeconomic_v1",
            client_kwargs={"reasoning": {"effort": "low"}, "max_output_tokens": 5000},
            log_prompts=True
        )
        
        # Use multiple times with different data
        wilson_result = searcher.search({"disease_name": "Wilson", "orphacode": "905"})
        huntington_result = searcher.search({"disease_name": "Huntington", "orphacode": "399"})
    """
    
    def __init__(self, prompt_alias: str, client_kwargs: Optional[Dict[str, Any]] = None, 
                 log_prompts: bool = False):
        """
        Initialize searcher with prompt and client configuration.
        
        Args:
            prompt_alias (str): Registered prompt identifier from the prompt registry
            client_kwargs (dict, optional): Configuration for the WebResponses client
            log_prompts (bool): Whether to log prompts being sent to LLM (default: False)
            
        Raises:
            PromptNotFoundError: If the prompt alias is not found in the registry
            Exception: If client configuration fails
        """
        # Store prompt configuration
        self.prompter = Prompter()
        prompt = self.prompter.get_prompt(prompt_alias)
        self.prompt_template = prompt.template
        self.prompt_model = prompt.model
        self.prompt_alias = prompt_alias  # Store for debugging/logging
        
        # Store logging configuration
        self.log_prompts = log_prompts
        
        # Store and configure client
        self.client = WebResponses()
        if client_kwargs:
            self.client.configure(**client_kwargs)
        
        # Store original client_kwargs for reference
        self.client_kwargs = client_kwargs or {}
        
    def search(self, template_kwargs: Dict[str, Any]) -> Any:
        """
        Execute search using stored configuration and new template data.
        
        This method formats the stored prompt template with the provided
        data and uses the configured client to make the API call.
        
        Args:
            template_kwargs (dict): Data for template formatting (e.g., 
                {"disease_name": "Wilson disease", "orphacode": "905"})
                
        Returns:
            Any: Parsed response object (type depends on prompt's model)
            
        Raises:
            KeyError: If template placeholders are missing from template_kwargs
            Exception: If API call or response parsing fails
        """
        # Format template using original approach (not format_from_object)
        formatted_prompt = self.prompt_template.format(**template_kwargs)
        
        # Log prompt if configured to do so
        if self.log_prompts:
            logger.info(f"=== SENDING PROMPT TO LLM ===")
            logger.info(f"Prompt alias: {self.prompt_alias}")
            logger.info(f"Input data keys: {list(template_kwargs.keys())}")
            logger.info(f"Prompt content:\n{formatted_prompt}")
            logger.info("=== END PROMPT ===")
        
        # Use stored client configuration for API call
        response = self.client.chat(formatted_prompt, text_format=self.prompt_model)
        
        return response
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the searcher's current configuration.
        
        Useful for debugging, logging, and monitoring.
        
        Returns:
            dict: Configuration information including prompt details and client settings
        """
        return {
            "prompt_alias": self.prompt_alias,
            "prompt_template_length": len(self.prompt_template),
            "prompt_model": self.prompt_model.__name__,
            "client_kwargs": self.client_kwargs,
            "has_configured_client": bool(self.client_kwargs)
        }
    
    def refresh_prompt(self) -> None:
        """
        Refresh prompt configuration from the registry.
        
        This method reloads the prompt template and model from the current
        registry state, useful if prompts have been updated.
        
        Note: This addresses the "stale state" concern by allowing manual refresh.
        """
        prompt = self.prompter.get_prompt(self.prompt_alias)
        self.prompt_template = prompt.template
        self.prompt_model = prompt.model
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"WebSearcher(prompt_alias='{self.prompt_alias}', "
                f"template_length={len(self.prompt_template)}, "
                f"configured={bool(self.client_kwargs)})") 