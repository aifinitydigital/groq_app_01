# create_vectordb.py
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import logging
from config_loader import load_config
from text_processor import TextProcessor
from vector_store import VectorStore
from embeddings_handler import EmbeddingsHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vectordb_creation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_vector_database(config_path: str = "config.yaml", pdf_path: str = "./Input/a2023-45.pdf"):
    """Create and populate the vector database"""
    try:
        # Load configuration
        config = load_config(config_path)
        logger.info("Configuration loaded successfully")

        # Initialize components
        text_processor = TextProcessor(
            chunk_size=config['chunking']['chunk_size'],
            chunk_overlap=config['chunking']['chunk_overlap']
        )
        
        vector_store = VectorStore(
            persist_directory=config['vector_db']['persist_directory'],
            distance_strategy=config['vector_db']['distance_strategy']
        )
        
        # Read and process document
        logger.info(f"Reading PDF file: {pdf_path}")
        text = text_processor.read_pdf(pdf_path)
        
        # Process into sections
        logger.info("Processing text into sections")
        sections = text_processor.process_text(text)
        
        # Add to vector store
        logger.info("Adding sections to vector store")
        vector_store.add_documents("bns_sections", sections)
        
        logger.info("Vector database created successfully")
        print(f"Created vector database with {len(sections)} sections")
        print(f"Database location: {config['vector_db']['persist_directory']}")
        
    except Exception as e:
        logger.error(f"Error creating vector database: {str(e)}")
        raise

if __name__ == "__main__":
    print("Creating BNS Vector Database...")
    create_vector_database()
    print("Done!")