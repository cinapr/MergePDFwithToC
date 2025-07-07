# MergePDFwithToC
Merge PDF with Table of Contents

## Installation

1. Install [JH PDF Merger by qwinsi](https://github.com/qwinsi/jh-pdf-merger)

2. pip install PyMuPDF PyPDF2 reportlab


## How to Use (For Bookmark PDF)
1. Merge PDFs with [JH PDF Merger by qwinsi](https://github.com/qwinsi/jh-pdf-merger). Don't forget to click generate bookmark when merging, so the generated PDF will have proper bookmark

2. Put the generated bookmark in same folder with ```bookmarkedpdf.py```

### Without Custom ToC (ToC contains directly taken from Bookmark section titles)
3. Run : ```python bookmarkedpdf.py input.pdf output.pdf [custom_titles.txt]```
custom_titles.txt is optional. If you don't give it the ToC will generated exactly the same with bookmark title.

### With Custom ToC
3. Filled the ```custom_titles.txt``` with the title of sections that you want to put on Table of Contents. **Make sure line count in the ```custom_titles.txt``` matches the number of bookmarks exactly**.
Example :
```
TITLE 1
TITLE 2
TITLE 3
```

4. Run : ```python bookmarkedpdf.py input.pdf output.pdf [custom_titles.txt]```
custom_titles.txt is optional. If you don't give it the ToC will generated exactly the same with bookmark title.


## How to Use (For Non-Bookmarked PDF)
1. Prepared PDF in the same folder with ```nonbookmarkedpdf.py```

2. Filled the ```custom_titles.txt``` with the title of sections that you want to put on Table of Contents.
The line should represent : ```[SECTION INDENT] [TITLE] | Page [PAGE NO]```
Example :
```
[1] TITLE 1 | Page 1
[2] TITLE 1.1 | Page 3
[2] TITLE 1.2 | Page 4
[3] TITLE 1.2.1 | Page 4
[3] TITLE 1.2.2 | Page 5
[3] TITLE 1.2.3 | Page 6
[1] TITLE 2 | Page 8
[1] TITLE 3 | Page 10
```


