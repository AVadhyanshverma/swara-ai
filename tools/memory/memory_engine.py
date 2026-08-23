from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding
import uuid
import os

class MemoryEngine:
    def __init__(self, collection_name="knowledge_base", path=":memory:", max_memory_mb: int = None, max_cpu_percent: float = None):
        self.client = QdrantClient(path=path)
        self.collection_name = collection_name
        
        # --- DYNAMIC RESOURCE ALLOCATION: CPU ---
        threads = None
        if max_cpu_percent is not None:
            total_cores = os.cpu_count() or 1
            # Calculate allowed threads based on percentage of total cores
            threads = max(1, int(total_cores * max_cpu_percent))
            print(f"MemoryEngine: Dynamic CPU allocation active. Using {threads} thread(s) (approx {max_cpu_percent*100}% of {total_cores} total cores).")
        
        # Initialize the lightweight FastEmbed model (ONNX based)
        self.model_name = "BAAI/bge-small-en-v1.5"
        self.encoder = TextEmbedding(self.model_name, threads=threads)
        self.vector_size = 384 
        
        # --- DYNAMIC RESOURCE ALLOCATION: RAM ---
        # The base ML model and Python environment takes roughly ~250MB.
        # We scale the batch processing size dynamically based on the remaining RAM budget.
        self.default_batch_size = 100
        if max_memory_mb is not None:
            free_mb = max_memory_mb - 250
            if free_mb <= 0:
                self.default_batch_size = 10 # Extreme constraint fallback
            else:
                # Conservative scaling: approx 1.5 chunks per MB of free memory
                self.default_batch_size = max(10, int(free_mb * 1.5))
            print(f"MemoryEngine: Dynamic RAM allocation active. Budget: {max_memory_mb}MB. Optimized batch size: {self.default_batch_size}")
        
        self._ensure_collection()

    def _ensure_collection(self):
        if not self.client.collection_exists(collection_name=self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )

    def _chunk_text(self, text: str, chunk_size: int = 250, overlap: int = 50) -> list[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), max(1, chunk_size - overlap)):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            if i + chunk_size >= len(words):
                break
        return chunks

    def _chunk_file_generator(self, file_path: str, chunk_size: int = 250, overlap: int = 50):
        """
        Generator that reads a file lazily and yields overlapping word chunks.
        Perfect for massive files to avoid running out of RAM (OOM errors).
        """
        buffer_words = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                words = line.split()
                buffer_words.extend(words)
                
                while len(buffer_words) >= chunk_size:
                    chunk = " ".join(buffer_words[:chunk_size])
                    yield chunk
                    buffer_words = buffer_words[max(1, chunk_size - overlap):]
                    
        if buffer_words:
            yield " ".join(buffer_words)

    def _insert_batch(self, batch_chunks: list[str], doc_id: str, doc_metadata: dict, start_index: int):
        batch_embeddings = list(self.encoder.embed(batch_chunks))
        points = []
        ids = []
        for j, (chunk_text, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
            point_id = str(uuid.uuid4())
            ids.append(point_id)
            payload = {
                "text": chunk_text,
                "doc_id": doc_id,
                "chunk_index": start_index + j,
                **doc_metadata
            }
            points.append(PointStruct(id=point_id, vector=embedding.tolist(), payload=payload))
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"MemoryEngine: Inserted batch of {len(points)} chunks.")
        return ids

    def add_document(self, text: str, doc_metadata: dict = None, chunk_size: int = 250, overlap: int = 50, batch_size: int = None):
        if not doc_metadata:
            doc_metadata = {}
        
        # Use dynamic batch size if none is provided
        batch_size = batch_size or self.default_batch_size
            
        doc_id = str(uuid.uuid4())
        chunks = self._chunk_text(text, chunk_size, overlap)
        
        print(f"MemoryEngine: Splitting document into {len(chunks)} chunks... (Processing {batch_size} chunks per batch)")
        
        all_ids = []
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i+batch_size]
            ids = self._insert_batch(batch_chunks, doc_id, doc_metadata, i)
            all_ids.extend(ids)
            
        return doc_id, all_ids

    def add_file(self, file_path: str, doc_metadata: dict = None, chunk_size: int = 250, overlap: int = 50, batch_size: int = None):
        """
        Streams a large file directly from disk to Qdrant without loading it entirely into memory.
        """
        if not doc_metadata:
            doc_metadata = {}
            
        # Use dynamic batch size if none is provided
        batch_size = batch_size or self.default_batch_size
            
        doc_id = str(uuid.uuid4())
        print(f"MemoryEngine: Processing file {file_path} via stream... (Processing {batch_size} chunks per batch)")
        
        all_ids = []
        current_batch = []
        chunk_index = 0
        
        for chunk in self._chunk_file_generator(file_path, chunk_size, overlap):
            current_batch.append(chunk)
            
            if len(current_batch) >= batch_size:
                ids = self._insert_batch(current_batch, doc_id, doc_metadata, chunk_index - len(current_batch) + 1)
                all_ids.extend(ids)
                current_batch = []
                
            chunk_index += 1
            
        if current_batch:
            ids = self._insert_batch(current_batch, doc_id, doc_metadata, chunk_index - len(current_batch))
            all_ids.extend(ids)
            
        print(f"MemoryEngine: Finished processing file. Total chunks inserted: {len(all_ids)}")
        return doc_id, all_ids

    def search(self, query: str, filters: dict = None, limit: int = 5):
        query_vector = list(self.encoder.embed([query]))[0].tolist()
        
        query_filter = None
        if filters:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            must_conditions = []
            for key, val in filters.items():
                must_conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=val))
                )
            query_filter = Filter(must=must_conditions)
            
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit
        )
        
        formatted_results = []
        for hit in search_result.points:
            formatted_results.append({
                "id": hit.id,
                "score": hit.score,
                "text": hit.payload.get("text"),
                "doc_id": hit.payload.get("doc_id"),
                "chunk_index": hit.payload.get("chunk_index"),
                "metadata": {k: v for k, v in hit.payload.items() if k not in ["text", "doc_id", "chunk_index"]}
            })
            
        return formatted_results

    def delete_document(self, doc_id: str):
        """
        Deletes all chunks associated with a specific doc_id.
        Perfect for the 'Rolling Summary' workflow where you replace old summaries.
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
                ]
            )
        )
        print(f"MemoryEngine: Deleted document {doc_id} and all its chunks.")
