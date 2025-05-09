# 📄 AI-Powered Resume & Cover Letter Assistant

This application automates the process of extracting information from PDF documents (such as resumes, certificates, etc.), stores them in a database, and uses a Large Language Model (LLM) to generate a tailored cover letter based on a provided job description.

---

## 🧠 Features

- Extracts text from PDF documents such as CVs, Resumes, and Certificates.
- Cleans and parses the text using OpenAI's GPT-4o-mini model.
- Stores metadata (title, content, category, size) in a Langgraph Vector Store (PGVector).
- Creates a Profile Summary based on all the parsed documents.
- Generates a structured output of the job description including requirements and nice-to-have skills.
- Retrieves results from similarity searches of required and nice to have skills
- Generates a professional, skill-aligned cover letter using LangChain and OpenAI.
- Improves the cover letter based on the job description and profile summary (in case of anything is missed)
- Recommends improvements to increase job application success chances.
- Gives an evaluation of the cover letter based on the job description and profile summary.

---

## 📂 Project Structure
├── app
│   ├── db_handler.py             # Handles database connections and CRUD operations
│   ├── extract_pdf_to_database.py # Extracts and parses PDF content
│   ├── langchain_handler.py     # Handles LLM prompts and cover letter generation
│   └── init.py
├── db
│   └── models.py                 # SQLModel data definitions
├── files
│   ├── documents.json            # Auto-generated file storing all parsed documents
│   └── job_description.txt       # Text file containing the job description
├── to_process                   # Folder containing PDFs to be processed
├── processed                    # Folder for already processed PDFs
├── main.py                      # Entry point for the application
├── .env                         # Environment variables (e.g., OpenAI keys, DB URL)
└── README.md

---

## 🛠️ Requirements

- Python 3.10+
- Poetry or pip for dependency management
- SQLite (default, can be changed in `.env`)
- API Key for OpenAI

---

## 🚀 Running the App
```angular2html
python main.py
```

The app will:
	•	Process PDFs in to_process/
	•	Store metadata in the database
	•	Retrieve documents and write them to files/documents.json
	•	Generate a cover letter using LangChain + GPT
	•	Print and save the result