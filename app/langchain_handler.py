
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json

from langchain_postgres import PGVector
from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer

from langchain_core.messages import (
    SystemMessage,
)
from pathlib import Path
from app.db_handler import DBHandler
import os

from typing import List, Tuple
import numpy.typing as npt
import numpy as np
from torch import Tensor
from langchain.schema import Document

from db.schemas import AIResponse, EvaluateCoverLetter, Match, DataJobDescription



class LangChainHandler:

    def __init__(self):

        load_dotenv()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_retries = 3,
        )


        self.structured_job_description = None
        self.vector_store = self._vector_store_documents()
        self.documents = None
        self.job_description = None

    def extract_key_data_from_job_description(self, external_job_description=None):
        """Extract key data from the job description."""
        if external_job_description:
            self.job_description = external_job_description
            print("Using external job description")

        print("Extracting key data from job description")
        prompt = f"""
        Extract the key data from the job description {self.job_description} and return it in a structured format.
        The key data should include the following fields:
        1. Company Name (name of the company offering the job)
        2. Contact Person (if available)    
        3. Job Title (e.g. Engineering Manager, Project Manager, etc.)
        4. Location of the job itself
         - this may differ from the location of the company offering the job
        5. Work Type (remote, on-site, hybrid)
        6. Employment Type (e.g. Full-time, Part-time, Contract, etc.)
        7. Requirements (e.g. skills, experience, etc.)
        8. Nice to Haves (e.g. skills, experience, etc.)
        9. Experience level (Junior, Mid, Senior)
        10. Education level (e.g. Bachelors, Masters, etc.)
        11. Compensation (e.g. salary, benefits, etc.)
        12. Company Culture (e.g. values, mission, etc.)
        13. Company Size (e.g. number of employees, etc.)
        14. Company Industry (e.g. technology, finance, etc.)
        15. Work hours (e.g. 9-5, flexible, etc.)
        16. Summary (e.g. skills, experience, etc.)
        """

        # Generate response from LLM
        structured_llm = self.llm.with_structured_output(DataJobDescription)
        self.structured_job_description:DataJobDescription = structured_llm.invoke([SystemMessage(content=prompt)])
        assert isinstance(self.structured_job_description, DataJobDescription), "Response is not of type AIResponse on Generation"
        print("Structured job description generated")
        print("-" * 20)
        print(f"Company Name: {self.structured_job_description.company_name}")
        print(f"Role: {self.structured_job_description.job_title}")
        print(f"Requirements: {self.structured_job_description.requirements}")
        print(f"Preferred/Nice to Have: {self.structured_job_description.nice_to_haves}")
        print(f"Compensation: {self.structured_job_description.compensation}")
        print(f"Location: {self.structured_job_description.location}")
        print(f"Summary: {self.structured_job_description.summary}")
        print("-" * 20)

        return self.structured_job_description




    def create_cover_letter(self, requirements, nice_to_haves, experiences,) -> AIResponse:
        """Generate a response using the validated query and supplementary documents."""
        print("Creating draft cover letter")

        # Extract user query and documents

        prompt_with_docs = f"""
        Job Description: {self.structured_job_description} Using the results from the similarity search and from
        the matching requirements {requirements}, possible nice to haves {nice_to_haves}, and experience levels {experiences}, create a cover letter with the goal of
        landing the job.
        The cover letter should be no longer than one page and should be in a professional format.
        The cover letter should be structured as follows:
        1. cl_company (Company Name)
        2. cl_role (what role the candidate is applying for)
        3. cl_opener (How You Heard About the Job - if not available, use a generic statement)
        4. cl_body (How You Fit the Profile)
        5. cl_bullet_points (Quantifiable Matches to the Job Description as Bullet points)
        6. cl_motivation (Motivation for applying to Work for the Company)
        7. cl_closing ( closing statement and Call to Action)
        Create a cover letter that is professional and engaging, without having typical AI generated influences. Ensure all categories are covered.
        Ensure the cover letter is generated in the language of the job description.
        """


        # Generate response from LLM
        structured_llm = self.llm.with_structured_output(AIResponse)
        response = structured_llm.invoke([SystemMessage(content=prompt_with_docs)])
        assert isinstance(response, AIResponse), "Response is not of type AIResponse on Generation"
        print(f"Response time = {response.time_taken}, tokens: {response.token_count}")
        return response


    def evaluate_cover_letter(self, cover_letter) -> EvaluateCoverLetter:
        "Evaluate the chances of getting the job based on the cover letter draft"
        print("Evaluating draft")
        prompt_with_info = f"""
        Evaluate the enhanced cover letter {cover_letter} from the aspect of the company looking for someone to fill the job with the following description {self.job_description}
        
        using a continuous score between 0 and 1 accurate to 3 decimal places. If there are no requirements for a certain category return 1
        The evaluation should include the following fields:
        1. Skill Match (e.g. skills, experience, etc.)
        2. Nice to Have (e.g. skills, experience, etc.)
        3. Direct Experience Match (e.g. skills, experience, etc.)
        4. Transfer Experience Match (e.g. skills, experience, etc.)
        5. Education Match (e.g. skills, experience, etc.)
        6. Culture Match (e.g. skills, experience, etc.)
        7. Soft Skills Match (e.g. skills, experience, etc.)
        8. Certificates Match (e.g. skills, experience, etc.)
        9. Goal Alignment Match (e.g. skills, experience, etc.)
        10. Result (product of all the above fields as percentage)
        """

        # Generate response from LLM
        structured_llm = self.llm.with_structured_output(EvaluateCoverLetter)
        response = structured_llm.invoke([SystemMessage(content=prompt_with_info)])
        print(f"Response generated: Chances of getting the job:  %")
        for field in response.__fields_set__:
            print(f"{field}: {getattr(response, field)}")
        return response

    def create_profile_summary(self) -> str:
        """create an improved cover letter based on results from the first draft"""
        print("creating profile summary")

        prompt_with_info = f"""
        using the {self.documents}, create a comprehensive summary of the profile.
        Highlight experience, skills, education, and any other relevant information relevant to a job application.
        """

        # Generate response from LLM

        profile_summary = self.llm.invoke([SystemMessage(content=prompt_with_info)])


        return profile_summary.content

    def match_for_jobs(self, job_description:str) -> Match:
        """evaluate match based on structured job description and profile"""
        system_prompt =f"""
        Evaluate how much the profile summary matches the job description {job_description}
        i.e 
        Hard skills, experience, soft skills etc.
        Give the response back as a percentage in the range of 0 to 100 (int)
        """
        structured_llm = self.llm.with_structured_output(Match)
        match = structured_llm.invoke([SystemMessage(content=system_prompt)])
        return match


    @staticmethod
    def _load_documents()->dict|None:
        print("Loading documents")
        """Load assistant guidelines from file."""
        project_root = Path(__file__).parent.parent
        doc_path = project_root / "files" / "documents.json"
        print(doc_path)
        try:
            with open(doc_path, "r") as file:
                return json.load(file)

        except Exception as e:
            print(f"Error loading documents: {e}")
            return None

    @staticmethod
    def _load_job_description()->str|None:
        """Load assistant guidelines from file."""
        print("Loading job description")
        project_root = Path(__file__).parent.parent
        doc_path = project_root / "files" / "job_description.txt"
        print(doc_path)
        try:
            with open(doc_path, "r") as file:
                return file.read()

        except Exception as e:
            print(f"Error loading documents: {e}")
            return None

    @staticmethod
    def create_cover_letter_file(cover_letter:AIResponse)->str:
        """ crete a cover letter file"""
        print("Creating cover letter file")
        template = f"""
{cover_letter.cl_opener} \n
{cover_letter.cl_body}\n
{cover_letter.cl_bullet_points}\n
{cover_letter.cl_motivation}\n
{cover_letter.cl_closing}
        """
        return template


    def main(self):
        """one function to rule them all"""
        self.documents = self._load_documents()
        self.job_description = self._load_job_description()
        self.extract_key_data_from_job_description()

        requirements, nice_to_haves, experiences = self.retrieve_from_vector_store()
        draft_response:AIResponse = self.create_cover_letter(requirements, nice_to_haves, experiences)
        cover_letter_evaluation= 0
        counter =0
        draft_str = ""
        while cover_letter_evaluation < 0.8 and counter < 3:
            counter += 1
            draft_str = self.create_cover_letter_file(draft_response)
            evaluation_summary    = self.evaluate_cover_letter(draft_str)
            cover_letter_evaluation = evaluation_summary.result

        with DBHandler() as db:
            db.store_resume_to_file(draft_str, type_name="cover_letter")

        with DBHandler() as db:
            db.store_resume_to_file(self.profile_summary, type_name="profile_summary")

    @staticmethod
    def _vector_store_documents() -> PGVector:
        """creates a vector store for the documents"""
        load_dotenv()
        connection_string = os.getenv("DATABASE_URL")
        return PGVector(connection=connection_string,
            collection_name="chat_history", use_jsonb=True,
            embeddings=EmbeddingFunctionWrapper(
                "all-MiniLM-L6-v2"), )

    def add_to_vector_store_documents(self, split_docs: List[Document]) -> None:
        """Embeds and stores the user query and AI response into the vector store."""
        print("Adding new document to vector store ...")

        self.vector_store.add_documents(
            documents=split_docs,
        )

    def retrieve_from_vector_store(self) -> Tuple[List, List, List]:
        """Retrieves the most relevant documents from the vector store."""
        print("Retrieving relevant documents from vector store ...")
        requirement_results = []
        nice_to_have_results = []
        experience_results = []
        for requirement in self.structured_job_description.requirements.split(","):
            print(f"Requirement: {requirement}")
            results = self.vector_store.similarity_search(
                requirement,
                k=5,
            )
        for nice_to_have in self.structured_job_description.preferred_nice_to_have.split(","):
            print(f"Nice to have: {nice_to_have}")
            nice_to_have_results += self.vector_store.similarity_search(
                nice_to_have,
                k=5,
                )
        for experience in self.structured_job_description.experience_level.split(","):
            print(f"Experience: {experience}")
            experience_results += self.vector_store.similarity_search(
                experience,
                k=5,
                )

        return requirement_results, nice_to_have_results, experience_results

class EmbeddingFunctionWrapper(Embeddings):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> npt.NDArray[np.float32]:
        # Use the encode method to generate embeddings
        return self.model.encode(texts, convert_to_tensor=False)

    def embed_query(self, text: str) -> Tensor:
        # For single query embedding
        return self.model.encode(text, convert_to_tensor=False)
