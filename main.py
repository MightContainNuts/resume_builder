from app.extract_pdf_to_database import CreateRAGData
from app.db_handler import DBHandler
from app.langchain_handler import LangChainHandler


def main():
    """call everything from here"""
    data = CreateRAGData()
    data.main()
    with DBHandler() as db:
        docs = db.retrieve_all_documents_from_db()
        db.store_documents_in_file(docs)
    ai_handler = LangChainHandler()
    response = ai_handler.create_cover_letter()
    print(response.Cover_letter)
    print(response.Improvements)
    with DBHandler() as db:
        db.store_resume_to_file(response.Cover_letter)



if __name__ == "__main__":
    main()
