import os
import glob
from langchain_core.tools import tool

SKILLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills"))

@tool
def list_skills() -> str:
    """Lists all available skills documented in the skills directory."""
    if not os.path.exists(SKILLS_DIR):
        return "No skills directory found."
    
    md_files = glob.glob(os.path.join(SKILLS_DIR, "*.md"))
    if not md_files:
        return "No skills found."
        
    skills = [os.path.splitext(os.path.basename(f))[0] for f in md_files]
    return "Available skills:\n- " + "\n- ".join(skills)

@tool
def read_skill(skill_name: str) -> str:
    """Reads the detailed documentation and usage instructions for a specific skill by name."""
    skill_path = os.path.join(SKILLS_DIR, f"{skill_name}.md")
    if not os.path.exists(skill_path):
        return f"Error: Skill '{skill_name}' not found. Use list_skills() to see available skills."
        
    with open(skill_path, "r", encoding="utf-8") as f:
        return f.read()
