# Warning control
import warnings
warnings.filterwarnings('ignore')

import os
from crewai import Agent, Task, Crew, Process, LLM
from dotenv import load_dotenv
from crewai_tools import ScrapeWebsiteTool, SerperDevTool
import streamlit as st
import time
from langchain_openai import ChatOpenAI

# Initialising the LLMs and the tools
load_dotenv()

search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()

os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")
huggingface_api_key = os.getenv("HUGGINGFACEHUB_API_TOKEN")
gemini_api_key = os.getenv("GEMINI_API_KEY")

gemini_pro_llm = LLM(
    api_key= gemini_api_key,
    model="gemini/gemini-1.5-pro",
)

gemini_llm = LLM(
    api_key= gemini_api_key,
    model="gemini/gemini-1.5-flash",
)

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_MODEL_NAME"] = 'gpt-4o'

# Defining the AGENTS

industry_analyst = Agent(
    role="Senior Industry Analyst",
    goal="researches about a company or an industry,"
         "regarding the strategic players, the relevant competitors,"
         "company's vision, its products, its Unique Selling Proposition(USP),"
         "strategic focus area and other important factors relevant to throughly"
         "understand the market trends and dynamics of a company or industry."
         "While searching the web avoid using long queries.",
    
    backstory="Experienced Senior Industry Analyst having strong Industry Knowledge"
              "and Research skills. Strong ability to analyze data and market trends "
              "to provide crucial insights important for decision making",

    verbose=True,
    allow_delegation=True,
    tools = [scrape_tool, search_tool]
)

business_analyst = Agent(
    role="Senior Business Analyst",
    goal="analyze business needs, identify opportunities for improvement,"
         "and facilitate the development of solutions that enhance processes,"
         "products, and services. Creates detailed report."
         "While searching the web avoid using long queries.",
    
    backstory="Certified Business Analysis Professional (CBAP) certified"
              "Senior Business Analyst having deep knowledge"
              "on Business Administration, Information Technology,"
              "Finance, Management and Economics."
              "Demonstrates strong ability to identify opportunities for potential development and propose effective solutions."
              "Expert in creating extremely detailed reports",

    verbose=True,
    allow_delegation=True,
    tools = [scrape_tool, search_tool]
)

AI_engineer = Agent(
    role="Senior AI Engineer",
    goal="Provide GenAI solutions for identified developemnt areas. "
         "Research recent relevant AI developments on required industry-use cases and"
         " provide relevant information with references.",
    
    backstory="Seasoned AI engineer with deep knowledge on GenAI,"
              "Always stays upto date with latest AI developments"
              "by researching  reports and insights on AI and digital"
              "transformation from industry-specific sources such as McKinsey, Deloitte, or Nexocode."
              "Helps management by suggesting relevant tech solutions"
              "and potential tech improvements.",

    verbose=True,
    allow_delegation=True,
    tools = [scrape_tool, search_tool]
)

report_editor = Agent(
    role="Senior Report Editor",
    goal="Ensure all the links provided in the report are actually correct."
         " Provide feasibility review on each of the given proposals in the report",
    
    backstory="Experienced Report editor with good knowledge regarding the feasibility and practicality of AI projects",

    verbose=True,
    allow_delegation=True,
    tools = [scrape_tool, search_tool]
)

# Defining the tasks

industry_research_task = Task(
    description=(
        "Research on {research_area}. Determine if {research_area} is a company or an Industry and research "
        "accordingly on it about its relevant segment and industry, its competitors, its vision and mission, "
        "its strategic focus areas  (e.g., operations, supply chain, customer experience, etc.) and all other information "
        "required to have a solid understanding of the Company or Industry"
    ),
    expected_output=(
        "Deep market research on {research_area} and its competitors necessary to understand"
        "its offerings, position in the market, demand areas, strategies and all the information"
        "necessary to understand the market trends and dynamics of the company or industry"
    ),
    agent= industry_analyst,
)

development_assessment_task = Task(
    description=(
        " 1. Based on the research on {research_area}, analyze industry trends and standards within the company's sector related to AI, ML, and automation."
        " 2. Propose relevant use cases where the company or industry can leverage GenAI, LLMs, and ML technologies to improve their processes, enhance"
        " customer satisfaction, and boost operational efficiency."
        " 3. Refer to reports and insights on AI and digital transformation from industry-specific sources such as McKinsey, Deloitte, or Nexocode."
        " 4. Search for industry-specific use cases (e.g., “how is the retail industry leveraging AI and ML” or “AI applications in automotive manufacturing”)."
        " 5. If applicable, propose GenAI solutions like document search, automated report generation, and AI-powered chat systems for internal or customer-facing purposes."
        " 6. Create a detailed market research report of {research_area} which should contain each of the proposed use-cases, application of AI, its benefits etc."
        " 7. Ensure actual clickable reference links are included at the end."
    ),
    expected_output=(
        "A detailed market research report containing the relevant use cases where the company or industry can leverage GenAI, LLMs, and ML technologies to improve their processes, enhance"
        " customer satisfaction, and boost operational efficiency. Also provide the relevant reference links of the industry use-cases at the end"
    ),
    agent= business_analyst,
    output_file = "market_research.md"
)

tech_proposal_task = Task(
    description=(
        " 1. Read the provided market research report to obtain the proposed use-cases"
        " 2. Loop through each and every proposed developments and search for relevant datasets for implementing its respective AI solutions on platforms like Kaggle, HuggingFace, and GitHub."
        " 3. Provide the reference links of the respective datasets for all the proposed use-cases."
        " 4. Ensure all use-cases have atleast one clickable reference link of relevant datasets."
    ),
    expected_output=(
        "A report containing the development area, a short description and the links of the respective datasets which can be used to implement the AI-based solutions."
        "Each development area must contain atleast one reference link."
    ),
    agent= AI_engineer,

)

editing_task = Task(
    description=(
        " 1. Ensure all the links provided in the report are actually correct."
        " 2. Incase any link does not leads to the expected dataset, correct the link."
        " 3. Provide feasibility and practicality review on each of the given proposals in the report"
        " 4. Ensure there are no spelling or grammatical error."
    ),
    expected_output=(
        "A report containing the development area, a short description and the links of the respective datasets which can be used to implement the AI-based solutions."
        "Each development area must contain atleast one reference link."
    ),
    agent= report_editor,
    output_file= "AI_use-cases.md"
)

# Defining the crew

market_research_crew = Crew(
    agents=[industry_analyst, business_analyst, AI_engineer, report_editor],
    tasks=[industry_research_task, development_assessment_task, tech_proposal_task, editing_task],
    cache = True,
    verbose=True,
    memory= True,
    manager_llm= ChatOpenAI(model="gpt-4o"),
    process= Process.hierarchical
)


def main():

    st.title("Market Research & Use Case Generation Agent")
    st.markdown("Enter a Industry or Company name to conduct market research and propose AI use-cases.")
    research_area = st.text_input("Research Area:", placeholder="Enter your research area (e.g., Tata Motors)")

    if st.button("Start Research"):
        if research_area:
            st.write(f"Generating market research data on {research_area}. Please wait...")

            with st.spinner("Researching..."):
   
                result = market_research_crew.kickoff(inputs={"research_area": research_area})

            st.markdown('<h3 style="color: #3498db;">Market Research Report</h3>', unsafe_allow_html=True)

            with open("market_research.md", "r") as file:
                final_report_content = file.read()
            st.markdown(final_report_content, unsafe_allow_html=True)


            st.markdown('<h3 style="color: #3498db;">AI use-case proposal Report</h3>', unsafe_allow_html=True)

            st.markdown(result.raw, unsafe_allow_html=True)
        else:
            st.warning("Please enter a research area to proceed.")

if __name__ == "__main__":
    main()
