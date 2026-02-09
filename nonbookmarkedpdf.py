import sys
import fitz  # PyMuPDF
import re


# -------------------------------------------------
# Text wrapping (UNCHANGED)
# -------------------------------------------------

def wrap_text(title, max_width, fontname, fontsize):
    words = title.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        test_width = fitz.get_text_length(
            test_line, fontname=fontname, fontsize=fontsize
        )

        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


# -------------------------------------------------
# Parse TOC TXT (STRICT, FAIL FAST)
# -------------------------------------------------

def parse_toc_txt(txt_file):
    toc_data = []
    pattern = re.compile(r"\[(\d+)\]\s*(.*?)\s*\|\s*PAGE\s*(\d+)", re.IGNORECASE)

    with open(txt_file, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            match = pattern.match(line)
            if not match:
                raise ValueError(
                    f"Invalid TOC format at line {lineno}:\n"
                    f"{line}\n\n"
                    f"Expected:\n"
                    f"[level] Title | PAGE number"
                )

            level = int(match.group(1))
            title = match.group(2).strip()
            page = int(match.group(3))  # 1-based from TXT

            toc_data.append((level, title, page))

    return toc_data


# -------------------------------------------------
# Estimate TOC page count (UNCHANGED LOGIC)
# -------------------------------------------------

def estimate_toc_pages(toc_data):
    font_size = 11
    line_spacing = 1.4 * font_size
    max_width = 420
    max_y = 800
    y = 36 + 30
    pages = 1

    for level, title, _ in toc_data:
        indent = (level - 1) * 20
        wrapped = wrap_text(title, max_width - indent, "helv", font_size)

        for _ in wrapped:
            y += line_spacing
            if y > max_y:
                pages += 1
                y = 36

    return pages


# -------------------------------------------------
# Generate TOC pages (ONLY PAGE MATH CHANGED)
# -------------------------------------------------

def generate_toc_pages(doc, toc_data, insert_at, cover_pages, toc_pages):
    font_size = 11
    line_spacing = 1.4 * font_size
    max_width = 420
    page_margin_top = 36
    page_margin_left = 72
    max_y = 800

    page_offset = cover_pages + toc_pages

    page_index = insert_at
    y = page_margin_top + 30

    page = doc.new_page(pno=page_index)

    page.insert_text(
        (page_margin_left, page_margin_top),
        "Table of Contents",
        fontsize=18,
        fontname="helv",
        fill=(0, 0, 0),
    )

    for level, title, txt_page in toc_data:
        indent = (level - 1) * 20

        # TXT page is 1-based
        display_page = txt_page + page_offset
        link_page = (txt_page - 1) + page_offset

        if link_page < 0 or link_page >= doc.page_count:
            raise ValueError(
                f"TOC link out of range:\n"
                f"Title: {title}\n"
                f"PAGE {txt_page} -> final page {link_page}\n"
                f"Document has {doc.page_count} pages"
            )

        wrapped = wrap_text(title, max_width - indent, "helv", font_size)

        for i, line in enumerate(wrapped):
            if i == len(wrapped) - 1:
                text = f"{line} .......... {display_page}"
            else:
                text = line

            pos = (page_margin_left + indent, y)

            page.insert_text(
                pos, text, fontsize=font_size, fontname="helv", fill=(0, 0, 1)
            )

            if i == 0:
                text_width = fitz.get_text_length(
                    text, fontname="helv", fontsize=font_size
                )

                rect = fitz.Rect(
                    pos[0],
                    y - line_spacing,
                    pos[0] + text_width,
                    y + (line_spacing * (len(wrapped) - 1)),
                )

                page.insert_link({
                    "kind": fitz.LINK_GOTO,
                    "page": link_page,
                    "from": rect,
                })

            y += line_spacing

            if y > max_y:
                page_index += 1
                page = doc.new_page(pno=page_index)
                y = page_margin_top


# -------------------------------------------------
# Add cover (UNCHANGED)
# -------------------------------------------------

def add_cover_if_any(doc, cover_pdf):
    if not cover_pdf:
        return 0

    cover_doc = fitz.open(cover_pdf)
    count = cover_doc.page_count
    doc.insert_pdf(cover_doc, start_at=0)
    cover_doc.close()

    return count


# -------------------------------------------------
# Main
# -------------------------------------------------

def add_custom_toc(input_pdf, output_pdf, toc_txt, cover_pdf=None):
    doc = fitz.open(input_pdf)

    toc_data = parse_toc_txt(toc_txt)

    cover_pages = add_cover_if_any(doc, cover_pdf)
    toc_pages = estimate_toc_pages(toc_data)

    generate_toc_pages(
        doc,
        toc_data,
        insert_at=cover_pages,
        cover_pages=cover_pages,
        toc_pages=toc_pages,
    )

    doc.save(output_pdf)
    print(f"✅ TOC added: {output_pdf}")


# -------------------------------------------------
# CLI
# -------------------------------------------------

if __name__ == "__main__":
    try:
        if len(sys.argv) not in (4, 5):
            print("Usage:\n  python nonbookmarkedpdf.py input.pdf output.pdf toc.txt [cover.pdf]")
            sys.exit(1)

        input_pdf = sys.argv[1]
        output_pdf = sys.argv[2]
        toc_txt = sys.argv[3]
        cover_pdf = sys.argv[4] if len(sys.argv) == 5 else None

        add_custom_toc(input_pdf, output_pdf, toc_txt, cover_pdf)

    except Exception as e:
        print("\n❌ ERROR:", e)
        sys.exit(1)
