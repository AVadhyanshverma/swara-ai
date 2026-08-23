from memory_engine import MemoryEngine
import time

def generate_story():
    story = """
The colony on Mars, named New Eden, had been established for nearly a century. Dust storms were a daily reality, painting the sky a perpetual, rusty orange. Life in the domes was heavily regulated, oxygen was rationed, and water was recycled through a massive central filtration unit. The colonists were a resilient bunch, mostly scientists, engineers, and their descendants. They spent their days maintaining the fragile ecosystem and their nights gazing back at the pale blue dot they called home.

Captain Elara Vance was the chief engineer of Sector 4. Her job was to ensure the integrity of the atmospheric seals. It was a tedious, high-pressure job. One microscopic fracture could mean disaster for hundreds of people. On a Tuesday evening, while inspecting the outer perimeter, her scanner detected an anomaly in the bedrock beneath the dome. It wasn't a fracture; it was an energy reading. Something buried deep beneath the red sand was emitting a faint, pulsating signal. 

She reported it to the central command, but they dismissed it as sensor ghosting caused by a recent solar flare. But Elara couldn't shake the feeling that it was something more. She enlisted the help of her old friend, Dr. Julian, an archeologist who had grown bored with the barren Martian landscape. Together, they sneaked out an excavation drone and began digging near Sector 4.

For weeks, they found nothing but rock and ice. But on the 23rd day, the drone's drill struck something metallic. It was an artifact, incredibly ancient, entirely smooth, and made of an alloy not found on Earth or Mars. As Julian cleaned off the dust, the artifact began to hum. It projected a holographic map of the galaxy, highlighting a path to a distant star system. 

In the year 2084, humanity discovered the secret to faster-than-light travel by harnessing the power of quantum string vibrations, all thanks to the translation of the data stored within this Martian artifact. The artifact contained blueprints for an engine that manipulated the fabric of space-time.

The discovery changed everything. Mars was no longer a desperate colony; it was the launching pad for humanity's expansion into the cosmos. New Eden became a bustling spaceport. Ships equipped with the new quantum string drives could travel to other solar systems in a matter of days. Elara Vance, once a humble engineer, was given the honor of captaining the first interstellar vessel, the 'Ares Pioneer'. 

As the ship prepared for its maiden voyage, Elara looked out at the rusty landscape one last time. They were leaving the cradle, stepping out into the vast unknown. The engines hummed, space-time warped around them, and in a flash of brilliant blue light, they were gone, leaving the red planet far behind.
"""
    return story.strip()

def run_tests():
    print("========================================")
    print("      INITIALIZING MEMORY ENGINE        ")
    print("========================================")
    engine = MemoryEngine()
    
    print("\n[TEST 1] --- Mini Story Storage & Retrieval ---")
    story_doc = generate_story()
    word_count = len(story_doc.split())
    print(f"--> Generated sci-fi story with {word_count} words.")
    
    start_time = time.time()
    # Storing the document. 
    # We use a smaller chunk size here so the retrieval returns very specific parts of the story.
    doc_id, chunk_ids = engine.add_document(story_doc, doc_metadata={"source": "sci-fi-archive", "type": "story"}, chunk_size=100, overlap=20)
    end_time = time.time()
    
    print(f"--> Successfully processed, chunked, and stored the story in {end_time - start_time:.2f} seconds.")
    print(f"--> Total overlapping chunks created: {len(chunk_ids)}")
    
    print("\n[TEST 2] --- Semantic Retrieval Query ---")
    query = "How did humanity achieve faster-than-light travel?"
    print(f"--> Querying: '{query}'")
    
    search_start = time.time()
    results = engine.search(query, limit=2, filters={"type": "story"})
    search_end = time.time()
    
    print(f"--> Search completed in {search_end - search_start:.4f} seconds.\n")
    print("Top Results:")
    for i, res in enumerate(results):
        print(f"[{i+1}] Score: {res['score']:.4f} | Chunk Index: {res['chunk_index']}")
        print(f"Text snippet:\n{res['text']}")
        print("-" * 70)

if __name__ == "__main__":
    run_tests()
