import os
from super_agent.utils.path_utils import get_project_root


def get_prompt_template(prompt_name: str) -> str:
    prompts_dir = get_project_root() / "super_agent" / "prompts"
    template = open(os.path.join(prompts_dir, f"{prompt_name}.md")).read()
    return template