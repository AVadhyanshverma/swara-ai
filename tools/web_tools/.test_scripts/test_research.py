import json
from firecrawl_tools import search_the_net, read_the_page

def run_research():
    print("Starting research on Ransomware Evolution (2025/2026), MITRE ATT&CK, and Mitigation...")
    
    research_results = {}
    
    # 1. Search for recent ransomware evolution and RaaS
    print("Searching for ransomware evolution...")
    search_1 = search_the_net.invoke({
        "query": "Ransomware evolution 2025 2026 RaaS models WannaCry",
        "limit": 3
    })
    research_results["search_evolution"] = search_1
    
    # 2. Search for ransomware MITRE ATT&CK tactics
    print("Searching for MITRE ATT&CK tactics...")
    search_2 = search_the_net.invoke({
        "query": "Ransomware MITRE ATT&CK framework tactics 2025",
        "limit": 2
    })
    research_results["search_mitre"] = search_2
    
    # 3. Search for ransomware mitigation strategies
    print("Searching for mitigation strategies...")
    search_3 = search_the_net.invoke({
        "query": "Ransomware mitigation strategy playbooks 2025",
        "limit": 2
    })
    research_results["search_mitigation"] = search_3
    
    # Read one of the pages (let's pick a generic reliable site if it appears, otherwise just use the search results as they contain descriptions/markdown usually from firecrawl)
    # Actually firecrawl search returns markdown of the results directly in `data` -> `markdown`
    # Let's write everything to a file
    with open("research_data.json", "w") as f:
        json.dump(research_results, f, indent=2)
    
    print("Research data saved to research_data.json")

if __name__ == "__main__":
    run_research()
