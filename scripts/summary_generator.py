#!/usr/bin/env python3
"""
AI Summary Generator for Telephony Mastery Content

Generates 5-bullet point summaries of content that was truncated from public versions.
"""

import os
import yaml
import json
import argparse
import asyncio
from pathlib import Path
from typing import Dict, List
import anthropic

class SummaryGenerator:
    def __init__(self, anthropic_api_key: str):
        """Initialize the summary generator"""
        self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.content_dir = Path("content")
        self.public_dir = Path("content-processing/public")
        self.private_dir = Path("content-processing/private")
        self.summaries_dir = Path("content-processing/summaries")
        
        # Ensure summaries directory exists
        self.summaries_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_frontmatter(self, content: str):
        """Parse YAML frontmatter and return metadata + content"""
        if not content.startswith('---'):
            return {}, content
            
        try:
            end_marker = content.find('\n---\n', 4)
            if end_marker == -1:
                return {}, content
                
            frontmatter_str = content[4:end_marker]
            body = content[end_marker + 5:]
            
            frontmatter = yaml.safe_load(frontmatter_str)
            return frontmatter or {}, body
        except yaml.YAMLError:
            return {}, content
    
    def extract_remaining_content(self, public_file: Path, private_file: Path) -> str:
        """Extract the content that was truncated from the public version"""
        try:
            with open(public_file, 'r', encoding='utf-8') as f:
                public_content = f.read()
            with open(private_file, 'r', encoding='utf-8') as f:
                private_content = f.read()
            
            public_frontmatter, public_body = self.parse_frontmatter(public_content)
            private_frontmatter, private_body = self.parse_frontmatter(private_content)
            
            # Remove the continuation notice from public content
            public_body = public_body.replace(
                "\n\n---\n\n*This lesson continues with advanced concepts and practical examples. Full content available in the complete course.*", 
                ""
            ).strip()
            
            # Find where the public content ends in the private content
            if public_body in private_body:
                remaining_start = private_body.find(public_body) + len(public_body)
                remaining_content = private_body[remaining_start:].strip()
                return remaining_content
            else:
                # Fallback: return second half of private content
                lines = private_body.split('\n')
                middle = len(lines) // 2
                return '\n'.join(lines[middle:]).strip()
                
        except Exception as e:
            print(f"Error extracting remaining content: {e}")
            return ""
    
    def generate_summary(self, content: str, title: str, module: str = "") -> str:
        """Generate 5-bullet point summary using Claude"""
        module_context = f" from the {module} module" if module else ""
        
        prompt = f"""Please create a concise 5-bullet point summary of the following advanced content from a telephony mastery lesson titled "{title}"{module_context}.

This content represents the latter portion of the lesson that goes beyond the introductory concepts. Focus on:
- Advanced technical concepts and implementation details
- Practical troubleshooting insights
- Real-world applications and best practices
- Key takeaways for network operations professionals
- Important warnings or considerations

Content to summarize:
{content}

Please provide exactly 5 bullet points, each starting with a dash (-) and focusing on the most valuable advanced concepts. Keep each bullet concise but informative."""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def process_file_summary(self, filename: str) -> Dict:
        """Generate summary for a specific file"""
        public_file = self.public_dir / filename
        private_file = self.private_dir / filename
        summary_file = self.summaries_dir / f"{filename.replace('.md', '_summary.md')}"
        
        if not public_file.exists() or not private_file.exists():
            return {"error": f"Missing public or private file for {filename}"}
        
        print(f"Generating summary for: {filename}")
        
        try:
            # Get the remaining content
            remaining_content = self.extract_remaining_content(public_file, private_file)
            
            if not remaining_content.strip():
                return {
                    "filename": filename,
                    "status": "skipped",
                    "reason": "No remaining content to summarize"
                }
            
            # Get metadata from private file
            with open(private_file, 'r', encoding='utf-8') as f:
                private_content = f.read()
            
            frontmatter, _ = self.parse_frontmatter(private_content)
            title = frontmatter.get('title', filename.replace('.md', ''))
            module = frontmatter.get('module', '')
            
            # Generate AI summary
            summary = self.generate_summary(remaining_content, title, module)
            
            # Create summary file
            summary_frontmatter = {
                'source_file': filename,
                'title': f"Advanced Concepts Summary: {title}",
                'module': module,
                'content_type': 'ai_summary',
                'generated_by': 'claude-3-haiku-20240307',
                'summary_of': 'truncated_content'
            }
            
            summary_yaml = yaml.dump(summary_frontmatter, default_flow_style=False)
            summary_content = f"---\n{summary_yaml}---\n\n# Advanced Concepts Summary: {title}\n\n{summary}\n\n---\n\n*This summary covers the advanced content that was truncated from the public version. For complete details and examples, see the full lesson content.*"
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            return {
                "filename": filename,
                "status": "success",
                "title": title,
                "module": module,
                "summary_file": str(summary_file),
                "remaining_word_count": len(remaining_content.split())
            }
            
        except Exception as e:
            return {
                "filename": filename,
                "status": "error",
                "error": str(e)
            }
    
    def process_all_summaries(self) -> List[Dict]:
        """Generate summaries for all processed files"""
        results = []
        
        # Find all public files (these are the ones that were processed)
        public_files = list(self.public_dir.glob("*.md"))
        print(f"Found {len(public_files)} files to generate summaries for")
        
        for public_file in public_files:
            result = self.process_file_summary(public_file.name)
            results.append(result)
        
        return results
    
    def generate_summary_report(self, results: List[Dict]) -> Dict:
        """Generate a report of summary generation results"""
        successful = [r for r in results if r.get('status') == 'success']
        skipped = [r for r in results if r.get('status') == 'skipped']
        failed = [r for r in results if r.get('status') == 'error']
        
        report = {
            "summary_generation_report": {
                "total_files": len(results),
                "summaries_generated": len(successful),
                "files_skipped": len(skipped),
                "failed": len(failed),
                "success_rate": f"{(len(successful)/len(results)*100):.1f}%" if results else "0%"
            },
            "generated_summaries": successful,
            "skipped_files": skipped,
            "errors": failed
        }
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Generate AI summaries for truncated content')
    parser.add_argument('--anthropic-key', type=str, required=True,
                       help='Anthropic API key (required)')
    parser.add_argument('--single-file', type=str,
                       help='Generate summary for a specific file only')
    
    args = parser.parse_args()
    
    # Change to script directory
    os.chdir(Path(__file__).parent.parent)
    
    generator = SummaryGenerator(args.anthropic_key)
    
    if args.single_file:
        result = generator.process_file_summary(args.single_file)
        print(json.dumps(result, indent=2))
    else:
        results = generator.process_all_summaries()
        report = generator.generate_summary_report(results)
        
        # Save report
        report_file = Path("scripts/summary_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{'='*60}")
        print("AI SUMMARY GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"Summaries generated: {report['summary_generation_report']['summaries_generated']}/{report['summary_generation_report']['total_files']}")
        print(f"Files skipped: {report['summary_generation_report']['files_skipped']}")
        print(f"Success rate: {report['summary_generation_report']['success_rate']}")
        print(f"\nSummary files saved to: {generator.summaries_dir}")
        print(f"Report saved to: {report_file}")
        
        if report['summary_generation_report']['failed'] > 0:
            print(f"\n⚠️  {report['summary_generation_report']['failed']} files failed")

if __name__ == "__main__":
    main()