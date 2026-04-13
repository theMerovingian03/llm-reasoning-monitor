from pathlib import Path
import yaml

def load_prompt(filename: str) -> dict:
    """Load a prompt file from the prompts folder.
    
    Args:
        filename: just the filename (e.g., 'monitor_prompts.yaml')
    
    Returns:
        dict: parsed YAML content
    """
    prompts_dir = Path(__file__).parent.parent / 'prompts'
    file_path = prompts_dir / filename
    
    with open(file_path, 'r', encoding='utf-8') as f:
        prompts = yaml.safe_load(f)
    f.close()
    return prompts
    