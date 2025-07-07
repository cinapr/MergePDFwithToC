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
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines

def generate_toc_page(doc, original_toc):
    toc_page = doc.new_page(pno=0)
    toc_page.insert_text((72, 36), "Table of Contents", fontsize=18, fontname="helv", fill=(0, 0, 0))

    y = 70
    font_size = 11
    line_spacing = 1.4 * font_size
    max_width = 420  # Width for title wrapping

    for level, title, page_num in original_toc:
        indent = (level - 1) * 20
        wrapped_lines = wrap_text(title, max_width - indent, fontname="helv", fontsize=font_size)

        for i, line in enumerate(wrapped_lines):
            # Only show page number on the last line
            if i == len(wrapped_lines) - 1:
                display_text = f"{line} .......... {page_num}"
            else:
                display_text = line

            pos = (72 + indent, y)
            toc_page.insert_text(pos, display_text, fontsize=font_size, fontname="helv", fill=(0, 0, 1))

            # Add link only to the first line
            if i == 0:
                text_width = fitz.get_text_length(display_text, fontname="helv", fontsize=font_size)
                rect = fitz.Rect(pos[0], y-line_spacing, pos[0] + text_width, y + (line_spacing * (len(wrapped_lines)-1)))
                toc_page.insert_link({
                    "kind": fitz.LINK_GOTO,
                    "page": page_num,  # Already correct
                    "from": rect
                })

            y += line_spacing
            if y > 800:
                # Optional: add new page if needed
                break

def add_toc_to_pdf(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)
    original_toc = doc.get_toc(simple=True)

    # Shift all bookmarks by 1 (to account for inserted TOC page)
    shifted_toc = [[lvl, title, page + 1] for lvl, title, page in original_toc]

    generate_toc_page(doc, original_toc)  # Draw TOC using original page numbers
    doc.set_toc(shifted_toc)              # Update bookmarks with correct pages

    doc.save(output_pdf)

# === MAIN ===
input_pdf = "input.pdf"
output_pdf = "output_with_wrapped_clickable_toc.pdf"
add_toc_to_pdf(input_pdf, output_pdf)
print(f"✅ TOC page added with wrapping + accurate clickable links!\n→ {output_pdf}")
