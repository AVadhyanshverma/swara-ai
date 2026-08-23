# Document Tools Skill

## Tools
- `analyze_document(file_path: str, instruction: str)`

## Usage Instructions
The document analysis tool takes a local file path (PDFs, images, videos) and extracts the contents directly into the agent's Vector Database.

1. **For Documents (.pdf, .docx, .txt, etc.):** 
   - The tool uses the Firecrawl API to parse the document natively into clean Markdown.
2. **For Images & Videos (.jpg, .png, .mp4, etc.):** 
   - The tool analyzes the file temporarily and passes it to the `stepfun-ai/step-3.7-flash` vision model (via NVIDIA NIM) to generate a detailed description.

**Arguments:**
- `file_path`: Absolute path to the file you want to analyze.
- `instruction`: (Optional) Custom instructions for the vision model (e.g., "Extract all tables from this image").

*Note: The extracted content is automatically added to the Vector DB via `memory_tools`. Use memory retrieval to query the extracted info.*
