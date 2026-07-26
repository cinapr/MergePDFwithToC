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


def calculate_toc_pages(titles, levels):
    """Simulates the layout to find out exactly how many TOC pages we need."""
    y = 70
    font_size = 11
    line_spacing = 1.4 * font_size
    max_width = 420
    pages = 1
    
    for title, level in zip(titles, levels):
        indent = (level - 1) * 20
        wrapped_lines = wrap_text(title, max_width - indent, fontname="helv", fontsize=font_size)
        
        block_height = len(wrapped_lines) * line_spacing
        
        # If this block pushes us past the bottom of the page, count a new page
        if y + block_height > 800:
            pages += 1
            y = 70
            
        y += block_height
        
    return pages


def generate_toc_pages(doc, toc_data):
    """
    Generates as many TOC pages as needed and inserts them at the start.
    """
    current_toc_page = 0
    toc_page = doc.new_page(pno=current_toc_page)
    toc_page.insert_text((72, 36), "Table of Contents", fontsize=18, fontname="helv", fill=(0, 0, 0))

    y = 70
    font_size = 11
    line_spacing = 1.4 * font_size
    max_width = 420 

    for level, title, display_page, target_index in toc_data:
        indent = (level - 1) * 20
        wrapped_lines = wrap_text(title, max_width - indent, fontname="helv", fontsize=font_size)
        
        block_height = len(wrapped_lines) * line_spacing
        
        # Create a new TOC page if we run out of vertical space
        if y + block_height > 800:
            current_toc_page += 1
            toc_page = doc.new_page(pno=current_toc_page)
            y = 70 
            
        for i, line in enumerate(wrapped_lines):
            # Show page number only on the last line of a wrapped title
            if i == len(wrapped_lines) - 1:
                display_text = f"{line} .......... {display_page}"
            else:
                display_text = line

            pos = (72 + indent, y)
            toc_page.insert_text(pos, display_text, fontsize=font_size, fontname="helv", fill=(0, 0, 1))

            # Add clickable link only on the first line
            if i == 0:
                text_width = fitz.get_text_length(display_text, fontname="helv", fontsize=font_size)
                rect = fitz.Rect(pos[0], y - line_spacing, pos[0] + text_width, y + (line_spacing * (len(wrapped_lines)-1)))
                toc_page.insert_link({
                    "kind": fitz.LINK_GOTO,
                    "page": target_index,  # 0-based index for the actual PDF engine
                    "from": rect
                })

            y += line_spacing


def add_toc_to_pdf(input_pdf, output_pdf, toc_titles_file=None):
    doc = fitz.open(input_pdf)
    original_toc = doc.get_toc(simple=True)  # Returns list of [level, title, 1-based page]

    levels = [item[0] for item in original_toc]
    
    # Load custom titles if file given
    if toc_titles_file:
        with open(toc_titles_file, encoding="utf-8") as f:
            titles_to_use = [line.strip() for line in f if line.strip()]

        if len(titles_to_use) != len(original_toc):
            raise ValueError(f"TXT title count ({len(titles_to_use)}) does not match bookmark count ({len(original_toc)})")
    else:
        titles_to_use = [item[1] for item in original_toc]

    # 1. Figure out exactly how many pages the TOC will take
    toc_page_count = calculate_toc_pages(titles_to_use, levels)

    # 2. Compose TOC data with dynamic page shifts
    toc_data = []
    for i, (level, _, original_1based_page) in enumerate(original_toc):
        # The page number printed on the TOC
        display_page = original_1based_page 
        
        # The physical index where the page will live after inserting TOC pages (0-based)
        target_index = (original_1based_page - 1) + toc_page_count 
        
        toc_data.append([level, titles_to_use[i], display_page, target_index])

    # 3. Create a completely blank new document
    new_doc = fitz.open()

    # 4. Copy all pages from the corrupted PDF into the clean new one FIRST
    new_doc.insert_pdf(doc)

    # 5. Generate TOC pages at the beginning of the new document
    generate_toc_pages(new_doc, toc_data)

    # 6. Update bookmarks (set_toc expects 1-based page numbers)
    new_doc.set_toc([[level, title, target_index + 1] for level, title, display_page, target_index in toc_data])

    # 7. Save the clean document
    new_doc.save(output_pdf, garbage=4)
    
    new_doc.close()
    doc.close()
    
    print(f"✅ TOC added with clickable links: {output_pdf}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:\n  python bookmarkedpdf.py input.pdf output.pdf [toc_titles.txt]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    toc_titles_file = sys.argv[3] if len(sys.argv) > 3 else None

    add_toc_to_pdf(input_pdf, output_pdf, toc_titles_file)