"""
Prompt registry and management system.

This module provides the global prompt registry and the Prompter class
for accessing and managing registered prompts.
"""

import logging
from typing import Dict, List, Type, Any
from .base_prompt import BasePrompt
from .exceptions import PromptNotFoundError, PromptRegistrationError


# Global prompt registry - single source of truth
PROMPT_REGISTRY: Dict[str, BasePrompt] = {}

# Set up logging
logger = logging.getLogger(__name__)


def register_prompt(cls: Type[BasePrompt]) -> Type[BasePrompt]:
    """
    Decorator for automatic prompt registration.
    
    Registers a prompt class in the global registry by instantiating it
    and storing the instance under its alias.
    
    Args:
        cls: Prompt class that inherits from BasePrompt
        
    Returns:
        Type[BasePrompt]: The original class (unchanged)
        
    Raises:
        PromptRegistrationError: If prompt registration fails
    """
    try:
        # Instantiate the prompt class
        instance = cls()
        
        # Get the alias from the instance
        alias = instance.alias
        
        # Validate the alias
        if not alias or not isinstance(alias, str):
            raise PromptRegistrationError(
                f"Invalid alias '{alias}' for prompt class {cls.__name__}. "
                "Alias must be a non-empty string."
            )
        
        # Store in global registry (last wins for duplicates)
        PROMPT_REGISTRY[alias] = instance
        
        logger.debug(f"Registered prompt: {alias} -> {cls.__name__}")
        
        return cls
        
    except Exception as e:
        raise PromptRegistrationError(
            f"Failed to register prompt class {cls.__name__}: {e}"
        ) from e


class Prompter:
    """
    Prompt management and access interface.
    
    Provides methods to retrieve prompts from the global registry,
    list available prompts, and get system inventory information.
    """
    
    def get_prompt(self, alias: str) -> BasePrompt:
        """
        Get a prompt by its alias.
        
        Args:
            alias (str): Unique prompt identifier
            
        Returns:
            BasePrompt: The prompt instance
            
        Raises:
            PromptNotFoundError: If the prompt alias is not found
        """
        if alias in PROMPT_REGISTRY:
            return PROMPT_REGISTRY[alias]
        else:
            available = list(PROMPT_REGISTRY.keys())
            logger.warning(
                f"Prompt '{alias}' not found. Available prompts: {available}"
            )
            raise PromptNotFoundError(
                f"Prompt '{alias}' not found",
                available_prompts=available
            )
    
    def format_from_object(self, template: str, obj: Any) -> str:
        """
        Format a template string using data extracted from any object.
        
        This is a simple formatting method that handles various object types
        by converting them to dictionaries and using Python's built-in
        string formatting.
        
        Args:
            template (str): Template string with {field} placeholders
            obj (Any): Object to extract data from (dict, Pydantic model, etc.)
            
        Returns:
            str: Formatted template string
            
        Raises:
            KeyError: If template placeholder not found in object data
            
        Example:
            prompter = Prompter()
            formatted = prompter.format_from_object(
                "Disease: {disease_name} (ORPHA:{orphacode})",
                {"disease_name": "Wilson disease", "orphacode": "905"}
            )
        """
        data = self._extract_dict_from_object(obj)
        return template.format(**data)
    
    def _extract_dict_from_object(self, obj: Any) -> Dict[str, Any]:
        """
        Extract dictionary representation from any object.
        
        Handles various object types and converts them to dictionaries
        suitable for template formatting.
        
        Args:
            obj (Any): Object to extract data from
            
        Returns:
            Dict[str, Any]: Dictionary representation of the object
        """
        if isinstance(obj, dict):
            return obj
        elif hasattr(obj, 'model_dump'):
            # Pydantic v2
            return obj.model_dump()
        elif hasattr(obj, 'dict'):
            # Pydantic v1
            return obj.dict()
        else:
            # Generic object - extract non-private attributes
            result = {}
            for attr_name in dir(obj):
                if not attr_name.startswith('_'):
                    try:
                        value = getattr(obj, attr_name)
                        if not callable(value):
                            result[attr_name] = value
                    except:
                        continue
            return result
    
    def list_prompts(self) -> List[str]:
        """
        Get list of all available prompt aliases.
        
        Returns:
            List[str]: List of registered prompt aliases
        """
        return list(PROMPT_REGISTRY.keys())
    
    def get_inventory(self) -> Dict[str, Any]:
        """
        Get detailed inventory of all registered prompts.
        
        Useful for debugging, monitoring, and system introspection.
        
        Returns:
            Dict[str, Any]: Comprehensive prompt inventory
        """
        return {
            "total_prompts": len(PROMPT_REGISTRY),
            "available_prompts": self.list_prompts(),
            "prompt_details": {
                alias: {
                    "class_name": prompt.__class__.__name__,
                    "template_length": len(prompt.template),
                    "model_name": prompt.model.__name__,
                    "has_custom_parser": (
                        prompt.__class__.parser != BasePrompt.parser
                    )
                }
                for alias, prompt in PROMPT_REGISTRY.items()
            },
            "registry_stats": {
                "memory_usage_kb": self._estimate_memory_usage(),
                "domains": self._get_domain_stats(),
                "versions": self._get_version_stats()
            }
        }
    
    def has_prompt(self, alias: str) -> bool:
        """
        Check if a prompt exists in the registry.
        
        Args:
            alias (str): Prompt alias to check
            
        Returns:
            bool: True if prompt exists, False otherwise
        """
        return alias in PROMPT_REGISTRY
    
    def get_prompts_by_domain(self, domain: str) -> Dict[str, BasePrompt]:
        """
        Get all prompts for a specific domain.
        
        Args:
            domain (str): Domain name (e.g., "socioeconomic")
            
        Returns:
            Dict[str, BasePrompt]: Dict of alias -> prompt for the domain
        """
        return {
            alias: prompt
            for alias, prompt in PROMPT_REGISTRY.items()
            if alias.startswith(domain)
        }
    
    def clear_registry(self) -> None:
        """
        Clear all prompts from the registry.
        
        WARNING: This is primarily for testing. Use with caution.
        """
        global PROMPT_REGISTRY
        PROMPT_REGISTRY.clear()
        logger.warning("Prompt registry cleared")
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage of the registry in KB."""
        import sys
        total_size = 0
        for prompt in PROMPT_REGISTRY.values():
            total_size += sys.getsizeof(prompt.template)
            total_size += sys.getsizeof(prompt.alias)
            total_size += sys.getsizeof(prompt)
        return round(total_size / 1024, 2)
    
    def _get_domain_stats(self) -> Dict[str, int]:
        """Get count of prompts by domain."""
        domains = {}
        for alias in PROMPT_REGISTRY.keys():
            domain = alias.split('_')[0] if '_' in alias else 'unknown'
            domains[domain] = domains.get(domain, 0) + 1
        return domains
    
    def _get_version_stats(self) -> Dict[str, List[str]]:
        """Get version information for each domain."""
        versions = {}
        for alias in PROMPT_REGISTRY.keys():
            if '_' in alias:
                domain, version = alias.split('_', 1)
                if domain not in versions:
                    versions[domain] = []
                versions[domain].append(version)
        return versions 