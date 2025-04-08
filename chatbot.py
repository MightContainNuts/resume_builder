import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from typing import List, Union
from langgraph.graph import START, END
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from app.services.tools import get_tavily_search_tool, get_wiki_summary
from typing import Optional

class State(BaseModel):
    """State class for LangGraph workflow."""
    messages: List[Union[HumanMessage, AIMessage]] = Field(default_factory=list)
    is_valid_query: bool = True

from pathlib import Path


class LangChainHandler:

    def __init__(self):
        load_dotenv()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            max_retries = 3,
        )

        self.documents = self._load_documents()

        self.guidelines = self._load_guidelines()
        self.workflow = self.build_workflow()


    def build_workflow(self):
        """Build the LangGraph workflow."""
        workflow = StateGraph(State)

        # Create the agent node with the ReAct agent
        agent = create_react_agent(
            self.llm,
            tools=[get_wiki_summary, get_tavily_search_tool, ],
            )


        # Add nodes to the graph
        workflow.add_node("validate", self.is_query_valid)
        workflow.add_node("handle_prompt_with_documents", self.handle_prompt_with_documents)
        workflow.add_node("agent", agent)


        # Add edges between nodes
        workflow.add_edge(START, "validate")

        # Explicitly define a unique branch name for the conditional edge
        workflow.add_conditional_edges(
            "validate",
            lambda state: "handle_prompt_with_documents" if state.is_valid_query else END)

        # Add edge from lookup_vector_store to agent
        workflow.add_edge("agent", "agent")

        workflow = workflow.compile()
        print(f"Workflow compiled successfully.")
        return workflow

    def is_query_valid(self, state:State)-> State:
        """Validate the user's query against the guidelines."""
        print("Validating Query against guidelines")
        try:
            user_message = state.messages[-1].content
            validation_prompt = f"""Using {self.guidelines}, determine if the  '{user_message}' is within the 
            guidelines. If the query is valid, return 'True' for is is_valid_query else 'False'
            If is_valid_query is false - create a polite but concise response to that effect.
            """

            response = self.llm.invoke([SystemMessage(content=validation_prompt)])

            if state.is_valid_query:
                print(f"Query within guidelines")
                print(f"Response: {response.content}")


            else:
                print(f"Query not within guidelines")

        except Exception as e:
            print(f"Error validating query: {e}")
            state.is_valid_query = False
            state.messages.append(
                AIMessage(content="Sorry, I had a problem validating your query. Please try again.")
            )
        return state

    def handle_prompt_with_documents(self, state: State) -> State:
        """Generate a response using the validated query and supplementary documents."""
        print("Handling prompt with documents")
        try:
            # Extract user query and documents
            user_message = state.messages[-1].content
            prompt_with_docs = f"""
            User query: {user_message} Here are the relevant documents to guide the response: 
            {self.documents} Based on the query and contents of the file, provide a helpful and 
            relevant response. Format the response using markdown for better readability."""

            # Generate response from LLM
            response = self.llm.invoke([SystemMessage(content=prompt_with_docs)])

            # Append the response to the state
            state.messages.append(AIMessage(content=response.content))
            print("Response generated successfully.")
        except Exception as e:
            print(f"Error in handle_prompt_with_documents: {e}")
            state.messages.append(
                AIMessage(content="Sorry, I encountered an error generating the response.")
            )
        return state

    def handle_message(self, user_message):
        # Process the message using the LLM
        try:
            # Create initial state
            input_state = State(
                messages=[HumanMessage(content=user_message)],
                is_valid_query=True
            )


            # Invoke the workflow
            result = self.workflow.invoke(input_state)

            # Extract AI response
            ai_messages = [
                msg.content
                for msg in result["messages"]
                if isinstance(msg, AIMessage)
            ]
            return (
                ai_messages[-1]
                if ai_messages
                else "Oops..An error occurred. Please try again later."
            )
        except Exception as e:
            print(f"Error processing chat: {e}")
            return "An error occurred. Please try again later."


#internal functions
    @staticmethod
    def _load_guidelines():
        """Load assistant guidelines from file."""
        base_path = Path(__file__).resolve().parent.parent.parent
        guidelines_path = base_path / "app" / "static" / "files" / "documents.json"
        try:

            with open(guidelines_path, "r") as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading guidelines: {e}")
            return {
                "prohibited_content": [
                    "harmful content",
                    "illegal activities",
                ],

            }


    @staticmethod
    def _load_documents()->Optional[dict|None]:
        """Load assistant guidelines from file."""
        base_path = Path(__file__).resolve().parent.parent.parent
        doc_path = base_path / "app" / "static" / "files" / "documents.json"
        try:
            with open(doc_path, "r") as file:
                return json.load(file)

        except Exception as e:
            print(f"Error loading documents: {e}")



if __name__ == "__main__":
    langchain_handler = LangChainHandler()
    print(langchain_handler.handle_message("what certificates regarding agile has Dean completed?"))
