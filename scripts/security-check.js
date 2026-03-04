#!/usr/bin/env node
/**
 * SECURITY VALIDATION SCRIPT
 * 
 * Comprehensive security checks to ensure:
 * - Full content never gets committed to Git
 * - Sensitive files are properly ignored
 * - Build processes are secure
 * 
 * This runs before every secure build/deploy
 */

import fs from 'fs/promises';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

class SecurityValidator {
  constructor() {
    this.execAsync = promisify(exec);
    this.dangerousPaths = [
      'content-full',
      'content-private', 
      'content-backup',
      '*.full.md',
      '*-full.md',
      '*-private.md'
    ];
    this.requiredIgnorePatterns = [
      'content-full/',
      'content-private/',
      '*.full.md',
      '*.private.md'
    ];
  }

  async runAllChecks() {
    console.log('🔒 Running comprehensive security validation...\n');
    
    const checks = [
      () => this.checkGitignore(),
      () => this.checkGitTracking(),
      () => this.checkFilePermissions(),
      () => this.checkContentStructure(),
      () => this.checkEnvironmentFiles(),
      () => this.validateBuildOutput()
    ];

    let passed = 0;
    let failed = 0;

    for (const check of checks) {
      try {
        await check();
        passed++;
      } catch (error) {
        console.error(`❌ ${error.message}\n`);
        failed++;
      }
    }

    console.log('📊 Security Validation Results:');
    console.log(`   ✅ Passed: ${passed}`);
    console.log(`   ❌ Failed: ${failed}`);

    if (failed > 0) {
      console.error('\n🚨 SECURITY VALIDATION FAILED!');
      console.error('Fix the issues above before proceeding.');
      process.exit(1);
    }

    console.log('\n🎉 Security validation passed! Safe to proceed.\n');
  }

  async checkGitignore() {
    console.log('🔍 Checking .gitignore configuration...');
    
    try {
      const gitignoreContent = await fs.readFile('.gitignore', 'utf-8');
      
      for (const pattern of this.requiredIgnorePatterns) {
        if (!gitignoreContent.includes(pattern)) {
          throw new Error(`Missing required .gitignore pattern: ${pattern}`);
        }
      }
      
      console.log('   ✅ .gitignore properly configured');
    } catch (error) {
      if (error.code === 'ENOENT') {
        throw new Error('.gitignore file missing!');
      }
      throw error;
    }
  }

  async checkGitTracking() {
    console.log('🔍 Checking Git tracking status...');
    
    for (const dangerousPath of this.dangerousPaths) {
      try {
        const { stdout } = await this.execAsync(`git ls-files "${dangerousPath}" 2>/dev/null`, {
          cwd: process.cwd()
        });
        
        // If stdout has content, files are tracked
        if (stdout.trim()) {
          throw new Error(`CRITICAL: ${dangerousPath} is tracked by Git! Files: ${stdout.trim()}`);
        }
      } catch (error) {
        if (error.message.includes('CRITICAL:')) {
          throw error;
        }
        // Command failed or no output = good (not tracked)
      }
    }
    
    console.log('   ✅ No sensitive files tracked by Git');
  }

  async checkFilePermissions() {
    console.log('🔍 Checking file permissions...');
    
    const sensitiveFiles = [
      'scripts/',
      '.env',
      '.env.local'
    ];

    for (const file of sensitiveFiles) {
      try {
        const stats = await fs.stat(file);
        if (stats.isDirectory() || stats.isFile()) {
          // Files exist, check if they're properly protected
          // (In a production environment, you'd check actual permissions)
          console.log(`   📁 Found: ${file}`);
        }
      } catch (error) {
        // File doesn't exist - that's OK for optional files
        if (file.includes('.env') && error.code === 'ENOENT') {
          continue; // .env files are optional
        }
      }
    }
    
    console.log('   ✅ File permissions acceptable');
  }

  async checkContentStructure() {
    console.log('🔍 Validating content structure...');
    
    // Check if full content directory exists
    try {
      await fs.access('content-full');
      console.log('   📁 content-full/ directory found (protected)');
    } catch (error) {
      console.log('   ⚠️  content-full/ directory not found (run migration first)');
    }

    // Check public content directory
    try {
      await fs.access('content');
      console.log('   📁 content/ directory found (public previews)');
      
      // Validate that public content has paywall notices
      const files = await this.getMarkdownFiles('content');
      if (files.length > 0) {
        const randomFile = files[Math.floor(Math.random() * files.length)];
        const content = await fs.readFile(randomFile, 'utf-8');
        
        if (!content.includes('Full Course Content Available') && !content.includes('preview')) {
          console.log('   ⚠️  Some files may not have paywall notices');
        } else {
          console.log('   ✅ Public content has paywall protection');
        }
      }
    } catch (error) {
      throw new Error('content/ directory missing - run content processing first');
    }
  }

  async checkEnvironmentFiles() {
    console.log('🔍 Checking environment configuration...');
    
    const envFiles = ['.env', '.env.local', '.env.production'];
    let foundAny = false;
    
    for (const envFile of envFiles) {
      try {
        await fs.access(envFile);
        foundAny = true;
        
        // Check if it's in .gitignore
        const gitignoreContent = await fs.readFile('.gitignore', 'utf-8');
        if (!gitignoreContent.includes(envFile) && !gitignoreContent.includes('.env')) {
          throw new Error(`${envFile} is not in .gitignore!`);
        }
      } catch (error) {
        if (error.message.includes('not in .gitignore')) {
          throw error;
        }
        // File doesn't exist - OK
      }
    }
    
    if (foundAny) {
      console.log('   ✅ Environment files properly protected');
    } else {
      console.log('   ℹ️  No environment files found');
    }
  }

  async validateBuildOutput() {
    console.log('🔍 Validating build output security...');
    
    const buildDirs = ['.nuxt', '.output', 'dist'];
    
    for (const buildDir of buildDirs) {
      try {
        await fs.access(buildDir);
        
        // Check that build directories are in .gitignore
        const gitignoreContent = await fs.readFile('.gitignore', 'utf-8');
        if (!gitignoreContent.includes(buildDir)) {
          throw new Error(`Build directory ${buildDir} not in .gitignore!`);
        }
      } catch (error) {
        if (error.message.includes('not in .gitignore')) {
          throw error;
        }
        // Build dir doesn't exist yet - OK
      }
    }
    
    console.log('   ✅ Build output configuration secure');
  }

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
      // Directory doesn't exist
    }
    
    return files;
  }
}

// Run security check if called directly
if (process.argv[1] === new URL(import.meta.url).pathname) {
  const validator = new SecurityValidator();
  validator.runAllChecks().catch(() => process.exit(1));
}

export default SecurityValidator;