"""Data Acquisition Crew — 2 agents: Static Data Extractor + Dynamic Data Retriever."""

from crewai import Agent, Crew, Process, Task
from crewai_tools import PDFSearchTool, FileReadTool, SerperDevTool, ScrapeWebsiteTool

from dentalbench.tools.docx_parser_tool import DocxParserTool
from dentalbench.tools.pubmed_search_tool import PubMedSearchTool

SKILLS_DIR = "./src/dentalbench/skills"


def static_data_extractor() -> Agent:
    return Agent(
        role="Static Data Extractor",
        goal=(
            "Extract structured content from oral medicine textbook PDFs, "
            "clinical guideline PDFs, and dental licensing exam Word documents. "
            "Classify each piece of content by subspecialty, knowledge type, and topic."
        ),
        backstory=(
            "You are a biomedical data engineer specializing in dental literature. "
            "You parse complex medical documents into clean, structured data."
        ),
        skills=[
            f"{SKILLS_DIR}/pdf-extraction",
            f"{SKILLS_DIR}/exam-parsing",
            f"{SKILLS_DIR}/oral-medicine-taxonomy",
        ],
        tools=[PDFSearchTool(), FileReadTool(), DocxParserTool()],
        verbose=True,
    )


def dynamic_data_retriever() -> Agent:
    return Agent(
        role="Dynamic Data Retriever",
        goal=(
            "Search PubMed Central for open-access oral medicine case reports "
            "(last 5 years), extract structured clinical data, and fetch "
            "supplementary information from authoritative medical web sources."
        ),
        backstory=(
            "You are a clinical research librarian with expertise in systematic "
            "literature retrieval for oral and maxillofacial medicine."
        ),
        skills=[
            f"{SKILLS_DIR}/pubmed-search",
            f"{SKILLS_DIR}/case-report-extraction",
            f"{SKILLS_DIR}/web-research-medical",
        ],
        tools=[PubMedSearchTool(), SerperDevTool(), ScrapeWebsiteTool()],
        verbose=True,
    )


def extract_static_task(agent: Agent, pdf_dir: str, exam_dir: str) -> Task:
    return Task(
        description=(
            f"1. Extract structured content from all PDF files in '{pdf_dir}'. "
            f"For each PDF, output JSON with title, section_hierarchy, content, page_number, content_type.\n"
            f"2. Parse all .docx exam files in '{exam_dir}'. "
            f"For each file, extract question_stem, options, correct_answer, explanation, subject. Translate to English.\n"
            f"3. Classify every extracted item by subspecialty (10 categories), knowledge_type (4 levels), and dimension (D1-D10)."
        ),
        expected_output=(
            "A JSON array of extracted content items, each with fields: "
            "source_file, source_type (textbook|guideline|exam), subspecialty, "
            "knowledge_type, dimension, content, and source_reference."
        ),
        agent=agent,
    )


def retrieve_dynamic_task(agent: Agent) -> Task:
    return Task(
        description=(
            "1. Search PMC-OA for oral medicine case reports across all subspecialties "
            "(last 5 years, English, open access). Target 700-1000 case reports.\n"
            "2. For each retrieved case report, extract structured clinical data: "
            "chief_complaint, history, examination, diagnosis, treatment, outcome.\n"
            "3. Tag each case report with subspecialty and relevant clinical topics."
        ),
        expected_output=(
            "A JSON array of case report objects, each with fields: "
            "pmcid, title, authors, year, doi, subspecialty, "
            "chief_complaint, history_present_illness, physical_examination, "
            "auxiliary_examination, diagnosis, differential_diagnosis, treatment, outcome."
        ),
        agent=agent,
    )


def create_data_acquisition_crew(pdf_dir: str, exam_dir: str) -> Crew:
    extractor = static_data_extractor()
    retriever = dynamic_data_retriever()

    return Crew(
        agents=[extractor, retriever],
        tasks=[
            extract_static_task(extractor, pdf_dir, exam_dir),
            retrieve_dynamic_task(retriever),
        ],
        process=Process.sequential,
        verbose=True,
    )
