#!/usr/bin/env python3
import argparse
import os
import sys
import datetime

# Directory to automatically store the generated mindmap copies
OUTPUT_DIR = "generated_maps"

# Standalone HTML template that uses the CDN so it is completely portable
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    /* Reset everything to full viewport */
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{
      width: 100%;
      height: 100%;
      background: #ffff;  /* Your dark theme black */
      overflow: hidden;      /* Prevent scrollbars */
    }}
    /* SVG fills the entire preview area */
    #mindmap {{
      width: 100vw;
      height: 100vh;
      display: block;
    }}
    /* Make markmap background transparent so body color shows through */
    .markmap {{
      background: transparent !important;
    }}
    /* Style the nodes for dark mode */
    .markmap-node-circle {{ fill: #4ade80; }}  /* Green nodes like your logo */
    .markmap-node-text {{ fill: #e5e5e5; }}    /* Light grey text */
    .markmap-link {{ stroke: #333; stroke-width: 1.5; }}
  </style>
</head>
<body>
  <svg id="mindmap"></svg>

  <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
  <script src="https://cdn.jsdelivr.net/npm/markmap-lib@0.18"></script>
  <script src="https://cdn.jsdelivr.net/npm/markmap-view@0.18"></script>
  <script>
    (async () => {{
      const {{ Transformer, Markmap }} = window.markmap;
      const transformer = new Transformer();
      
      // Your markdown content
      const markdown = `{markdown_content}`;
      
      const {{ root }} = transformer.transform(markdown);
      
      // Create markmap with dark theme options
      const mm = Markmap.create('#mindmap', {{
        autoFit: true,           // Auto-scale to fit container
        fitRatio: 0.85,          // Use 85% of available space
        duration: 500,           // Animation duration
        style: (id) => `
          ${{id}} {{ background: transparent; }}
          ${{id}} .markmap-node-text {{ font-family: 'Inter', sans-serif; }}
        `
      }}, root);

      // CRITICAL: Fit the map after a brief delay so DOM settles
      setTimeout(() => mm.fit(), 100);
      
      // Re-fit on window resize
      window.addEventListener('resize', () => mm.fit());
    }})();
  </script>
</body>
</html>
"""

def generate_mindmap(markdown_content, title="Generated Mindmap", filename=None, session_id=None):
    """Generates the HTML file and saves it in the mindmaps directory."""
    import sys
    # Go up two directories to reach the Reverie root where path_manager.py lives
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    try:
        from path_manager import get_mindmaps_dir, ensure_session_paths
        if not session_id:
            session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ensure_session_paths(session_id)
        output_dir = str(get_mindmaps_dir(session_id))
    except ImportError:
        # Fallback if path_manager is not found
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, OUTPUT_DIR)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mindmap_{timestamp}.html"
    
    if not filename.endswith('.html'):
        filename += '.html'
        
    output_path = os.path.join(output_dir, filename)
    
    safe_markdown = markdown_content.strip().replace('\\', '\\\\').replace('`', '\\`')
    html_content = HTML_TEMPLATE.format(
        title=title,
        markdown_content=safe_markdown
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Tool for AI agents to generate standalone HTML mindmaps from Markdown.")
    parser.add_argument("--markdown", "-m", help="Markdown content passed directly as a string", type=str)
    parser.add_argument("--file", "-f", help="Path to a markdown file to read from", type=str)
    parser.add_argument("--title", "-t", help="Title of the mindmap", default="AI Generated Mindmap")
    parser.add_argument("--output", "-o", help="Specific output filename (e.g. 'my_map.html')", default=None)
    parser.add_argument("--session", "-s", help="Session ID to store the map in the correct workspace", default=None)
    
    args = parser.parse_args()
    
    content = ""
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
    elif args.markdown:
        # Allows AI to pass literal \\n if it struggles with multiline bash strings
        content = args.markdown.replace("\\n", "\n")
    elif not sys.stdin.isatty():
        # Easily pipe output from another command or echo
        content = sys.stdin.read()
    else:
        print("Error: Please provide markdown via --markdown, --file, or standard input (pipe).")
        parser.print_help()
        sys.exit(1)
        
    if not content.strip():
        print("Error: No markdown content provided.")
        sys.exit(1)

    saved_path = generate_mindmap(content, title=args.title, filename=args.output, session_id=args.session)
    print(f"Success! Mindmap automatically saved to:")
    print(saved_path)

if __name__ == "__main__":
    main()
