#!/usr/bin/env node
/**
 * SECURITY CONTENT PROCESSOR
 * 
 * This script processes full course content and creates truncated public versions
 * that are safe for GitHub/public deployment.
 * 
 * NEVER MODIFY THIS TO EXPOSE FULL CONTENT!
 */

import fs from 'fs/promises';
import path from 'path';

class ContentProcessor {
  constructor() {
    this.fullContentDir = './content-full';
    this.publicContentDir = './content';
    this.maxPublicLines = 50; // Maximum lines for public preview
    this.maxPublicChars = 2500; // Maximum characters for public preview
  }

  /**
   * Process a single markdown file
   * Extracts frontmatter + limited content for public version
   */
  async processMarkdownFile(filePath) {
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const lines = content.split('\n');
      
      // Extract frontmatter
      let frontmatterEnd = -1;
      let inFrontmatter = false;
      
      for (let i = 0; i < lines.length; i++) {
        if (lines[i].trim() === '---') {
          if (!inFrontmatter) {
            inFrontmatter = true;
          } else {
            frontmatterEnd = i;
            break;
          }
        }
      }

      if (frontmatterEnd === -1) {
        console.warn(`No frontmatter found in ${filePath}`);
        return null;
      }

      // Get frontmatter
      const frontmatter = lines.slice(0, frontmatterEnd + 1).join('\n');
      
      // Get content after frontmatter
      const bodyContent = lines.slice(frontmatterEnd + 1).join('\n');
      
      // Create truncated version
      const truncatedContent = this.createTruncatedContent(bodyContent);
      
      // Add paywall notice
      const publicContent = frontmatter + '\n\n' + truncatedContent + '\n\n' + this.getPaywallNotice();
      
      return publicContent;
    } catch (error) {
      console.error(`Error processing ${filePath}:`, error);
      return null;
    }
  }

  /**
   * Create truncated content with intelligent cutoff
   */
  createTruncatedContent(content) {
    const lines = content.split('\n');
    let publicLines = [];
    let charCount = 0;
    
    // Always include first heading and intro paragraph
    for (let i = 0; i < Math.min(lines.length, this.maxPublicLines); i++) {
      const line = lines[i];
      
      // Stop at character limit
      if (charCount + line.length > this.maxPublicChars) {
        break;
      }
      
      publicLines.push(line);
      charCount += line.length + 1; // +1 for newline
      
      // Stop at first major section after intro
      if (i > 10 && line.startsWith('## ')) {
        break;
      }
    }
    
    return publicLines.join('\n');
  }

  /**
   * Generate paywall notice
   */
  getPaywallNotice() {
    return `---

## 🔒 Full Course Content Available

This is a preview of the Telephony Mastery Course. The complete lesson includes:

- ✅ Detailed technical explanations
- ✅ Advanced configuration examples  
- ✅ Hands-on lab exercises
- ✅ Real-world troubleshooting scenarios
- ✅ Practice quizzes and assessments

[**🚀 Unlock Full Course Access**](https://teleponymastery.com/enroll)

---

*Preview shows approximately 25% of the full lesson content.*`;
  }

  /**
   * Process all files in full content directory
   */
  async processAllContent() {
    try {
      console.log('🔄 Processing content for public deployment...');
      
      // Ensure directories exist
      await fs.mkdir(this.publicContentDir, { recursive: true });
      
      // Get all markdown files from full content
      const files = await this.getMarkdownFiles(this.fullContentDir);
      
      let processed = 0;
      let errors = 0;
      
      for (const file of files) {
        const relativePath = path.relative(this.fullContentDir, file);
        const outputPath = path.join(this.publicContentDir, relativePath);
        
        // Ensure output directory exists
        await fs.mkdir(path.dirname(outputPath), { recursive: true });
        
        console.log(`Processing: ${relativePath}`);
        
        const publicContent = await this.processMarkdownFile(file);
        
        if (publicContent) {
          await fs.writeFile(outputPath, publicContent, 'utf-8');
          processed++;
        } else {
          errors++;
        }
      }
      
      console.log(`✅ Content processing complete:`);
      console.log(`   📄 ${processed} files processed`);
      console.log(`   ❌ ${errors} errors`);
      console.log(`   📁 Public content: ${this.publicContentDir}`);
      
    } catch (error) {
      console.error('❌ Content processing failed:', error);
      process.exit(1);
    }
  }

  /**
   * Recursively get all markdown files
   */
  async getMarkdownFiles(dir) {
    const files = [];
    
    try {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory()) {
          files.push(...await this.getMarkdownFiles(fullPath));
        } else if (entry.name.endsWith('.md')) {
          files.push(fullPath);
        }
      }
    } catch (error) {
      if (error.code !== 'ENOENT') {
        throw error;
      }
    }
    
    return files;
  }

  /**
   * Security check - ensure full content is not in git
   */
  async validateSecurity() {
    console.log('🔒 Running security validation...');
    
    const dangerousPaths = [
      'content-full',
      'content-private',
      this.fullContentDir
    ];
    
    for (const dangerousPath of dangerousPaths) {
      if (await this.isInGit(dangerousPath)) {
        throw new Error(`SECURITY VIOLATION: ${dangerousPath} is tracked by Git!`);
      }
    }
    
    console.log('✅ Security validation passed');
  }

  /**
   * Check if path is tracked by git
   */
  async isInGit(filePath) {
    const { exec } = await import('child_process');
    const { promisify } = await import('util');
    const execAsync = promisify(exec);
    
    try {
      await execAsync(`git ls-files --error-unmatch ${filePath}`, { 
        cwd: process.cwd(),
        stdio: 'pipe'
      });
      return true; // File is tracked
    } catch (error) {
      return false; // File is not tracked (which is what we want)
    }
  }
}

// Run the processor
if (process.argv[1] === new URL(import.meta.url).pathname) {
  const processor = new ContentProcessor();
  
  processor.validateSecurity()
    .then(() => processor.processAllContent())
    .catch(error => {
      console.error('💥 Fatal error:', error.message);
      process.exit(1);
    });
}

export default ContentProcessor;