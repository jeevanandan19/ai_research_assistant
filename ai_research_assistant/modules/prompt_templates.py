"""
Prompt Templates Module
Custom prompt templates engineered to minimize hallucinations
and restrict answers to retrieved document context.
"""
from langchain_core.prompts import PromptTemplate


# ─────────────────────────────────────────────────────────────────────
# Research Paper Summarization Prompt
# ─────────────────────────────────────────────────────────────────────
SUMMARIZATION_PROMPT = PromptTemplate(
    input_variables=["context"],
    template="""You are an expert academic research analyst. Analyze the provided research paper content and generate a comprehensive structured summary.

RESEARCH PAPER CONTENT:
{context}

STRICT INSTRUCTIONS:
- Base your analysis ONLY on the content provided above.
- Do NOT hallucinate or add information not present in the text.
- Maintain professional academic language.
- If a section cannot be determined from the text, state "Not explicitly mentioned in the paper."

Generate your response in the following format:

## Abstract Summary
[Provide a concise 3-5 sentence overview of the paper's objective and primary findings.]

## Detailed Summary
[Provide a comprehensive 200-300 word summary covering background, methodology, experiments, and results.]

## Key Contributions
- [Contribution 1]
- [Contribution 2]
- [Contribution 3]

## Limitations
- [Limitation 1]
- [Limitation 2]

## Future Work Suggestions
- [Suggestion 1]
- [Suggestion 2]
""",
)


# ─────────────────────────────────────────────────────────────────────
# Question Answering Prompt
# ─────────────────────────────────────────────────────────────────────
QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a precise AI research assistant. Answer questions about research papers using ONLY the provided context.

RETRIEVED CONTEXT FROM DOCUMENT:
{context}

QUESTION: {question}

RULES:
1. Answer using ONLY information from the context above.
2. Do NOT use any external knowledge or make assumptions.
3. If the answer is NOT in the context, respond with exactly: "Information not found in the uploaded document."
4. Be concise but thorough. Use specific details from the context.
5. Use professional academic language.

Answer:""",
)


# ─────────────────────────────────────────────────────────────────────
# Keyword Extraction Prompt
# ─────────────────────────────────────────────────────────────────────
KEYWORD_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["context"],
    template="""You are an NLP expert. Extract the most important technical keywords from the research paper content below.

PAPER CONTENT:
{context}

INSTRUCTIONS:
- Focus on technical terms, methods, algorithms, datasets, metrics, and domain concepts.
- Include acronyms with full forms when present.
- Prioritize terms central to the paper's contribution.
- Aim for 15-25 relevant keywords total.

Return ONLY valid JSON in this exact format (no extra text, no markdown):
{{"primary_keywords": ["keyword1", "keyword2"], "technical_methods": ["method1", "method2"], "datasets_and_metrics": ["dataset1", "metric1"], "domain_concepts": ["concept1", "concept2"]}}""",
)


# ─────────────────────────────────────────────────────────────────────
# Key Insight Extraction Prompt
# ─────────────────────────────────────────────────────────────────────
INSIGHT_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["context"],
    template="""You are an expert academic reviewer. Analyze the research paper content and extract key insights.

PAPER CONTENT:
{context}

Extract insights based ONLY on the provided content. Use professional academic language.

## Core Research Insight
[The single most important finding in 2-3 sentences.]

## Technical Innovation
[What technical approach or method is novel about this work?]

## Empirical Findings
[Summarize key quantitative or qualitative results.]

## Broader Impact
[Implications for the field or real-world applications.]

## Critical Observations
[Noteworthy observations about methodology or experimental design.]
""",
)


# ─────────────────────────────────────────────────────────────────────
# Novelty Detection Prompt
# ─────────────────────────────────────────────────────────────────────
NOVELTY_DETECTION_PROMPT = PromptTemplate(
    input_variables=["context"],
    template="""You are a senior researcher evaluating novelty of a research paper. Assess only based on claims made within the paper itself.

PAPER CONTENT:
{context}

## Novelty Score Assessment
[Rate as: High / Medium / Low novelty with brief justification based on the paper's own claims.]

## Novel Technical Contributions
[List specific new techniques, architectures, or methods introduced.]

## Novel Applications or Use Cases
[List any new application domains addressed.]

## Differentiation from Prior Work
[Based only on what the paper states, how does it differ from existing approaches?]

## Innovation Summary
[2-3 sentence summary of what makes this work original.]
""",
)


def get_summarization_prompt() -> PromptTemplate:
    return SUMMARIZATION_PROMPT

def get_qa_prompt() -> PromptTemplate:
    return QA_PROMPT

def get_keyword_extraction_prompt() -> PromptTemplate:
    return KEYWORD_EXTRACTION_PROMPT

def get_insight_extraction_prompt() -> PromptTemplate:
    return INSIGHT_EXTRACTION_PROMPT

def get_novelty_detection_prompt() -> PromptTemplate:
    return NOVELTY_DETECTION_PROMPT
