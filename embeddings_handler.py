# embeddings_handler.py

from sentence_transformers import SentenceTransformer
import torch
from typing import List

class EmbeddingsHandler:
    def __init__(self, model_name: str, device: str = "cpu"):
        """Initialize the embeddings model"""
        self.model_name = model_name
        self.device = device
        self.model = SentenceTransformer(model_name).to(device)
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for given texts"""
        try:
            with torch.no_grad():
                embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            raise Exception(f"Error generating embeddings: {str(e)}")