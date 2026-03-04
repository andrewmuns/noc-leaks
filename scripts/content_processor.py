#!/usr/bin/env python3
"""
Content Processing System for Telephony Mastery Site

This script processes markdown files to:
1. Extract first 300 words for public content
2. Generate AI summaries of remaining content
3. Maintain clean separation between public and private content
"""

import os
import re
import yaml
import json
import argparse
from pathlib import Path
from typing import Dict, Tuple, List
import anthropic

# Configuration
CONTENT_DIR = Path("content")
PUBLIC_DIR = Path("content-processing/public")
PRIVATE_DIR = Path("content-processing/private")
SCRIPTS_DIR = Path("scripts")

class ContentProcessor:
    def __init__(self, anthropic_api_key: str = None):
        """Initialize the content processor"""
        self.anthropic_client = None
        if anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        # Ensure directories exist
        PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
        PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
        
    def parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Parse YAML frontmatter and return metadata + content"""
        if not content.startswith('---'):
            return {}, content
            
        try:
            # Find the end of frontmatter
            end_marker = content.find('\n---\n', 4)
            if end_marker == -1:
                return {}, content
                
            frontmatter_str = content[4:end_marker]
            body = content[end_marker + 5:]
            
            frontmatter = yaml.safe_load(frontmatter_str)
            return frontmatter or {}, body
        except yaml.YAMLError:
            return {}, content
    
    def count_words(self, text: str) -> int:
        """Count words in text, excluding markdown syntax"""
        # Remove markdown headers, links, code blocks, etc.
        clean_text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        clean_text = re.sub(r'`[^`]+`', '', clean_text)
        clean_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_text)
        clean_text = re.sub(r'#+\s*', '', clean_text)
        clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_text)
        clean_text = re.sub(r'\*([^*]+)\*', r'\1', clean_text)
        clean_text = re.sub(r'>\s*', '', clean_text)
        
        words = clean_text.split()
        return len(words)
    
    def extract_first_n_words(self, text: str, n: int = 300) -> Tuple[str, str]:
        """Extract first n words preserving markdown structure"""
        lines = text.split('\n')
        extracted_lines = []
        remaining_lines = []
        word_count = 0
        extraction_complete = False
        
        for line in lines:
            if not extraction_complete:
                line_word_count = self.count_words(line)
                if word_count + line_word_count <= n:
                    extracted_lines.append(line)
                    word_count += line_word_count
                else:
                    # Split the line to get exactly n words
                    words_needed = n - word_count
                    words = line.split()
                    if words_needed > 0:
                        partial_line = ' '.join(words[:words_needed])
                        extracted_lines.append(partial_line)
                    remaining_lines.append(' '.join(words[words_needed:]) if words_needed > 0 else line)
                    remaining_lines.extend(lines[lines.index(line) + 1:])
                    extraction_complete = True
                    break
            else:
                remaining_lines.append(line)
        
        if not extraction_complete:
            remaining_lines = []
            
        extracted_text = '\n'.join(extracted_lines).strip()
        remaining_text = '\n'.join(remaining_lines).strip()
        
        return extracted_text, remaining_text
    
    async def generate_summary(self, content: str, title: str) -> str:
        """Generate 5-bullet point summary using Claude"""
        if not self.anthropic_client:
            return "AI summary generation not available (no API key provided)"
            
        prompt = f"""Please create a concise 5-bullet point summary of the following content from a telephony mastery lesson titled "{title}".

Focus on the key technical concepts, practical insights, and actionable knowledge. Each bullet should be informative and specific.

Content:
{content}

Please provide exactly 5 bullet points, each starting with a dash (-) and focusing on the most important technical concepts."""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def process_file(self, file_path: Path, word_limit: int = 300) -> Dict:
        """Process a single markdown file"""
        print(f"Processing: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}
        
        # Parse frontmatter and content
        frontmatter, body = self.parse_frontmatter(content)
        
        # Extract first n words and remaining content
        extracted_text, remaining_text = self.extract_first_n_words(body, word_limit)
        
        # Create public version (truncated)
        public_frontmatter = frontmatter.copy()
        public_frontmatter['content_type'] = 'truncated'
        public_frontmatter['word_limit'] = word_limit
        public_frontmatter['full_content_available'] = True
        
        public_yaml = yaml.dump(public_frontmatter, default_flow_style=False)
        public_content = f"---\n{public_yaml}---\n\n{extracted_text}"
        
        if remaining_text.strip():
            public_content += f"\n\n---\n\n*This lesson continues with advanced concepts and practical examples. Full content available in the complete course.*"
        
        # Create private version (full content)
        private_frontmatter = frontmatter.copy()
        private_frontmatter['content_type'] = 'complete'
        private_frontmatter['public_word_count'] = self.count_words(extracted_text)
        private_frontmatter['total_word_count'] = self.count_words(body)
        
        private_yaml = yaml.dump(private_frontmatter, default_flow_style=False)
        private_content = f"---\n{private_yaml}---\n\n{body}"
        
        # Save files
        public_file = PUBLIC_DIR / file_path.name
        private_file = PRIVATE_DIR / file_path.name
        
        with open(public_file, 'w', encoding='utf-8') as f:
            f.write(public_content)
        
        with open(private_file, 'w', encoding='utf-8') as f:
            f.write(private_content)
        
        return {
            "file": file_path.name,
            "status": "success",
            "public_words": self.count_words(extracted_text),
            "total_words": self.count_words(body),
            "remaining_words": self.count_words(remaining_text),
            "public_file": str(public_file),
            "private_file": str(private_file),
            "has_remaining_content": bool(remaining_text.strip())
        }
    
    def process_all_files(self, word_limit: int = 300) -> List[Dict]:
        """Process all markdown files in content directory"""
        results = []
        
        # Find all markdown files
        md_files = list(CONTENT_DIR.glob("*.md"))
        print(f"Found {len(md_files)} markdown files to process")
        
        for file_path in md_files:
            result = self.process_file(file_path, word_limit)
            results.append(result)
        
        return results
    
    def generate_processing_report(self, results: List[Dict]) -> Dict:
        """Generate a summary report of processing results"""
        successful = [r for r in results if r.get('status') == 'success']
        failed = [r for r in results if r.get('status') != 'success']
        
        if successful:
            total_words = sum(r['total_words'] for r in successful)
            public_words = sum(r['public_words'] for r in successful)
            files_with_remaining = sum(1 for r in successful if r['has_remaining_content'])
        else:
            total_words = public_words = files_with_remaining = 0
        
        report = {
            "processing_summary": {
                "total_files": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "files_with_truncated_content": files_with_remaining
            },
            "word_statistics": {
                "total_words_across_all_files": total_words,
                "public_words_across_all_files": public_words,
                "average_file_length": total_words // len(successful) if successful else 0,
                "compression_ratio": f"{(public_words/total_words*100):.1f}%" if total_words > 0 else "0%"
            },
            "files_processed": successful,
            "errors": failed
        }
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Process telephony mastery content')
    parser.add_argument('--word-limit', type=int, default=300, 
                       help='Word limit for public content (default: 300)')
    parser.add_argument('--anthropic-key', type=str, 
                       help='Anthropic API key for AI summaries')
    parser.add_argument('--single-file', type=str,
                       help='Process only a specific file')
    parser.add_argument('--report-only', action='store_true',
                       help='Generate report without processing files')
    
    args = parser.parse_args()
    
    # Change to script directory
    os.chdir(Path(__file__).parent.parent)
    
    processor = ContentProcessor(args.anthropic_key)
    
    if args.report_only:
        # Check if processed files exist and generate report
        public_files = list(PUBLIC_DIR.glob("*.md"))
        print(f"Found {len(public_files)} processed files")
        return
    
    if args.single_file:
        file_path = CONTENT_DIR / args.single_file
        if not file_path.exists():
            print(f"Error: File {file_path} does not exist")
            return
        
        result = processor.process_file(file_path, args.word_limit)
        print(json.dumps(result, indent=2))
    else:
        results = processor.process_all_files(args.word_limit)
        report = processor.generate_processing_report(results)
        
        # Save report
        report_file = SCRIPTS_DIR / "processing_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{'='*60}")
        print("CONTENT PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Files processed: {report['processing_summary']['successful']}/{report['processing_summary']['total_files']}")
        print(f"Total words: {report['word_statistics']['total_words_across_all_files']:,}")
        print(f"Public words: {report['word_statistics']['public_words_across_all_files']:,}")
        print(f"Compression ratio: {report['word_statistics']['compression_ratio']}")
        print(f"Files with truncated content: {report['processing_summary']['files_with_truncated_content']}")
        print(f"\nPublic files saved to: {PUBLIC_DIR}")
        print(f"Private files saved to: {PRIVATE_DIR}")
        print(f"Report saved to: {report_file}")
        
        if report['processing_summary']['failed'] > 0:
            print(f"\n⚠️  {report['processing_summary']['failed']} files failed to process")

if __name__ == "__main__":
    main()