#!/usr/bin/env python3
"""
Local xelatex PDF compiler.
Compiles a LaTeX source string to a PDF using xelatex (preferred) or pdflatex.
All E2B cloud sandbox code has been removed — local compilation only.
"""
from __future__ import annotations

import logging
import re as _re
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

LATEX_TIMEOUT = 60          # seconds per xelatex run
MAX_LATEX_RUNS = 2          # run twice to resolve cross-references


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _find_executable(name: str) -> str | None:
    return shutil.which(name)


_ERROR_RE = _re.compile(
    r'(?:'
    r'^!.*'
    r'|^.*?:\d+: .*'
    r'|^Package \S+ Error:.*'
    r'|^LaTeX Error:.*'
    r'|^Undefined control sequence\.'
    r'|^Missing \{ inserted\.'
    r'|^Missing \$ inserted\.'
    r'|^Extra \}, or forgotten \\\$\.'
    r'|^Too many \}'
    r'|^Emergency stop\.'
    r'|^l\.\d+.*'
    r')',
    _re.MULTILINE,
)


def _extract_latex_errors(log: str) -> str:
    """Return only the error lines from a xelatex log."""
    lines = _ERROR_RE.findall(log)
    return "\n".join(lines[:30]) if lines else log[-2000:]


def _run_xelatex(engine: str, tex_file: Path, out_dir: Path) -> subprocess.CompletedProcess:
    """Run xelatex/pdflatex once and return the result."""
    return subprocess.run(
        [
            engine,
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={out_dir}",
            str(tex_file),
        ],
        capture_output=True,
        text=True,
        timeout=LATEX_TIMEOUT,
        cwd=str(out_dir),
        stdin=subprocess.DEVNULL,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def render_latex_to_pdf(
    latex_source: str,
    output_pdf: str | Path,
) -> Path:
    """
    Compile *latex_source* to a PDF at *output_pdf* using the best available
    local LaTeX engine (xelatex → pdflatex).

    Raises RuntimeError with a concise error excerpt on failure.
    """
    if not latex_source or not latex_source.strip():
        raise ValueError("LaTeX source cannot be empty.")

    output_pdf = Path(output_pdf).expanduser().resolve()

    engine = _find_executable("xelatex") or _find_executable("pdflatex")
    if engine is None:
        raise RuntimeError(
            "No LaTeX engine found on PATH. "
            "Install TeX Live: apt-get install -y texlive-xetex texlive-fonts-recommended texlive-latex-extra"
        )

    with tempfile.TemporaryDirectory(prefix="resume_latex_") as tmp:
        tmp_path = Path(tmp)
        tex_file = tmp_path / "document.tex"
        pdf_file = tmp_path / "document.pdf"

        tex_file.write_text(latex_source, encoding="utf-8", newline="\n")

        last_result = None
        for run_num in range(1, MAX_LATEX_RUNS + 1):
            try:
                last_result = _run_xelatex(engine, tex_file, tmp_path)
            except subprocess.TimeoutExpired:
                raise RuntimeError(
                    f"LaTeX compilation timed out after {LATEX_TIMEOUT}s."
                )

            if last_result.returncode == 0 and pdf_file.exists():
                # Success on this run — no need to keep going if PDF is valid
                break

        # Final check
        if not pdf_file.exists() or pdf_file.stat().st_size == 0:
            raw_log = (last_result.stdout or "") + "\n" + (last_result.stderr or "")
            # Also try reading the .log file for more detail
            log_file = tmp_path / "document.log"
            if log_file.exists():
                raw_log += "\n" + log_file.read_text(encoding="utf-8", errors="replace")
            concise = _extract_latex_errors(raw_log)
            raise RuntimeError(
                f"LaTeX compilation failed ({engine}).\n\n"
                f"Relevant errors:\n{concise}"
            )

        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf_file, output_pdf)
        logger.info("PDF compiled successfully → %s", output_pdf)
        return output_pdf
