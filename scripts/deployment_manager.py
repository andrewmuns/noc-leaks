#!/usr/bin/env python3
"""
Deployment Manager for Telephony Mastery Content

Manages the deployment of processed content, ensuring clean separation
between local private content and publicly deployable content.
"""

import os
import json
import shutil
import argparse
from pathlib import Path
from typing import Dict, List
import yaml

class DeploymentManager:
    def __init__(self):
        """Initialize the deployment manager"""
        self.base_dir = Path.cwd()
        self.public_dir = Path("content-processing/public")
        self.private_dir = Path("content-processing/private")
        self.summaries_dir = Path("content-processing/summaries")
        self.deploy_dir = Path("content-processing/deploy")
        self.scripts_dir = Path("scripts")
        
        # Create deploy directory structure
        self.deploy_dir.mkdir(parents=True, exist_ok=True)
        (self.deploy_dir / "content").mkdir(exist_ok=True)
        (self.deploy_dir / "summaries").mkdir(exist_ok=True)
        (self.deploy_dir / "metadata").mkdir(exist_ok=True)
    
    def create_deployment_manifest(self) -> Dict:
        """Create a manifest of all deployable content"""
        manifest = {
            "deployment_info": {
                "created_at": self._get_timestamp(),
                "content_type": "telephony_mastery_public",
                "version": "1.0"
            },
            "content_summary": {
                "public_files": [],
                "summary_files": [],
                "total_public_files": 0,
                "total_summaries": 0
            },
            "deployment_structure": {
                "content/": "Truncated public content files",
                "summaries/": "AI-generated summaries of advanced content",
                "metadata/": "Deployment metadata and manifests"
            }
        }
        
        # Collect public files
        if self.public_dir.exists():
            public_files = list(self.public_dir.glob("*.md"))
            for file in public_files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    frontmatter = self._parse_frontmatter(content)[0]
                    manifest["content_summary"]["public_files"].append({
                        "filename": file.name,
                        "title": frontmatter.get("title", "Untitled"),
                        "module": frontmatter.get("module", "Unknown"),
                        "difficulty": frontmatter.get("difficulty", "Unknown"),
                        "word_limit": frontmatter.get("word_limit", 300)
                    })
                except Exception as e:
                    print(f"Warning: Could not process {file.name}: {e}")
            
            manifest["content_summary"]["total_public_files"] = len(public_files)
        
        # Collect summary files
        if self.summaries_dir.exists():
            summary_files = list(self.summaries_dir.glob("*.md"))
            for file in summary_files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    frontmatter = self._parse_frontmatter(content)[0]
                    manifest["content_summary"]["summary_files"].append({
                        "filename": file.name,
                        "source_file": frontmatter.get("source_file", "Unknown"),
                        "title": frontmatter.get("title", "Untitled"),
                        "module": frontmatter.get("module", "Unknown")
                    })
                except Exception as e:
                    print(f"Warning: Could not process {file.name}: {e}")
            
            manifest["content_summary"]["total_summaries"] = len(summary_files)
        
        return manifest
    
    def _parse_frontmatter(self, content: str):
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
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def prepare_deployment(self) -> Dict:
        """Prepare all content for deployment"""
        print("Preparing deployment package...")
        
        # Clear existing deployment directory
        if self.deploy_dir.exists():
            shutil.rmtree(self.deploy_dir)
        
        self.deploy_dir.mkdir(parents=True)
        (self.deploy_dir / "content").mkdir()
        (self.deploy_dir / "summaries").mkdir()
        (self.deploy_dir / "metadata").mkdir()
        
        # Copy public content files
        public_files_copied = 0
        if self.public_dir.exists():
            for file in self.public_dir.glob("*.md"):
                dest = self.deploy_dir / "content" / file.name
                shutil.copy2(file, dest)
                public_files_copied += 1
        
        # Copy summary files
        summary_files_copied = 0
        if self.summaries_dir.exists():
            for file in self.summaries_dir.glob("*.md"):
                dest = self.deploy_dir / "summaries" / file.name
                shutil.copy2(file, dest)
                summary_files_copied += 1
        
        # Create deployment manifest
        manifest = self.create_deployment_manifest()
        manifest_file = self.deploy_dir / "metadata" / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Create README for deployment
        readme_content = self._create_deployment_readme(manifest)
        readme_file = self.deploy_dir / "README.md"
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        # Create .gitignore to protect private content
        gitignore_content = self._create_deployment_gitignore()
        gitignore_file = self.deploy_dir / ".gitignore"
        with open(gitignore_file, 'w') as f:
            f.write(gitignore_content)
        
        deployment_summary = {
            "status": "success",
            "deployment_dir": str(self.deploy_dir),
            "files_copied": {
                "public_content": public_files_copied,
                "summaries": summary_files_copied
            },
            "manifest_created": str(manifest_file),
            "readme_created": str(readme_file)
        }
        
        print(f"✅ Deployment prepared successfully")
        print(f"📁 Deployment directory: {self.deploy_dir}")
        print(f"📄 Public content files: {public_files_copied}")
        print(f"📋 Summary files: {summary_files_copied}")
        
        return deployment_summary
    
    def _create_deployment_readme(self, manifest: Dict) -> str:
        """Create README for deployment package"""
        return f"""# Telephony Mastery - Public Content Package

This package contains the publicly deployable content from the Telephony Mastery course.

## Package Information

- **Created:** {manifest['deployment_info']['created_at']}
- **Content Type:** {manifest['deployment_info']['content_type']}
- **Version:** {manifest['deployment_info']['version']}

## Content Summary

- **Public Content Files:** {manifest['content_summary']['total_public_files']} lessons
- **AI-Generated Summaries:** {manifest['content_summary']['total_summaries']} summaries

## Directory Structure

```
deploy/
├── content/           # Truncated public lesson content (first 300 words)
├── summaries/         # AI-generated 5-bullet summaries of advanced content
├── metadata/          # Deployment manifests and metadata
├── README.md          # This file
└── .gitignore         # Protects against accidental private content inclusion
```

## Content Processing Details

Each file in `content/` contains:
- Complete YAML frontmatter with lesson metadata
- First 300 words of the lesson content
- Continuation notice for truncated content

Each file in `summaries/` contains:
- AI-generated 5-bullet point summary
- Summary of the advanced content not included in public version
- Generated using Claude 3 Haiku

## Usage Notes

1. **Public Content:** Files in `content/` are safe for public distribution
2. **Full Content:** Complete lessons remain in the private repository
3. **AI Summaries:** Provide value preview of advanced concepts
4. **Metadata:** All files include comprehensive metadata for content management

## Deployment Safety

This package is designed to ensure NO private content is accidentally deployed:
- Only truncated content (first 300 words) is included
- AI summaries are generated from truncated portions only
- Full lesson content remains in private repository
- .gitignore prevents accidental inclusion of private files

---

**⚠️ Important:** This is public content only. Full course content remains private and licensed.
"""
    
    def _create_deployment_gitignore(self) -> str:
        """Create .gitignore for deployment safety"""
        return """# Telephony Mastery Deployment - Protect Private Content
#
# This .gitignore ensures that private content never gets accidentally
# included in public deployments

# Private content directories (if accidentally copied)
../private/
../content/
../content-processing/private/
**/private/

# Full content files
*-full.md
*-complete.md
*-private.md

# Processing artifacts
processing_report.json
summary_report.json
*.log

# Environment files
.env
.env.*
anthropic_api_key*

# System files
.DS_Store
Thumbs.db
*.swp
*.swo
*~

# IDE files
.vscode/
.idea/
*.sublime-*

# Node modules (if any)
node_modules/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# Any files containing 'private' or 'full'
*private*
*full*
*complete*

# Backup files
*.bak
*.backup
*.old
"""
    
    def validate_deployment(self) -> Dict:
        """Validate that deployment contains only public content"""
        issues = []
        warnings = []
        
        if not self.deploy_dir.exists():
            issues.append("Deployment directory does not exist")
            return {"status": "failed", "issues": issues}
        
        # Check for required structure
        required_dirs = ["content", "summaries", "metadata"]
        for dir_name in required_dirs:
            dir_path = self.deploy_dir / dir_name
            if not dir_path.exists():
                issues.append(f"Missing required directory: {dir_name}")
        
        # Validate content files
        content_dir = self.deploy_dir / "content"
        if content_dir.exists():
            for file in content_dir.glob("*.md"):
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                frontmatter, _ = self._parse_frontmatter(content)
                
                # Check if marked as truncated
                if frontmatter.get('content_type') != 'truncated':
                    warnings.append(f"Content file {file.name} not marked as truncated")
                
                # Check word limit
                word_limit = frontmatter.get('word_limit')
                if not word_limit:
                    warnings.append(f"Content file {file.name} missing word_limit metadata")
        
        # Check for accidentally included private files
        for root, dirs, files in os.walk(self.deploy_dir):
            for file in files:
                if any(term in file.lower() for term in ['private', 'full', 'complete']):
                    issues.append(f"Potentially private file found: {file}")
        
        validation_result = {
            "status": "passed" if not issues else "failed",
            "issues": issues,
            "warnings": warnings,
            "deployment_dir": str(self.deploy_dir)
        }
        
        return validation_result

def main():
    parser = argparse.ArgumentParser(description='Manage deployment of telephony mastery content')
    parser.add_argument('action', choices=['prepare', 'validate', 'status'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    # Change to script directory
    os.chdir(Path(__file__).parent.parent)
    
    manager = DeploymentManager()
    
    if args.action == 'prepare':
        result = manager.prepare_deployment()
        print(json.dumps(result, indent=2))
        
    elif args.action == 'validate':
        result = manager.validate_deployment()
        print(json.dumps(result, indent=2))
        
        if result['status'] == 'failed':
            print(f"\n❌ Validation failed with {len(result['issues'])} issues")
            exit(1)
        elif result['warnings']:
            print(f"\n⚠️  Validation passed with {len(result['warnings'])} warnings")
        else:
            print("\n✅ Validation passed - deployment is safe")
            
    elif args.action == 'status':
        manifest_file = manager.deploy_dir / "metadata" / "manifest.json"
        
        if not manifest_file.exists():
            print("No deployment found. Run 'prepare' first.")
            return
        
        with open(manifest_file) as f:
            manifest = json.load(f)
        
        print("📦 Deployment Status")
        print(f"Created: {manifest['deployment_info']['created_at']}")
        print(f"Public files: {manifest['content_summary']['total_public_files']}")
        print(f"Summary files: {manifest['content_summary']['total_summaries']}")
        print(f"Location: {manager.deploy_dir}")

if __name__ == "__main__":
    main()