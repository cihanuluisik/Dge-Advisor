import logging
import os
from llama_index.core import SimpleDirectoryReader

logger = logging.getLogger(__name__)

class DocumentLoader:
    def load_documents(self, md_dir: str, file_extension: str = '.md'):
        reader = SimpleDirectoryReader(
            input_dir=md_dir, 
            recursive=True,
            file_metadata=lambda filename: {
                'file_name': os.path.basename(filename),
                'file_path': filename,
                'file_type': 'markdown'
            }
        )
        documents = reader.load_data()
        logger.info(f"Loaded {len(documents)} documents")
        return documents