from app.services.ingestion import load_file, chunk_documents

from pathlib import Path
from app.rag.vectorstore import add_documents

docs = load_file(path=Path('data/sample_kb/company_employee_handbook.md'))
chunks = chunk_documents(docs)

add_documents(chunks)



