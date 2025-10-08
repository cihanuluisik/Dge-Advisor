#!/usr/bin/env python3
import os, argparse
from pathlib import Path
from docling.document_converter import DocumentConverter
from tqdm import tqdm

class MDConverter:
    def __init__(self, docs_dir: str, md_dir: str, force: bool = False):
        self.docs_dir = Path(docs_dir)
        self.md_dir = Path(md_dir)
        self.converter = DocumentConverter()
        self.force = force
    
    def _get_files_to_process(self):
        files_to_process = []
        for file_path in self.docs_dir.iterdir():
            if not file_path.is_file():
                continue
            md_path = self.md_dir / f"{file_path.stem}.md"
            if self.force or not md_path.exists():
                files_to_process.append(file_path)
        return files_to_process
    
    def _convert_file(self, src_path: Path):
        try:
            conv_res = self.converter.convert(str(src_path))
            md_content = conv_res.document.export_to_markdown()
            final_content = f"# Source: {src_path.name}\n\n{md_content}"
            
            out_md = self.md_dir / f"{src_path.stem}.md"
            out_md.write_text(final_content, encoding="utf-8")
            print(f"✅ Converted: {src_path.name}")
            return True
        except Exception as e:
            print(f"⚠️ Error converting {src_path.name}: {e}")
            return False
    
    def convert_all(self):
        self.md_dir.mkdir(parents=True, exist_ok=True)
        files = self._get_files_to_process()
        
        if not files:
            print("No new files to convert.")
            return
        
        print(f"Converting {len(files)} file(s)...")
        for src_path in tqdm(files, desc="Converting", unit="file"):
            self._convert_file(src_path)

def main():
    parser = argparse.ArgumentParser(description="Convert documents to markdown")
    parser.add_argument("--docs-dir", 
                        default=os.getenv("DOCS_DIR") or "data/all",
                        help="Source documents directory")
    parser.add_argument("--md-dir", 
                        default=os.getenv("MD_DIR") or "data/md",
                        help="Output markdown directory")
    parser.add_argument("--force", action="store_true",
                        help="Force reconversion of existing MD files")
    
    args = parser.parse_args()
    
    converter = MDConverter(args.docs_dir, args.md_dir, args.force)
    converter.convert_all()

if __name__ == "__main__":
    main()
