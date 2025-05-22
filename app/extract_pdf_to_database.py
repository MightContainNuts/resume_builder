import os
from pydantic import BaseModel
from dotenv import load_dotenv
from app.db_handler import DBHandler
from pathlib import Path
import pymupdf

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.langchain_handler import LangChainHandler

from typing import List
from langchain_core.documents import Document

from db.schemas import PDFMetadata




class CreateRAGData:

    def __init__(self):

        self.to_process_path = Path()  / "to_process"
        self.processed_path = Path()  / "processed"
        self.text = None
        self.metadata = None
        self.files = self.list_pdf_files_in_dir()


        self.llm = self.create_model()


    @staticmethod
    def create_model():
        """create llm model"""
        print("Creating LLM model")
        model = "gpt-4o-mini"
        load_dotenv()
        api_key = os.environ.get("OPENAI_API_KEY")
        llm = ChatOpenAI(model=model,
                         temperature=0,
                         max_tokens=1000, )
        return llm


    def list_pdf_files_in_dir(self):
        """
        List all files in the DIR_TO_PROCESS directory.
        """
        print(f"Listing files in {self.to_process_path}")
        files = os.listdir(self.to_process_path)
        files_pdf = [file for file in files  if file.endswith("pdf")]
        print(f"Found {len(files_pdf)} PDF files in {self.to_process_path}")
        return files_pdf


    def extract_text_from_pdf(self, file_name:str)->str:
        """
        Extract text from a PDF file.
        """

        """
                Extract text from a PDF file.
                """

        print(f"Extracting text from {file_name}")
        extracted_text = ""
        doc = pymupdf.open(
            os.path.join(self.to_process_path, file_name))

        for page in doc:
            text = page.get_text().encode("utf8")
            extracted_text += text.decode("utf8")
        print(f"Extracted text from {file_name}")
        return extracted_text


    def clean_and_create_metadata(self,text)->PDFMetadata:
        """
        Tokenize the text into smaller chunks.
        """
        print("Cleaning Text")
        prompt ="""
        Clean up the text and remove any unwanted characters.
        Correct the text to make it more readable. All the certificates and information have all been completed by
        Dean Didion. Correct any incorrectly assigned certificates to the correct person.
        Remove any formatting (empty lines, tabs) to form clean text for storing effectively in a database.
        Create a metadata dictionary with the following keys:
        title: The title of the document.
        content: The content of the document.
        category: The type of the document (certificate, cv, etc)
        size: The size of the document in word count
        Return the cleaned text as a string
        text to clean: {text}"""

        structured_llm = self.llm.with_structured_output(PDFMetadata)
        response = structured_llm.invoke([SystemMessage(content=prompt)])


        print(f"Data parsed")
        print(f"Title: {response.title}")
        print(f"Category: {response.category}")
        print(f"Size: {response.size}")
        print(f"Content: {response.content[:20]}...")
        return response


    @staticmethod
    def split_document(doc:str)->List[Document]:
        """ split the document into smaller chunks.  """
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.create_documents([doc])
        return chunks


    def move_file_to_processed(self, file_name:str)->None:
        """
        Move the processed file to the processed directory.
        """
        os.rename(os.path.join(self.to_process_path, file_name), os.path.join(self.processed_path, file_name))
        print(f"Moved {file_name} from {self.to_process_path} to {self.processed_path}")

    @staticmethod
    def save_to_db(structured_data:PDFMetadata)->None:
        """
        Save the structured data to the database.
        """
        with DBHandler() as db:
            db.add_new_document(structured_data)
            print(f"Saved {structured_data.title} to database")


    def main(self)->None:
        """
        Main function to process the PDF files.
        """
        for file in self.files:
            print("-" * 20)
            print(f"Processing {file}")
            print("-"*20)
            raw_text = self.extract_text_from_pdf(file)
            cleaned_text = self.clean_and_create_metadata(raw_text)
            self.save_to_db(structured_data=cleaned_text)
            #print(f"Metadata: {cleaned_text.title}, {cleaned_text.category}, {cleaned_text.size}")
            #split_docs = self.split_document(cleaned_text.content)
            #lgh = LangChainHandler()
            #lgh.add_to_vector_store_documents(split_docs)
            self.move_file_to_processed(file)
            print(f"Processed {file}")
            print("-" * 20)
            print("\n\n")
        with DBHandler() as db:
            docs = db.retrieve_all_documents_from_db()
            db.store_documents_in_file(docs)
