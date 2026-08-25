import asyncio
from app.llm import llm
from app.schemas.resume import AnalyzerOutput
structured_llm = llm.models[0].with_structured_output(AnalyzerOutput)
print("hasattr ainvoke:", hasattr(structured_llm, "ainvoke"))
