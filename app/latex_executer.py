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


def _parse_detailed_error(log: str, tex_file: Path) -> str:
    """
    Extracts detailed error information including source context.
    """
    lines = log.splitlines()
    error_line = None
    error_msg = ""
    
    # Try to find file-line-error
    for line in lines:
        if ".tex:" in line and "Error" not in error_msg:
            match = _re.search(r'\.tex:(\d+):\s*(.*)', line)
            if match:
                error_line = int(match.group(1))
                error_msg = match.group(2)
                break
        elif line.startswith("!"):
            error_msg = line
            # Often the next lines have l.<number>
            
    if not error_line:
        for line in lines:
            match = _re.search(r'^l\.(\d+)', line)
            if match:
                error_line = int(match.group(1))
                if not error_msg:
                    error_msg = line
                break

    if not error_msg:
        # Fallback to concise errors
        return _extract_latex_errors(log)

    # Read context from tex_file
    context_str = ""
    source_line_str = ""
    if error_line and tex_file.exists():
        try:
            with open(tex_file, 'r', encoding='utf-8') as f:
                tex_lines = f.readlines()
            
            start_idx = max(0, error_line - 3)
            end_idx = min(len(tex_lines), error_line + 2)
            
            context_lines = []
            for i in range(start_idx, end_idx):
                prefix = "-> " if i + 1 == error_line else "   "
                line_content = tex_lines[i].rstrip('\n')
                context_lines.append(f"{prefix}{i+1:3d} | {line_content}")
                if i + 1 == error_line:
                    source_line_str = line_content
                    
            context_str = "\n" + "\n".join(context_lines)
        except Exception:
            context_str = "\n[Could not read source file for context]"
            
    # Try to provide a human-readable explanation
    explanation = "Check for unescaped special characters (e.g., &, %, $, #, _) or malformed LaTeX commands."
    if "Misplaced alignment tab character" in error_msg:
        explanation = "Unescaped '&' found. '&' is used for alignment in tables. Literal ampersands must be written as '\\&'."
    elif "Undefined control sequence" in error_msg:
        explanation = "A LaTeX command was misspelled or is missing a required package."
    elif "Missing $ inserted" in error_msg or "Missing { inserted" in error_msg:
        explanation = "Unescaped special character (like '_' or '^') which LaTeX thinks starts math mode, or unmatched braces."
        
    report = [
        "LaTeX compilation failed.",
        "",
        f"File: {tex_file.name}",
        f"Line: {error_line if error_line else 'Unknown'}",
        f"Error: {error_msg.strip('! ')}",
        "",
        "Source Context:" + (context_str if context_str else " None available"),
        "",
        "Possible cause / Suggested correction:",
        explanation
    ]
    
    return "\n".join(report)


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
        concise = _parse_detailed_error(raw_log, tex_file)

        raise RuntimeError(
            f"{concise}\n\n"
            f"Full command: {' '.join(command)}"
        ) from exc



def render_latex_to_pdf(
    latex_source: str,
    output_pdf: str | Path,
) -> Path:
    """
    Compile LaTeX source into a PDF using E2B, falling back to local execution.
    """
    if not latex_source or not latex_source.strip():
        raise ValueError("LaTeX source cannot be empty.")

    output_pdf = Path(output_pdf).expanduser().resolve()

    # ──────────────────────────────────────────────────────────────────────────
    # Try E2B cloud sandbox (e2b >= 2.x API)
    # ──────────────────────────────────────────────────────────────────────────
    try:
        from app.config import settings
        import e2b

        if settings.e2b_api_key:
            sandbox = None
            try:
                # e2b v2: Sandbox.create() is the factory classmethod
                # 'template' is the sandbox template id or name
                sandbox = e2b.Sandbox.create(
                    template="latex-resume-env",
                    api_key=settings.e2b_api_key,
                    timeout=LATEX_TIMEOUT + 30,
                )

                # Write the .tex file
                sandbox.files.write("/home/user/document.tex", latex_source)

                # Run xelatex — returns a CommandHandle; call .wait() for result
                handle = sandbox.commands.run(
                    "xelatex -interaction=nonstopmode -halt-on-error /home/user/document.tex",
                    cwd="/home/user",
                    timeout=float(LATEX_TIMEOUT),
                )
                result = handle.wait()

                if result.exit_code != 0:
                    raw_log = (result.stdout or "") + "\n" + (result.stderr or "")
                    tex_path = Path("/home/user/document.tex")
                    concise = _parse_detailed_error(raw_log, tex_path)
                    raise RuntimeError(f"E2B LaTeX compilation failed:\n{concise}")

                # Read the generated PDF — use format='bytes' (no read_bytes in v2)
                pdf_bytes = sandbox.files.read("/home/user/document.pdf", format="bytes")

                output_pdf.parent.mkdir(parents=True, exist_ok=True)
                with open(output_pdf, "wb") as f:
                    f.write(pdf_bytes)

                return output_pdf

            finally:
                if sandbox is not None:
                    try:
                        sandbox.kill()
                    except Exception:
                        pass

    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(
            f"E2B compilation failed or is unconfigured: {e}. Falling back to local execution."
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Fallback to local LaTeX execution
    # ──────────────────────────────────────────────────────────────────────────
    latex_engine = _find_executable("xelatex") or _find_executable("pdflatex")
    if latex_engine is None:
        raise RuntimeError(
            "E2B compilation failed and no local xelatex/pdflatex was found on PATH.\n\n"
            "Install TeX Live locally or configure E2B_API_KEY properly."
        )

    with tempfile.TemporaryDirectory(prefix="resume_latex_") as temp_dir:
        temp_path = Path(temp_dir)
        tex_file = temp_path / "document.tex"
        generated_pdf = temp_path / "document.pdf"

        tex_file.write_text(latex_source, encoding="utf-8", newline="\n")

        result = _run_latex(
            latex_engine=latex_engine,
            tex_file=tex_file,
            output_directory=temp_path,
        )

        if not generated_pdf.exists():
            raise RuntimeError(
                "LaTeX compilation completed but no PDF was generated.\n\n"
                f"Compiler output:\n{result.stdout}"
            )

        if generated_pdf.stat().st_size == 0:
            raise RuntimeError("LaTeX compilation generated an empty PDF.")

        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(generated_pdf, output_pdf)

    return output_pdf