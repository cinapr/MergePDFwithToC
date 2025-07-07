import sys
import fitz  # PyMuPDF
import re


def wrap_text(title, max_width, fontname, fontsize):
    words = title.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        test_width = fitz.get_text_length(test_line, fontname=fontname, fontsize=fontsize)
        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def parse_toc_txt(txt_file):
    toc_data = []
    pattern = re.compile(r"\[(\d+)\]\s*(.*?)\s*\|\s*PAGE\s*(\d+)", re.IGNORECASE)

    with open(txt_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if not match:
                raise ValueError(f"Invalid line format: {line}")
            level = int(match.group(1))
            title = match.group(2).strip()
            page = int(match.group(3))
            display_page = page + 1  # Account for inserted TOC
            link_page = page
            toc_data.append([level, title, display_page, link_page])

    return toc_data


def generate_toc_page(doc, toc_data):
    font_size = 11
    line_spacing = 1.4 * font_size
    max_width = 420
    page_margin_top = 36
    page_margin_left = 72
    max_y = 800

    toc_page = doc.new_page(pno=0)  # First TOC page
    y = page_margin_top + 30
    page_number = 1  # TOC page count

    def new_toc_page():
        nonlocal y, page_number
        page_number += 1
        y = page_margin_top
        return doc.new_page(pno=page_number - 1)

    # Title on first TOC page
    toc_page.insert_text((page_margin_left, page_margin_top), "Table of Contents", fontsize=18, fontname="helv", fill=(0, 0, 0))

    current_page = toc_page

    for level, title, display_page, link_page in toc_data:
        indent = (level - 1) * 20
        wrapped_lines = wrap_text(title, max_width - indent, fontname="helv", fontsize=font_size)

        for i, line in enumerate(wrapped_lines):
            if i == len(wrapped_lines) - 1:
                display_text = f"{line} .......... {display_page}"
            else:
                display_text = line

            pos = (page_margin_left + indent, y)
            current_page.insert_text(pos, display_text, fontsize=font_size, fontname="helv", fill=(0, 0, 1))

            if i == 0:
                text_width = fitz.get_text_length(display_text, fontname="helv", fontsize=font_size)
                rect = fitz.Rect(pos[0], y - line_spacing, pos[0] + text_width, y + (line_spacing * (len(wrapped_lines)-1)))
                current_page.insert_link({
                    "kind": fitz.LINK_GOTO,
                    "page": link_page,
                    "from": rect
                })

            y += line_spacing

            if y > max_y:
                current_page = new_toc_page()



def add_custom_toc(input_pdf, output_pdf, toc_txt):
    doc = fitz.open(input_pdf)
    toc_data = parse_toc_txt(toc_txt)
    generate_toc_page(doc, toc_data)
    doc.save(output_pdf)
    print(f"✅ TOC added: {output_pdf}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage:\n  python nonbookmarked_toc.py input.pdf output.pdf toc.txt")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    toc_txt = sys.argv[3]

    add_custom_toc(input_pdf, output_pdf, toc_txt)
