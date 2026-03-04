#!/usr/bin/env node
/**
 * CONTENT MIGRATION SCRIPT
 * 
 * Migrates existing content to secure structure:
 * - Moves current content/ to content-full/ (protected)
 * - Creates public previews in content/
 * 
 * ⚠️  RUN THIS ONCE DURING INITIAL SETUP ONLY!
 */

import fs from 'fs/promises';
import path from 'path';

class ContentMigrator {
  constructor() {
    this.sourceDir = './content';
    this.fullDir = './content-full';
    this.backupDir = './content-backup-' + Date.now();
  }

  async migrate() {
    console.log('🔄 Starting secure content migration...');
    
    try {
      // Step 1: Create backup of original content
      console.log('📦 Creating backup...');
      await this.createBackup();
      
      // Step 2: Move existing content to full directory
      console.log('🔒 Moving content to secure location...');
      await this.moveToFull();
      
      // Step 3: Generate public previews
      console.log('📄 Generating public previews...');
      const { default: ContentProcessor } = await import('./process-content.js');
      const processor = new ContentProcessor();
      await processor.processAllContent();
      
      console.log('✅ Migration completed successfully!');
      console.log('\n📁 Directory structure:');
      console.log(`   content-full/     ← FULL COURSE CONTENT (never committed)`);
      console.log(`   content/          ← PUBLIC PREVIEWS (safe for GitHub)`);
      console.log(`   ${path.basename(this.backupDir)}/ ← Original backup`);
      
    } catch (error) {
      console.error('❌ Migration failed:', error);
      console.log('\n🔄 Rolling back...');
      await this.rollback();
    }
  }

  async createBackup() {
    try {
      await fs.mkdir(this.backupDir, { recursive: true });
      await this.copyDirectory(this.sourceDir, this.backupDir);
      console.log(`✅ Backup created: ${this.backupDir}`);
    } catch (error) {
      throw new Error(`Failed to create backup: ${error.message}`);
    }
  }

  async moveToFull() {
    try {
      // Create full content directory
      await fs.mkdir(this.fullDir, { recursive: true });
      
      // Copy content to full directory
      await this.copyDirectory(this.sourceDir, this.fullDir);
      
      // Remove original content directory
      await fs.rm(this.sourceDir, { recursive: true, force: true });
      
      console.log(`✅ Content moved to: ${this.fullDir}`);
    } catch (error) {
      throw new Error(`Failed to move content: ${error.message}`);
    }
  }

  async copyDirectory(src, dest) {
    await fs.mkdir(dest, { recursive: true });
    
    const entries = await fs.readdir(src, { withFileTypes: true });
    
    for (const entry of entries) {
      const srcPath = path.join(src, entry.name);
      const destPath = path.join(dest, entry.name);
      
      if (entry.isDirectory()) {
        await this.copyDirectory(srcPath, destPath);
      } else {
        await fs.copyFile(srcPath, destPath);
      }
    }
  }

  async rollback() {
    try {
      // Remove any partial migration
      await fs.rm(this.sourceDir, { recursive: true, force: true });
      await fs.rm(this.fullDir, { recursive: true, force: true });
      
      // Restore from backup
      await this.copyDirectory(this.backupDir, this.sourceDir);
      
      console.log('✅ Rollback completed - original content restored');
    } catch (error) {
      console.error('💥 Rollback failed:', error);
      console.log(`Manual recovery needed - restore from: ${this.backupDir}`);
    }
  }
}

// Run migration if called directly  
if (process.argv[1] === new URL(import.meta.url).pathname) {
  const migrator = new ContentMigrator();
  migrator.migrate().catch(console.error);
}

export default ContentMigrator;