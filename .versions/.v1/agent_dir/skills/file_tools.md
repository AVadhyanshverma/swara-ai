# File Tools Skill

## Tools
- `create_file(filepath: str, content: str)`
- `list_directory(directory: str)`
- `delete_file(filepath: str)`

## Usage Instructions
These tools give the agent a dedicated filesystem workspace to create, list, and delete files. The root of this workspace is restricted to an `agent_workspace` folder inside the project, ensuring safe file operations.

1. **`create_file`**: Creates a new file (and any necessary parent directories). Use relative paths (e.g., `session_123/notes.txt`).
2. **`list_directory`**: Lists the contents of a directory. Pass an empty string `""` to list the root workspace directory.
3. **`delete_file`**: Deletes a file or directory recursively.

**Security:**
- All paths are resolved relative to the agent's safe workspace.
- Path traversal (e.g., `../../`) is blocked.
