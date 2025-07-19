"""
Research prioritization prompts package.

This package contains all prompt implementations for the Carlos III
research prioritization system.
"""

# This package uses prompt_registry.py for centralized import management.
# Import prompt_registry to initialize all prompts:
#
#   import apps.research_prioritization.prompts.prompt_registry
#
# Then use the prompter:
#
#   from utils.prompts import Prompter
#   prompter = Prompter()
#   prompt = prompter.get_prompt("socioeconomic_v1") 