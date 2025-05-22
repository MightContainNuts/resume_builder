# pydantic schemas

from pydantic import BaseModel, Field





class AIResponse(BaseModel):
    """Response model for the LangChainHandler."""
    cl_company: str = Field(description="The companies name.")
    cl_role: str = Field(description="The role the candidate is applying for.")
    cl_opener: str = Field(description="The opening statement of the cover letter. (How You Heard About the Job)")
    cl_body: str = Field(description="The body of the cover letter. (How You Fit the Profile)")
    cl_bullet_points: str = Field(description="The bullet points of the cover letter. (Quantifiable Matches to the Job Description)")
    cl_motivation: str = Field(description="Motivation for applying. (Why You Want to Work for the Company)")
    cl_closing: str = Field(description="The closing statement of the cover letter. (Call to Action)")

    time_taken: str = Field(description="Time taken to generate the response.")
    token_count: int = Field(description="Number of tokens used in the response.")

class EvaluateCoverLetter(BaseModel):
    """Response model for the LangChainHandler."""
    skill_match:float = Field(description="Evaluation of the skill match value between the candidate and the job description.")
    nice_to_have_match: float = Field(description="Evaluation of the nice to have skills match between the candidate and the job description.")
    direct_experience_match:float = Field(description="Evaluation of the experience match value between the candidate and the job description.")
    transfer_experience_match: float = Field(description="Evaluation of the transferable experience match between the candidate and the job description.")
    education_match: float = Field(description="Evaluation of the education match between the candidate and the job description.")
    culture_match: float = Field(description="Evaluation of the culture match between the candidate and the job description.")
    soft_skills_match: float = Field(description="Evaluation of the soft skills match between the candidate and the job description.")
    certificates_match: float = Field(description="Evaluation of the certificates match between the candidate and the job description.")
    goal_alignment_match: float = Field(description="Evaluation of the goal alignment match between the candidate and the job description.")
    result: float = Field(description="Overall evaluation of the chances of getting the job.")

class DataJobDescription(BaseModel):
    """Response model for the LangChainHandler."""
    company_name: str = Field(description="The companies name.")
    contact_person: str = Field(description="The contact person for the job.")
    job_title: str = Field(description="The title of the job.")
    employment_type: str = Field(description="The type of employment.")
    requirements: str = Field(description="The requirements for the job.")
    nice_to_haves: str = Field(description="Preferred or nice to have skills.")
    experience_level: str = Field(description="Experience level required for the job.")
    education_level: str = Field(description="Education level required for the job.")
    compensation: str = Field(description="Compensation offered for the job.")
    company_culture: str = Field(description="Company culture and values.")
    location: str = Field(description="Location of the job.")
    company_size: str = Field(description="Size of the company.")
    company_industry: str = Field(description="Industry of the company.")
    work_hours: str = Field(description="Work hours for the job.")
    summary: str = Field(description="Summary of the job.")

class Match(BaseModel):
    """Response model for the LangChainHandler."""
    match:int = Field(description="Match value between the candidate and the job description.")


class PDFMetadata(BaseModel):
    title: str
    content: str
    category: str
    size: int