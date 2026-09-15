import asyncio
from app.latex_executer import render_latex_to_pdf
from pathlib import Path

latex_code = r"""
\documentclass{article}
\begin{document}
Hello World
\end{document}
"""

pdf_path = render_latex_to_pdf(latex_code, Path("generated_pdfs/test.pdf"))
print("Generated:", pdf_path)
