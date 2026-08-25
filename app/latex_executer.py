#!/usr/bin/env python3

from __future__ import annotations

import re as _re
from pathlib import Path
import shutil
import subprocess
import tempfile


LATEX_TIMEOUT = 60


def _find_executable(name: str) -> str | None:
    """Find an executable available on PATH."""
    return shutil.which(name)


def _extract_latex_errors(log: str) -> str:
    """
    Parse a xelatex/pdflatex log and return only the lines that describe
    actual errors — stripping the long package-loading preamble that makes
    the full log hard to read.

    Patterns captured:
      • Lines starting with "!" (TeX fatal errors)
      • Lines matching "Package <name> Error: ..."
      • Lines matching "LaTeX Error: ..."
      • Lines matching "<file>:<line>: ..." (file-line-error format)
      • Lines matching "Undefined control sequence" / "Missing { inserted" etc.
      • The "l.<line> ..." context line that immediately follows an error
    """
    error_patterns = _re.compile(
        r'(?:'
        r'^!.*'                                  # ! Fatal error
        r'|^.*?:\d+: .*'                         # file:line: error  (-file-line-error)
        r'|^Package \S+ Error:.*'                # Package X Error:
        r'|^LaTeX Error:.*'                      # LaTeX Error:
        r'|^Undefined control sequence\.'         # undefined cs
        r'|^Missing \{ inserted\.'               # brace errors
        r'|^Missing \$ inserted\.'
        r'|^Extra \}, or forgotten \\\$\.'
        r'|^Too many \}'
        r'|^Emergency stop\.'
        r'|^l\.\d+.*'                            # l.96 ... context line
        r')',
        _re.MULTILINE,
    )

    matched = error_patterns.findall(log)
    if matched:
        return '\n'.join(line.strip() for line in matched if line.strip())

    # Fallback: return the last 40 lines if nothing matched the patterns
    lines = log.splitlines()
    return '\n'.join(lines[-40:])


def _run_latex(
    latex_engine: str,
    tex_file: Path,
    output_directory: Path,
) -> subprocess.CompletedProcess[str]:

    command = [
        latex_engine,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        "-output-directory",
        str(output_directory),
        str(tex_file),
    ]

    try:
        return subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=LATEX_TIMEOUT,
            check=True,
        )

    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"LaTeX compilation timed out after "
            f"{LATEX_TIMEOUT} seconds."
        ) from exc

    except subprocess.CalledProcessError as exc:

        raw_log = exc.stdout or ""
        concise = _extract_latex_errors(raw_log)

        raise RuntimeError(
            "LaTeX compilation failed.\n\n"
            f"Key errors:\n{concise}\n\n"
            f"Full command: {' '.join(command)}"
        ) from exc



def render_latex_to_pdf(
    latex_source: str,
    output_pdf: str | Path,
) -> Path:
    """
    Compile LaTeX source into a PDF.

    Args:
        latex_source: Complete LaTeX document.
        output_pdf: Destination PDF path.

    Returns:
        Path to generated PDF.
    """

    if not latex_source or not latex_source.strip():
        raise ValueError("LaTeX source cannot be empty.")

    output_pdf = Path(output_pdf).expanduser().resolve()

    # ------------------------------------------------------------
    # Find the LaTeX engine
    # ------------------------------------------------------------
    # xelatex is used instead of pdflatex because generated resumes may
    # include packages like fontspec (custom font handling), which only
    # work under XeTeX or LuaTeX. xelatex also supports everything
    # pdflatex supports here (geometry, hyperref, fontawesome5, etc.),
    # so this is a safe drop-in replacement.

    latex_engine = _find_executable("xelatex")

    if latex_engine is None:
        raise RuntimeError(
            "xelatex was not found on PATH.\n\n"
            "Install TeX Live using:\n"
            "sudo apt install texlive-xetex texlive-latex-extra"
        )

    # ------------------------------------------------------------
    # Temporary compilation directory
    # ------------------------------------------------------------

    with tempfile.TemporaryDirectory(
        prefix="resume_latex_"
    ) as temp_dir:

        temp_path = Path(temp_dir)

        tex_file = temp_path / "document.tex"
        generated_pdf = temp_path / "document.pdf"

        # --------------------------------------------------------
        # Write .tex file
        # --------------------------------------------------------

        tex_file.write_text(
            latex_source,
            encoding="utf-8",
            newline="\n",
        )

        # --------------------------------------------------------
        # First & Second compilation with auto-healing retry
        # --------------------------------------------------------

        current_latex = latex_source
        max_attempts = 3
        first_result = None
        second_result = None

        for attempt in range(max_attempts):
            tex_file.write_text(current_latex, encoding="utf-8", newline="\n")
            try:
                first_result = _run_latex(
                    latex_engine=latex_engine,
                    tex_file=tex_file,
                    output_directory=temp_path,
                )
                second_result = _run_latex(
                    latex_engine=latex_engine,
                    tex_file=tex_file,
                    output_directory=temp_path,
                )
                break
            except RuntimeError as exc:
                err_msg = str(exc)
                if attempt < max_attempts - 1 and "Undefined control sequence" in err_msg:
                    # Extract undefined macro name if present (e.g. \faLinkinelinkedin)
                    undef_match = _re.search(r'\\([A-Za-z]+)', err_msg)
                    if undef_match:
                        bad_cs = f"\\{undef_match.group(1)}"
                        # Strip or replace bad control sequence
                        current_latex = current_latex.replace(bad_cs, "")
                        continue
                raise exc

        # --------------------------------------------------------
        # Verify PDF
        # --------------------------------------------------------

        if not generated_pdf.exists():
            output = second_result.stdout or first_result.stdout

            raise RuntimeError(
                "LaTeX compilation completed but no PDF was generated.\n\n"
                f"Compiler output:\n{output}"
            )

        if generated_pdf.stat().st_size == 0:
            raise RuntimeError(
                "LaTeX compilation generated an empty PDF."
            )

        # --------------------------------------------------------
        # Create output directory
        # --------------------------------------------------------

        output_pdf.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # --------------------------------------------------------
        # Copy PDF
        # --------------------------------------------------------

        shutil.copy2(
            generated_pdf,
            output_pdf,
        )

    return output_pdf

# from pathlib import Path
# from your_module_name import render_latex_to_pdf  # Replace with actual module name

# Your LaTeX document
# latex_document = r"""
# \documentclass[11pt,a4paper]{article}
# \usepackage[margin=0.7in]{geometry}
# \usepackage{enumitem}
# \usepackage{titlesec}
# \usepackage{hyperref}
# \usepackage{fontawesome5}
# \usepackage{xcolor}
# \usepackage{parskip}
# \usepackage{ragged2e}

# \definecolor{primary}{HTML}{2C3E50}
# \definecolor{secondary}{HTML}{34495E}
# \definecolor{accent}{HTML}{3498DB}
# \definecolor{text}{HTML}{2C3E50}
# \definecolor{muted}{HTML}{7F8C8D}

# \hypersetup{
#     colorlinks=true,
#     urlcolor=accent,
#     linkcolor=primary,
#     pdfauthor={},
#     pdfsubject={Software Developer Resume},
#     pdfkeywords={Python, FastAPI, SQL, Docker, Software Development}
# }

# \titleformat{\section}{\large\bfseries\color{primary}}{}{0em}{}[\titlerule]
# \titlespacing{\section}{0pt}{12pt}{6pt}

# \setlist[itemize]{leftmargin=*, topsep=2pt, itemsep=2pt, label=\textbullet}
# \setlist[description]{leftmargin=!, labelwidth=2.5cm, font=\normalfont\bfseries\color{secondary}}

# \pagestyle{empty}
# \raggedbottom

# \begin{document}

# \begin{center}
#     {\LARGE \bfseries \color{primary} Full Name}\\[6pt]
#     {\color{muted} \faMapMarker\hspace{2pt} City, Country \quad 
#     \faPhone\hspace{2pt} +XX XXX XXXX \quad 
#     \faEnvelope\hspace{2pt} \href{mailto:email@example.com}{email@example.com} \quad 
#     \faLinkedin\hspace{2pt} \href{https://linkedin.com/in/username}{linkedin.com/in/username} \quad 
#     \faGithub\hspace{2pt} \href{https://github.com/username}{github.com/username}}
# \end{center}

# \vspace{4pt}

# \section*{Professional Summary}
# \noindent Junior Software Developer with a Computer Science degree and approximately two years of professional experience. Practical exposureto Python, FastAPI (one project), SQL, and Docker. Familiar with LangGraph through tutorial work. Strong foundation in clean code principles,debugging, and collaborative problem-solving. Eager to contribute and grow in a backend-focused development role.

# \section*{Technical Skills}
# \begin{description}
#     \item[Languages] Python (proficient), SQL (basic), HTML/CSS, JavaScript (basics)
#     \item[Frameworks] FastAPI (project-level experience), LangGraph (tutorial-level)
#     \item[Tools] Docker (basic usage), Git, VS Code, Linux CLI
#     \item[Databases] PostgreSQL (basic), SQLite
#     \item[Concepts] REST APIs, Clean Code, Debugging, Unit Testing (pytest), Agile/Scrum basics
# \end{description}

# \section*{Experience}
# \noindent \textbf{Software Developer Intern / Junior Developer} \hfill \textit{Month 20XX -- Present}\\
# \noindent \textit{Company Name, Location}\\
# \begin{itemize}
#     \item Contributed to a small FastAPI-based backend service: implemented CRUD endpoints, integrated with PostgreSQL, and wrote basic unit tests.
#     \item Wrote and maintained SQL queries for data retrieval and reporting; optimized a few slow queries under supervision.
#     \item Used Docker to containerize the development environment; built and ran images locally.
#     \item Collaborated in a small team using Git (feature branches, pull requests) and participated in daily stand-ups.
#     \item Debugged production issues, added logging, and improved error handling in existing Python modules.
# \end{itemize}

# \vspace{4pt}
# \noindent \textbf{Relevant Project: FastAPI Task Manager} \hfill \textit{Personal / Academic}\\
# \begin{itemize}
#     \item Designed and built a REST API with FastAPI for task management (create, read, update, delete, status transitions).
#     \item Implemented JWT-based authentication and role-based access control.
#     \item Used SQLAlchemy with PostgreSQL; wrote migrations with Alembic.
#     \item Containerized the application with Docker and Docker Compose for local development.
#     \item Achieved ~80\% test coverage with pytest; documented endpoints with OpenAPI/Swagger.
# \end{itemize}

# \vspace{4pt}
# \noindent \textbf{Learning Exercise: LangGraph Agent Tutorial} \hfill \textit{Self-directed}\\
# \begin{itemize}
#     \item Completed the official LangGraph tutorial to build a simple ReAct-style agent with tool use.
#     \item Explored state graphs, conditional edges, and checkpointing concepts.
#     \item Gained familiarity with LangChain ecosystem basics (LLM integration, prompt templates).
# \end{itemize}

# \section*{Education}
# \noindent \textbf{Bachelor of Science in Computer Science} \hfill \textit{20XX -- 20XX}\\
# \noindent \textit{University Name, Location}\\
# Relevant coursework: Data Structures \& Algorithms, Databases, Operating Systems, Computer Networks, Software Engineering, Object-Oriented Programming.

# \section*{Additional}
# \begin{itemize}
#     \item Strong analytical mindset; enjoys reading source code to understand internals.
#     \item Quick learner — comfortable picking up new libraries and frameworks via documentation.
#     \item Effective communicator in cross-functional settings; values code reviews and knowledge sharing.
#     \item English: Professional working proficiency.
# \end{itemize}

# \end{document}
# """

# # Render to PDF
# try:
#     pdf_path = render_latex_to_pdf(
#         latex_source=latex_document,
#         output_pdf = Path.home() / "Downloads" / "document.pdf"
#     )
#     print(f"PDF successfully created at: {pdf_path}")
# except Exception as e:
#     print(f"Error: {e}")