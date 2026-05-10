"""
Graph builder module for the adaptive RAG system.
"""

from langchain_community.tools import TavilySearchResults
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate
from langgraph.constants import START, END
from langgraph.graph.state import StateGraph

from src.rag.reAct_agent import agent_executor
from src.config.settings import Config
from src.llms.openai import llm
from src.models.grade import Grade
from src.models.state import State
from src.tools.graph_tools import doc_tool

config = Config()


# -------------------------------
# Query Classifier (no forced routing)
# -------------------------------
def query_classifier(state: State):
    question = state["messages"][-1].content

    return {
        "messages": state["messages"],
        "latest_query": question
    }


# -------------------------------
# Retriever Node
# -------------------------------
def retriever_node(state: State):
    query = state["latest_query"]

    result = agent_executor.invoke({"input": query})

    intermediate_steps = result.get("intermediate_steps", [])
    tool_calls = []

    if intermediate_steps:
        for action, tool_result in intermediate_steps:
            tool_calls.append({
                "tool": action.tool,
                "input": action.tool_input,
            })

    new_message = AIMessage(
        content=result["output"],
        additional_kwargs={"tool_calls": tool_calls},
    )

    return {"messages": [new_message]}


# -------------------------------
# Grade Retrieved Results
# -------------------------------
def grade(state: State):
    grading_prompt = PromptTemplate(
        template=config.prompt("grading_prompt"),
        input_variables=["question", "context"]
    )

    context = state["messages"][-1].content
    question = state["latest_query"]

    llm_with_grade = llm.with_structured_output(Grade)

    chain = grading_prompt | llm_with_grade
    result = chain.invoke({"question": question, "context": context})

    return {
        "messages": state["messages"],
        "binary_score": result.binary_score
    }


# -------------------------------
# Query Rewrite (optional)
# -------------------------------
def rewrite_query(state: State):
    query = state["latest_query"]

    rewrite_prompt = PromptTemplate(
        template=config.prompt("rewrite_prompt"),
        input_variables=["query"]
    )

    chain = rewrite_prompt | llm
    result = chain.invoke({"query": query})

    return {"latest_query": result.content}


# -------------------------------
# Generate Final Answer
# -------------------------------
def generate(state: State):
    context = state["messages"][-1].content

    generate_prompt = PromptTemplate(
        template=config.prompt("generate_prompt"),
        input_variables=["context"]
    )

    chain = generate_prompt | llm
    result = chain.invoke({"context": context})

    return {
        "messages": [{"role": "assistant", "content": result.content}]
    }


# -------------------------------
# Web Search (Tavily)
# -------------------------------
def web_search(state: State):
    search_tool = TavilySearchResults()

    result = search_tool.invoke(state["latest_query"])

    contents = [item["content"] for item in result if "content" in item]

    return {
        "messages": [
            {"role": "assistant", "content": "\n\n".join(contents)}
        ]
    }


# -------------------------------
# Routing after grading
# -------------------------------
def grade_router(state: State):
    if state["binary_score"] == "yes":
        return "generate"
    else:
        return "web_search"


# -------------------------------
# Build Graph
# -------------------------------
graph = StateGraph(State)

graph.add_node("query_analysis", query_classifier)
graph.add_node("retriever", retriever_node)
graph.add_node("grade", grade)
graph.add_node("generate", generate)
graph.add_node("rewrite", rewrite_query)
graph.add_node("web_search", web_search)

# Flow
graph.add_edge(START, "query_analysis")

# Always retrieve first
graph.add_edge("query_analysis", "retriever")

# Then grade
graph.add_edge("retriever", "grade")

# Conditional routing
graph.add_conditional_edges("grade", grade_router)

# If web search → generate
graph.add_edge("web_search", "generate")

# End
graph.add_edge("generate", END)

builder = graph.compile()