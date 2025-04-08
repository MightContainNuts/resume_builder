
from sqlmodel import SQLModel, create_engine, Session, select, inspect
from db.models import Documents
from dotenv import load_dotenv
from pathlib import Path
import os
import json



class DBHandler:
    def __init__(self):
        load_dotenv()
        self.engine = None
        self.session = None
        self.db_url = os.getenv("DATABASE_URL")

        # Resolve the path using pathlib


    def __enter__(self):
        self.create_engine()
        self.create_schema()
        self.create_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()

        if self.engine:
            self.engine.dispose()
        if exc_type or exc_val or exc_tb:
            print(f"An error occurred: \n {exc_val} \n {exc_tb} \n {exc_type}")
        print("Database connection closed.")


    def create_engine(self):
        self.engine = create_engine(self.db_url, echo=True)

    def create_session(self):
        if self.engine:
            self.session = Session(self.engine)
        else:
            raise ValueError("Engine not created. Call create_engine first.")

    def create_schema(self):
        """Create the database schema (tables) if they don't exist."""
        if self.engine:
            SQLModel.metadata.create_all(self.engine)
        else:
            raise ValueError("Engine not created. Call create_engine first.")


    def add_new_document(self, structured_data):
        """Add a document to the RAG table."""
        try:
            # Ensure structured_data is not None and has all the required fields
            if not structured_data:
                print("structured_data is None or invalid")
                return None

            title = structured_data.title
            content = structured_data.content
            category = structured_data.category
            size = structured_data.size

            print(f"Saving structured data to database: {title}")
            print(f"Title: {title}")
            print(f"Category: {category}")
            print(f"Size: {size}")
            print(f"Content: {content[:20]}")

            # Ensure all required fields are non-empty
            if not all([title, content, category, size]):
                print("One or more required fields are missing in structured_data")
                return None

            new_doc = Documents(
                title=title,
                content=content,
                category=category,
                size=size,
            )

            print(f"Created RAGDoc instance: {new_doc}")

            if not new_doc:
                print("Failed to create RAGDoc object.")
                return None

            self.session.add(new_doc)
            self.session.commit()

            print("Document saved successfully.")

        except Exception as e:
            print(f"Error occurred: {e}")
            self.session.rollback()

    def inspect_columns(self, table_name:str)->list:
        """
        Inspect the columns of the table.
        """
        inspector = inspect(self.engine)
        with DBHandler() as db:
            columns = [column['name'] for column in inspector.get_columns(table_name)]
        return columns

    def recreate_schema(self):
        """
        Recreate the database schema.
        """
        if self.engine:
            SQLModel.metadata.drop_all(self.engine)
            SQLModel.metadata.create_all(self.engine)
            print("Database schema recreated.")
        else:
            raise ValueError("Engine not created. Call create_engine first.")


    def retrieve_all_documents_from_db(self):
        """Retrieve all documents from the ragdoc table."""
        if self.engine:
            all_docs = self.session.exec(select(Documents.title,
                                                Documents.content,
                                                Documents.category)).all()
            print(f"Documents retrieved from the database. number of documents: {len(all_docs)}")

            all_docs_dict = [
                {"title": doc[0], "content": doc[1], "category": doc[2]} for doc in all_docs
            ]
            print(f"Documents retrieved from the database. number of documents: {len(all_docs)}")
            return all_docs_dict


    def store_documents_in_file(self, documents:list[dict[str:str]])->None:
        """Store documents in a file."""

        db_path = Path() / "files" /"documents.json"

        with open(db_path, "w", encoding='utf-8') as json_file:
            json.dump(documents, json_file, ensure_ascii=False,indent = 4)
        print("Documents stored in documents.json. number of documents: ", len(documents))

    def store_resume_to_file(self, resume:str)->None:
        """
        Store the resume to a file.
        """
        resume_path = Path() / "files" / "cover_letter.txt"
        with open(resume_path, "w") as f:
            f.write(resume)
        print(f"Stored resume to file")