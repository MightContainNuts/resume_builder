import os
import pymupdf
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from app.services.chatbot import LangChainHandler
from app.db.db_init import DBHandler


class PDFMetadata(BaseModel):
    title: str
    content: str
    category: str
    size: int


class CreateRAGData:

    def __init__(self):

        self.to_process_path = "app/services/to_process"
        self.processed_path = "app/services/processed"
        self.text = None
        self.metadata = None
        self.files = self.list_pdf_files_in_dir()
        load_dotenv()
        api_key = os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(
            api_key=os.environ.get(api_key),
        )
        self.lc_handler = LangChainHandler()


    def list_pdf_files_in_dir(self):
        """
        List all files in the DIR_TO_PROCESS directory.
        """
        files = os.listdir(self.to_process_path)
        files_pdf = [file for file in files  if file.endswith("pdf")]
        return files_pdf

    def extract_text_from_pdf(self, file_name:str)->str:
        """
        Extract text from a PDF file.
        """
        print(f"Extracting text from {file_name}")
        extracted_text = ""
        doc = pymupdf.open(os.path.join(self.to_process_path, file_name))

        for page in doc:
            text = page.get_text().encode("utf8")
            extracted_text += text.decode("utf8")
        print(f"Extracted text from {file_name}")
        return extracted_text


    def clean_and_create_metadata(self,text):
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
        Return the cleaned text as a string"""

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system","content": prompt},
                {"role": "user",  "content": text},
                           ],
            response_format=PDFMetadata,
            )
        print(f"Data parsed")
        print(f"Title: {response.choices[0].message.parsed.title}")
        print(f"Category: {response.choices[0].message.parsed.category}")
        print(f"Size: {response.choices[0].message.parsed.size}")
        print(f"Content: {response.choices[0].message.parsed.content[:20]}...")
        return response.choices[0].message.parsed

    def save_metadata_to_db(self, metadata:PDFMetadata)->None:
        """
        Save the metadata to the database.
        """
        print(f"Saving metadata to database")
        with DBHandler() as db:
            db.add_new_document(
                structured_data=metadata,
            )
        print(f"Metadata saved to database")

    def move_file_to_processed(self, file_name:str)->None:
        """
        Move the processed file to the processed directory.
        """
        os.rename(os.path.join(self.to_process_path, file_name), os.path.join(self.processed_path, file_name))
        print(f"Moved {file_name} from {self.to_process_path} to {self.processed_path}")


    def main(self)->None:
        """
        Main function to process the PDF files.
        """
        for file in self.files:
            print("-" * 20)
            print(f"Processing {file}")
            print("-"*20)
            text = self.extract_text_from_pdf(file)
            metadata = self.clean_and_create_metadata(text)
            print(f"Metadata: {metadata.title}, {metadata.category}, {metadata.size}")
            self.save_metadata_to_db(metadata)
            self.move_file_to_processed(file)
            print(f"Processed {file}")
            print("-" * 20)
            print("\n\n")


if __name__ == "__main__":
    data = CreateRAGData()
    data.main()
