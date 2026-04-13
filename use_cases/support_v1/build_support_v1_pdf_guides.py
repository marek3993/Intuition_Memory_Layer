from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


PAGE_WIDTH = 1240
PAGE_HEIGHT = 1754
MARGIN_X = 110
MARGIN_TOP = 110
MARGIN_BOTTOM = 120
FOOTER_HEIGHT = 40
LINE_GAP = 6
SECTION_GAP = 18
LIST_INDENT = 34
FONT_DIR = Path(r"C:\Windows\Fonts")
BODY_FONT_PATH = FONT_DIR / "arial.ttf"
BOLD_FONT_PATH = FONT_DIR / "arialbd.ttf"
BUILD_COMMAND = "python use_cases/support_v1/build_support_v1_pdf_guides.py"


@dataclass(frozen=True)
class GuideSpec:
    source_path: Path
    output_path: Path


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def parse_blocks(markdown_text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            blocks.append(("paragraph", " ".join(line.strip() for line in paragraph_lines)))
            paragraph_lines.clear()

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            blocks.append(("title", stripped[2:].strip()))
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            blocks.append(("heading", stripped[3:].strip()))
            continue
        if stripped.startswith("- "):
            flush_paragraph()
            blocks.append(("bullet", stripped[2:].strip()))
            continue
        paragraph_lines.append(stripped)

    flush_paragraph()
    return blocks


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def line_height(draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont) -> int:
    bbox = draw.textbbox((0, 0), "Ag", font=font)
    return (bbox[3] - bbox[1]) + LINE_GAP


def break_long_word(
    draw: ImageDraw.ImageDraw,
    word: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    chunks: list[str] = []
    current = ""
    for character in word:
        candidate = current + character
        if current and text_width(draw, candidate, font) > max_width:
            chunks.append(current)
            current = character
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    wrapped: list[str] = []
    current = ""
    for word in words:
        if text_width(draw, word, font) > max_width:
            if current:
                wrapped.append(current)
                current = ""
            wrapped.extend(break_long_word(draw, word, font, max_width))
            continue

        candidate = word if not current else f"{current} {word}"
        if text_width(draw, candidate, font) <= max_width:
            current = candidate
        else:
            wrapped.append(current)
            current = word

    if current:
        wrapped.append(current)
    return wrapped


def new_page() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
    return image, ImageDraw.Draw(image)


def add_footer(pages: Iterable[Image.Image], footer_font: ImageFont.FreeTypeFont) -> None:
    pages = list(pages)
    total_pages = len(pages)
    for index, page in enumerate(pages, start=1):
        draw = ImageDraw.Draw(page)
        footer_text = f"Page {index} of {total_pages}"
        width = text_width(draw, footer_text, footer_font)
        x = PAGE_WIDTH - MARGIN_X - width
        y = PAGE_HEIGHT - MARGIN_BOTTOM + 20
        draw.text((x, y), footer_text, fill="#666666", font=footer_font)


def render_pdf(markdown_text: str, output_path: Path) -> None:
    title_font = load_font(BOLD_FONT_PATH, 34)
    heading_font = load_font(BOLD_FONT_PATH, 22)
    body_font = load_font(BODY_FONT_PATH, 16)
    footer_font = load_font(BODY_FONT_PATH, 12)

    pages: list[Image.Image] = []
    page, draw = new_page()
    y = MARGIN_TOP
    content_bottom = PAGE_HEIGHT - MARGIN_BOTTOM - FOOTER_HEIGHT

    def start_new_page() -> None:
        nonlocal page, draw, y
        pages.append(page)
        page, draw = new_page()
        y = MARGIN_TOP

    def ensure_space(required_height: int) -> None:
        nonlocal y
        if y + required_height <= content_bottom:
            return
        start_new_page()

    def draw_lines(
        lines: list[str],
        font: ImageFont.FreeTypeFont,
        x: int,
        fill: str = "black",
        prefix: str = "",
    ) -> None:
        nonlocal y
        line_step = line_height(draw, font)
        prefix_width = text_width(draw, prefix, font) if prefix else 0
        first_line = True
        for line in lines:
            if y + line_step > content_bottom:
                start_new_page()
                line_step = line_height(draw, font)
                first_line = True
            if prefix and first_line:
                draw.text((x, y), prefix, fill=fill, font=font)
                draw.text((x + prefix_width, y), line, fill=fill, font=font)
            else:
                draw.text((x + (prefix_width if prefix else 0), y), line, fill=fill, font=font)
            y += line_step
            first_line = False

    for block_type, text in parse_blocks(markdown_text):
        if block_type == "title":
            block_lines = wrap_text(draw, text, title_font, PAGE_WIDTH - (2 * MARGIN_X))
            block_height = (len(block_lines) * line_height(draw, title_font)) + SECTION_GAP
            ensure_space(block_height)
            for line in block_lines:
                width = text_width(draw, line, title_font)
                draw.text(((PAGE_WIDTH - width) / 2, y), line, fill="black", font=title_font)
                y += line_height(draw, title_font)
            y += SECTION_GAP
            continue

        if block_type == "heading":
            block_lines = wrap_text(draw, text, heading_font, PAGE_WIDTH - (2 * MARGIN_X))
            block_height = (len(block_lines) * line_height(draw, heading_font)) + SECTION_GAP
            ensure_space(block_height + line_height(draw, body_font) * 2)
            for line in block_lines:
                draw.text((MARGIN_X, y), line, fill="black", font=heading_font)
                y += line_height(draw, heading_font)
            y += SECTION_GAP
            continue

        if block_type == "bullet":
            prefix = "• "
            text_width_available = PAGE_WIDTH - (2 * MARGIN_X) - LIST_INDENT
            block_lines = wrap_text(draw, text, body_font, text_width_available)
            ensure_space((len(block_lines) * line_height(draw, body_font)) + SECTION_GAP)
            draw_lines(block_lines, body_font, MARGIN_X, prefix=prefix)
            y += SECTION_GAP
            continue

        block_lines = wrap_text(draw, text, body_font, PAGE_WIDTH - (2 * MARGIN_X))
        ensure_space((len(block_lines) * line_height(draw, body_font)) + SECTION_GAP)
        draw_lines(block_lines, body_font, MARGIN_X)
        y += SECTION_GAP

    pages.append(page)
    add_footer(pages, footer_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(
        output_path,
        "PDF",
        resolution=150.0,
        save_all=True,
        append_images=pages[1:],
    )


def main() -> None:
    support_dir = Path(__file__).resolve().parent
    repo_root = support_dir.parent.parent
    guides = [
        GuideSpec(
            source_path=support_dir / "SUPPORT_V1_MASTER_GUIDE_FOR_PDF.md",
            output_path=support_dir / "artifacts" / "support_v1_master_guide.pdf",
        ),
        GuideSpec(
            source_path=support_dir / "SUPPORT_V1_MASTER_GUIDE_SK_FOR_PDF.md",
            output_path=support_dir / "artifacts" / "support_v1_master_guide_sk.pdf",
        ),
    ]

    for guide in guides:
        markdown_text = guide.source_path.read_text(encoding="utf-8")
        render_pdf(markdown_text, guide.output_path)

    print("Built support_v1 PDF guides.")
    print()
    print("Source guide paths:")
    for guide in guides:
        print(f"- {guide.source_path.relative_to(repo_root).as_posix()}")
    print()
    print("Output PDF paths:")
    for guide in guides:
        print(f"- {guide.output_path.relative_to(repo_root).as_posix()}")
    print()
    print(f"PowerShell command: {BUILD_COMMAND}")
    print(
        "Summary: Adds one explicit support_v1 PDF builder that renders the two print-friendly "
        "master guide markdown sources into simple readable PDF artifacts."
    )


if __name__ == "__main__":
    main()
