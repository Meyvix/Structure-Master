"""
StructureMaster - Document Converter
Convert documentation to PDF and Word formats.
"""

import os
import sys
from pathlib import Path


def convert_to_pdf(html_path: Path, output_path: Path) -> bool:
    """
    Convert HTML to PDF using available tools.
    
    Tries multiple methods:
    1. wkhtmltopdf (if installed)
    2. weasyprint (Python library)
    3. pdfkit (Python library)
    """
    html_path = Path(html_path)
    output_path = Path(output_path)
    
    # Method 1: Try wkhtmltopdf
    try:
        import subprocess
        result = subprocess.run(
            ['wkhtmltopdf', '--enable-local-file-access', 
             '--encoding', 'utf-8',
             str(html_path), str(output_path)],
            capture_output=True
        )
        if result.returncode == 0:
            print(f"✅ PDF created with wkhtmltopdf: {output_path}")
            return True
    except FileNotFoundError:
        pass
    
    # Method 2: Try weasyprint
    try:
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(output_path))
        print(f"✅ PDF created with weasyprint: {output_path}")
        return True
    except ImportError:
        pass
    except Exception as e:
        print(f"❌ weasyprint error: {e}")
    
    # Method 3: Try pdfkit
    try:
        import pdfkit
        pdfkit.from_file(str(html_path), str(output_path))
        print(f"✅ PDF created with pdfkit: {output_path}")
        return True
    except ImportError:
        pass
    except Exception as e:
        print(f"❌ pdfkit error: {e}")
    
    print("❌ No PDF converter available.")
    print("   Install one of these:")
    print("   - wkhtmltopdf: https://wkhtmltopdf.org/downloads.html")
    print("   - pip install weasyprint")
    print("   - pip install pdfkit")
    return False


def convert_to_word(html_path: Path, output_path: Path) -> bool:
    """
    Convert HTML to Word document.
    
    Uses python-docx or pypandoc.
    """
    html_path = Path(html_path)
    output_path = Path(output_path)
    
    # Method 1: Try pypandoc
    try:
        import pypandoc
        pypandoc.convert_file(
            str(html_path), 'docx',
            outputfile=str(output_path)
        )
        print(f"✅ Word document created with pypandoc: {output_path}")
        return True
    except ImportError:
        pass
    except Exception as e:
        print(f"❌ pypandoc error: {e}")
    
    # Method 2: Try htmldocx
    try:
        from htmldocx import HtmlToDocx
        from docx import Document
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        doc = Document()
        parser = HtmlToDocx()
        parser.add_html_to_document(html_content, doc)
        doc.save(str(output_path))
        print(f"✅ Word document created with htmldocx: {output_path}")
        return True
    except ImportError:
        pass
    except Exception as e:
        print(f"❌ htmldocx error: {e}")
    
    print("❌ No Word converter available.")
    print("   Install one of these:")
    print("   - pip install pypandoc")
    print("   - pip install python-docx htmldocx")
    return False


def main():
    """Main conversion function."""
    # Paths
    docs_dir = Path(__file__).parent
    
    files_to_convert = [
        ("TUTORIAL_COMPLETE_FA", "راهنمای کامل"),
        ("CODE_EXPLANATION_FA", "توضیح کدها"),
    ]
    
    print("=" * 50)
    print("📄 StructureMaster Document Converter")
    print("=" * 50)
    print()
    
    for base_name, title in files_to_convert:
        html_file = docs_dir / f"{base_name}.html"
        pdf_file = docs_dir / f"{base_name}.pdf"
        docx_file = docs_dir / f"{base_name}.docx"
        
        if not html_file.exists():
            print(f"❌ HTML file not found: {html_file}")
            continue
        
        print(f"\n📖 Converting: {title}")
        print("-" * 40)
        
        # Convert to PDF
        print("🔄 Converting to PDF...")
        convert_to_pdf(html_file, pdf_file)
        
        # Convert to Word
        print("🔄 Converting to Word...")
        convert_to_word(html_file, docx_file)
    
    print("\n" + "=" * 50)
    print("✨ Conversion complete!")
    print()
    print("Files created in docs/ directory:")
    for base_name, title in files_to_convert:
        pdf_file = docs_dir / f"{base_name}.pdf"
        docx_file = docs_dir / f"{base_name}.docx"
        if pdf_file.exists():
            print(f"  📕 {pdf_file.name}")
        if docx_file.exists():
            print(f"  📘 {docx_file.name}")
    
    print()
    print("💡 Alternative: Open HTML files in browser")
    print("   and use Print → Save as PDF")



if __name__ == "__main__":
    main()
