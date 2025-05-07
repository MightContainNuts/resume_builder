
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json
from pydantic import BaseModel, Field

from langchain_core.messages import (
    SystemMessage,
)
from pathlib import Path
from app.db_handler import DBHandler



class AIResponse(BaseModel):
    """Response model for the LangChainHandler."""
    cl_company: str = Field(description="The companies name.")
    cl_role: str = Field(description="The role the candidate is applying for.")
    cl_opener: str = Field(description="The opening statement of the cover letter. (How You Heard About the Job)")
    cl_body: str = Field(description="The body of the cover letter. (How You Fit the Profile)")
    cl_bullet_points: str = Field(description="The bullet points of the cover letter. (Quantifiable Matches to the Job Description)")
    cl_motivation: str = Field(description="Motivation for applying. (Why You Want to Work for the Company)")
    cl_closing: str = Field(description="The closing statement of the cover letter. (Call to Action)")

    strengths: str = Field(description="Strengths of the candidate.")
    weaknesses: str = Field(description="Weaknesses of the candidate.")
    opportunities: str = Field(description="Opportunities for the candidate.")
    threats: str = Field(description="Threats to the candidate.")

    time_taken: str = Field(description="Time taken to generate the response.")
    token_count: int = Field(description="Number of tokens used in the response.")

class EvaluateChances(BaseModel):
    """Response model for the LangChainHandler."""
    chances: int = Field(description="Evaluation of the chances of getting the job, based on cover letter and job description.")
    reasoning: str = Field(description="Why the chances are what they are.")

class LangChainHandler:

    def __init__(self):

        load_dotenv()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_retries = 3,
        )

        self.documents = self._load_documents()
        self.job_description = self._load_job_description()


    def create_cover_letter(self) -> AIResponse:
        """Generate a response using the validated query and supplementary documents."""
        print("Creating draft cover letter")

        # Extract user query and documents

        prompt_with_docs = f"""
        Job Description: {self.job_description} Using the documents provided, which are: {self.documents}.
        Match skills from the document and job description and emphasise these in the cover letter
        The cover letter should be no longer than one page and should be in a professional format.
        The cover letter should be structured as follows:
        1. Company Name
        2. Role
        3. Opener (How You Heard About the Job)
        4. Body (How You Fit the Profile)
        5. Bullet Points (Quantifiable Matches to the Job Description)
        6. Motivation for applying (Why You Want to Work for the Company)
        7. Closing (Call to Action)
        include a SWOT analysis of the candidate and include the strengths, weaknesses, opportunities and threats.
        Create a cover letter that is professional and engaging, but not too much like an AI generated response.
        Ensure the cover letter is generated in the language of the job description.
        """

        # Generate response from LLM
        structured_llm = self.llm.with_structured_output(AIResponse)
        response = structured_llm.invoke([SystemMessage(content=prompt_with_docs)])
        assert isinstance(response, AIResponse), "Response is not of type AIResponse on Generation"
        print(f"Response time = {response.time_taken}, tokens: {response.token_count}")
        return response

    def improve_cover_letter(self, cover_letter_draft, strengths, weaknesses, opportunities, threats, draft_chance) -> AIResponse:
        "create an improved cover letter based on results from the first draft"
        print("Improving cover letter")

        prompt_with_info = f"""
        Check the draft cover letter {cover_letter_draft} provided and improve it using standard cover letter writing.
        Try and cover any missing critical points and address any issues with the content and structure.
        Improve the content against the {strengths},{weaknesses}, {opportunities}, {threats} and the job description 
        {self.job_description} to improve {draft_chance.chances} % chance of getting the job.
        Look for missed skills that are available in {self.documents} that compliment the skills required or that you
        feel are noteworthy. The cover letter should impress the reader, but not sound to much like an AI generated 
        response.The cover letter should be no longer than one page and should be in a professional format."""


        # Generate response from LLM
        structured_llm = self.llm.with_structured_output(AIResponse)
        final_cover_letter = structured_llm.invoke([SystemMessage(content=prompt_with_info)])
        assert isinstance(final_cover_letter, AIResponse), "Response is not of type AIResponse on Generation"
        print(f"Response time = {final_cover_letter.time_taken}, tokens: {final_cover_letter.token_count}")
        return final_cover_letter

    def analyse_chances(self, final_cover_letter) -> EvaluateChances:
        "Evaluate the chances of getting the job based on the cover letter draft"
        print("Evaluating chances")
        prompt_with_info = f"""
        Evaluate the enhanced cover letter {final_cover_letter} and evaluate against the job description in percentage.
        Summarise your reasoning"""

        # Generate response from LLM
        structured_llm = self.llm.with_structured_output(EvaluateChances)
        response = structured_llm.invoke([SystemMessage(content=prompt_with_info)])
        print(f"Response generated: Chances of getting the job: {response.chances} %")
        print(response.reasoning)
        return response

    def create_profile_summary(self) -> str:
        "create an improved cover letter based on results from the first draft"
        print("creating profile summary")

        prompt_with_info = f"""
        using the {self.documents}, create a summary of the profile."""

        # Generate response from LLM

        profile_summary = self.llm.invoke([SystemMessage(content=prompt_with_info)])


        return profile_summary.content


    @staticmethod
    def _load_documents()->dict|None:
        print("Loading documents")
        """Load assistant guidelines from file."""
        doc_path = Path() / "files" / "documents.json"
        try:
            with open(doc_path, "r") as file:
                return json.load(file)

        except Exception as e:
            print(f"Error loading documents: {e}")


    @staticmethod
    def _load_job_description()->str|None:
        """Load assistant guidelines from file."""
        print("Loading job description")
        doc_path = Path() / "files" / "job_description.txt"
        try:
            with open(doc_path, "r") as file:
                return file.read()

        except Exception as e:
            print(f"Error loading documents: {e}")

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
        first_draft = self.create_cover_letter()
        draft_template = self.create_cover_letter_file(first_draft)
        draft_chance    = self.analyse_chances(draft_template)
        final_cover_letter =self.improve_cover_letter(draft_template,
                                                      strengths=first_draft.strengths,
                                                      weaknesses=first_draft.weaknesses,
                                                      opportunities=first_draft.opportunities,
                                                      threats=first_draft.threats,
                                                      draft_chance=draft_chance)
        self.analyse_chances(final_cover_letter)
        final_template = self.create_cover_letter_file(final_cover_letter)
        with DBHandler() as db:
            db.store_resume_to_file(final_template, type="cover_letter")
        summary = self.create_profile_summary()
        with DBHandler() as db:
            db.store_resume_to_file(summary, type="profile_summary")
