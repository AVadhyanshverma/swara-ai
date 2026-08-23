import json
from firecrawl_tools import read_the_page

def extract_tartan_info():
    print("Extracting Tartan info using Firecrawl's LLM extraction feature...")
    
    schema = {
        "type": "object",
        "properties": {
            "definition": {
                "type": "string",
                "description": "A concise definition of what Tartan is."
            },
            "origin": {
                "type": "string",
                "description": "Where and when did Tartan originate?"
            },
            "cultural_significance": {
                "type": "string",
                "description": "Why is Tartan culturally significant, especially to Scotland?"
            }
        },
        "required": ["definition", "origin", "cultural_significance"]
    }
    
    result = read_the_page.invoke({
        "url": "https://en.wikipedia.org/wiki/Tartan",
        "only_main_content": True,
        "extraction_schema": schema,
        "extraction_prompt": "Extract a clear definition, the historical origins, and cultural significance of Tartan."
    })
    
    with open("tartan_extracted.json", "w") as f:
        json.dump(result, f, indent=2)
        
    print("Extraction complete. Saved to tartan_extracted.json")

if __name__ == "__main__":
    extract_tartan_info()
