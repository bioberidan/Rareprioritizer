"""
Central prompt registry for research prioritization system.

⭐ SINGLE IMPORT POINT ⭐

Import this module to automatically register all available prompts.
Registration happens through import side effects via @register_prompt decorators.

Usage:
    # Import this module to initialize all prompts
    import prompts.prompt_registry
    
    # Then use the prompter
    from utils.prompts import Prompter
    prompter = Prompter()
    
    # Access any registered prompt
    prompt = prompter.get_prompt("socioeconomic_v1")
    
Available prompts after import:
- socioeconomic_v1: Original socioeconomic impact analysis
- socioeconomic_v2: Enhanced socioeconomic impact analysis  
- groups_v1: Original CIBERER groups analysis
- groups_v2: Enhanced CIBERER groups analysis
"""

# Import all prompt modules to trigger @register_prompt decorators
# This registers all prompts in the global PROMPT_REGISTRY

# Socioeconomic impact analysis prompts
from .socioeconomic.prompts import *

# CIBERER research groups analysis prompts  
from .groups.prompts import *

# Future prompt modules can be added here:
# from .prevalence.prompts import *
# from .therapeutic.prompts import *
# from .genetic.prompts import *

# Note: Registration happens automatically during import.
# No explicit code needed - the decorators handle everything. 