import sys
import fitz  # PyMuPDF


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


def generate_toc_page(doc, toc_data):
    """
    toc_data: list of [level, title, display_page, link_page]
    """
    toc_page = doc.new_page(pno=0)  # Insert TOC page at beginning
    toc_page.insert_text((72, 36), "Table of Contents", fontsize=18, fontname="helv", fill=(0, 0, 0))

    y = 70
    font_size = 11
    line_spacing = 1.4 * font_size
    max_width = 420  # max width for wrapped text

    for level, title, display_page, link_page in toc_data:
        indent = (level - 1) * 20
        wrapped_lines = wrap_text(title, max_width - indent, fontname="helv", fontsize=font_size)

        for i, line in enumerate(wrapped_lines):
            # Show page number only on last line
            if i == len(wrapped_lines) - 1:
                display_text = f"{line} .......... {display_page-1}"
            else:
                display_text = line

            pos = (72 + indent, y)
            toc_page.insert_text(pos, display_text, fontsize=font_size, fontname="helv", fill=(0, 0, 1))

            # Add clickable link only on first line
            if i == 0:
                text_width = fitz.get_text_length(display_text, fontname="helv", fontsize=font_size)
                #rect = fitz.Rect(pos[0], y, pos[0] + text_width, y + line_spacing)
                rect = fitz.Rect(pos[0], y-line_spacing, pos[0] + text_width, y + (line_spacing * (len(wrapped_lines)-1)))
                toc_page.insert_link({
                    "kind": fitz.LINK_GOTO,
                    "page": link_page-1,
                    "from": rect
                })

            y += line_spacing
            if y > 800:
                # Optionally add more pages if TOC too long
                break


def add_toc_to_pdf(input_pdf, output_pdf, toc_titles_file=None):
    doc = fitz.open(input_pdf)
    original_toc = doc.get_toc(simple=True)  # list of [level, title, page]

    # Load custom titles if file given
    if toc_titles_file:
        with open(toc_titles_file, encoding="utf-8") as f:
            custom_titles = [line.strip() for line in f if line.strip()]

        if len(custom_titles) != len(original_toc):
            raise ValueError(f"TXT title count ({len(custom_titles)}) does not match bookmark count ({len(original_toc)})")

        # Compose TOC data: [level, title, displayed_page, link_page]
        toc_data = []
        for i, (level, _, page) in enumerate(original_toc):
            display_page = page + 1         # visible page number (1-based)
            link_page = page + 1            # page index shifted by TOC insertion
            toc_data.append([level, custom_titles[i], display_page, link_page])
    else:
        toc_data = []
        for level, title, page in original_toc:
            display_page = page + 1
            link_page = page + 1
            toc_data.append([level, title, display_page, link_page])

    # Generate TOC page at beginning
    generate_toc_page(doc, toc_data)

    # Update bookmarks (set_toc expects [level, title, page])
    doc.set_toc([[level, title, link_page] for level, title, display_page, link_page in toc_data])

    doc.save(output_pdf)
    print(f"✅ TOC added with clickable links: {output_pdf}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:\n  python bookmarkedpdf.py input.pdf output.pdf [toc_titles.txt]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    toc_titles_file = sys.argv[3] if len(sys.argv) > 3 else None

    add_toc_to_pdf(input_pdf, output_pdf, toc_titles_file)
