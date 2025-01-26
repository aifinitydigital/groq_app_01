# vector_store.py

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, persist_directory: str, distance_strategy: str = "cosine"):
        """Initialize ChromaDB with persistence"""
        self.persist_directory = persist_directory
        self.distance_strategy = distance_strategy
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Use sentence transformers embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-MiniLM-L12-v2"
        )
    
    def create_or_get_collection(self, collection_name: str) -> chromadb.Collection:
        """Create or get existing collection"""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
        except Exception:
            # Create new collection if it doesn't exist
            collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": self.distance_strategy}
            )
        
        return collection
    
    def add_documents(self, collection_name: str, documents: List[Dict]) -> None:
        """Add documents to collection"""
        collection = self.create_or_get_collection(collection_name)
        
        try:
            # Prepare data for ChromaDB
            docs = []
            metadatas = []
            ids = []
            
            for doc in documents:
                section_num = doc['section_num']
                docs.append(doc['content'])
                metadatas.append({
                    'section_num': section_num,
                    'title': doc['title'],
                    'chapter': doc['chapter']
                })
                # Use section number as ID for easy retrieval
                ids.append(f"section_{section_num}")
            
            # Add documents to collection
            collection.add(
                documents=docs,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Added {len(documents)} documents to collection {collection_name}")
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    def get_section(self, collection_name: str, section_num: str) -> Optional[Dict]:
        """Get specific section by number"""
        collection = self.create_or_get_collection(collection_name)
        
        try:
            results = collection.get(
                ids=[f"section_{section_num}"]
            )
            
            if results['ids']:
                return {
                    'content': results['documents'][0],
                    'metadata': results['metadatas'][0],
                    'score': 1.0  # Direct lookup gets perfect score
                }
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving section {section_num}: {str(e)}")
            return None
    
    def search(self, collection_name: str, query: str, k: int = 3, score_threshold: float = 0.5) -> List[Dict]:
        """Search documents"""
        collection = self.create_or_get_collection(collection_name)
        
        try:
            results = collection.query(
                query_texts=[query],
                n_results=k
            )
            
            # Process and format results
            formatted_results = []
            for idx, doc_id in enumerate(results['ids'][0]):
                score = 1 - results.get('distances', [[0]])[0][idx]  # Convert distance to similarity
                
                if score >= score_threshold:
                    formatted_results.append({
                        'content': results['documents'][0][idx],
                        'metadata': results['metadatas'][0][idx],
                        'score': score
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []