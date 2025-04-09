from app.extract_pdf_to_database import CreateRAGData
from app.db_handler import DBHandler
from app.langchain_handler import LangChainHandler
from app.langchain_handler import AIResponse


def main():
    """call everything from here"""
    data = CreateRAGData()
    data.main()
    ai_handler = LangChainHandler()
    ai_handler.main()




if __name__ == "__main__":
    main()
