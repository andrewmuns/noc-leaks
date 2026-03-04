# 🔒 Telephony Mastery - Security & Git Strategy

## 🚨 CRITICAL SECURITY RULES

**NEVER COMMIT FULL COURSE CONTENT TO GIT!**

This project implements a **bulletproof security system** to protect premium course content while allowing safe public deployment.

## 📁 Directory Structure

```
telephony-mastery-site/
├── content-full/           ← 🔒 FULL COURSE CONTENT (NEVER COMMITTED)
├── content/                ← 📄 PUBLIC PREVIEWS (Safe for GitHub)
├── scripts/               ← 🛠️ Content processing tools
├── .gitignore            ← 🛡️ Security protection rules
└── nuxt.config.security.ts ← ⚙️ Secure build configuration
```

### 🔒 Protected Content (`content-full/`)
- **Contains**: Complete course materials with full content
- **Security**: NEVER committed to Git, listed in .gitignore
- **Access**: Local development only
- **Backup**: Manual backups to secure storage only

### 📄 Public Content (`content/`)
- **Contains**: Truncated previews with paywall notices
- **Security**: Safe for public GitHub repositories
- **Generated**: Automatically created from `content-full/`
- **Deployment**: This directory is deployed to production

## 🚀 Secure Workflow

### Initial Setup (One Time)

1. **Migrate existing content to secure structure:**
   ```bash
   npm run content:migrate
   ```

2. **Initialize Git with security:**
   ```bash
   git init
   git add .gitignore
   git commit -m "feat: initial security setup"
   ```

### Daily Development Workflow

1. **Edit full content** (always work in `content-full/`):
   ```bash
   # Edit files in content-full/ directory
   vim content-full/sip-protocol/lesson-1.md
   ```

2. **Generate public previews:**
   ```bash
   npm run content:process
   ```

3. **Validate security before commit:**
   ```bash
   npm run security:check
   ```

4. **Secure development:**
   ```bash
   npm run dev:secure
   ```

5. **Secure build/deploy:**
   ```bash
   npm run build:secure
   ```

## 🛠️ Available Scripts

| Command | Purpose | Safety Level |
|---------|---------|--------------|
| `npm run content:migrate` | One-time setup migration | 🔒 Secure |
| `npm run content:process` | Generate public previews | 🔒 Secure |
| `npm run security:check` | Validate security | 🔒 Secure |
| `npm run dev:secure` | Secure development server | 🔒 Secure |
| `npm run build:secure` | Secure production build | 🔒 Secure |
| `npm run dev` | ⚠️ Basic dev (no security checks) | ⚠️ Use secure version |
| `npm run build` | ⚠️ Basic build (no security checks) | ⚠️ Use secure version |

## 🛡️ Security Layers

### Layer 1: .gitignore Protection
- `content-full/` - Full content directory
- `*.full.md` - Full content files
- `*-private.md` - Private files
- Environment and credential files

### Layer 2: Content Processing
- Automatic truncation of full content
- Paywall notices added to public versions
- Character and line limits enforced
- Smart content cutoff at logical points

### Layer 3: Build Security
- Nuxt.js configured to ignore sensitive patterns
- Nitro build excludes full content files
- Security validation before every build

### Layer 4: Git Hooks (Optional)
- Pre-commit hooks can validate security
- Prevent commits containing sensitive patterns
- Automatic security checks

## 🚨 Emergency Procedures

### If Full Content Gets Committed
1. **Stop immediately** - do not push!
2. **Remove from Git history:**
   ```bash
   git reset --soft HEAD~1
   git reset HEAD content-full/
   git commit -m "fix: remove sensitive content"
   ```
3. **If already pushed** - contact repository admin immediately

### If Security Check Fails
1. **Do not proceed** with build/deploy
2. **Run diagnostics:**
   ```bash
   npm run security:check
   ```
3. **Fix reported issues**
4. **Re-validate before continuing**

## 📋 Security Checklist

Before every commit:
- [ ] Only editing files in `content-full/` directory
- [ ] Ran `npm run content:process` to update public previews
- [ ] Ran `npm run security:check` - all checks passed
- [ ] No `.full.md` or `-private.md` files in staging area
- [ ] No `content-full/` directory in Git status

Before every deployment:
- [ ] Ran `npm run build:secure` successfully
- [ ] Security validation passed
- [ ] Only `content/` directory (public previews) included
- [ ] Paywall notices present in public content

## 🎯 Content Creation Guidelines

### Creating New Course Content

1. **Always create in `content-full/`:**
   ```bash
   # ✅ Correct
   vim content-full/new-module/lesson-1.md
   
   # ❌ Wrong - will be public!
   vim content/new-module/lesson-1.md
   ```

2. **Use descriptive frontmatter:**
   ```yaml
   ---
   title: "Advanced SIP Troubleshooting"
   description: "Deep dive into SIP debugging"
   module: "SIP Protocol Mastery"
   lesson: 5
   difficulty: "Advanced"
   duration: "60 minutes"
   ---
   ```

3. **Structure content for good previews:**
   - Start with clear introduction
   - Use descriptive headings
   - Put most valuable content later (gets truncated)

### Public Preview Strategy

The content processor creates previews by:
- Including frontmatter (title, description, etc.)
- Taking first ~2500 characters or 50 lines
- Stopping at logical breakpoints (major headings)
- Adding paywall notice with enrollment CTA

## 🔍 Monitoring & Validation

### Regular Security Audits
- Weekly: Run full security validation
- Before releases: Complete security checklist
- Monthly: Review .gitignore patterns
- Quarterly: Audit access logs and permissions

### Content Quality Checks
- Preview quality: Ensure truncated content makes sense
- Paywall placement: Verify CTAs are effective
- Technical accuracy: Public content should be correct
- SEO optimization: Preview content should be search-friendly

## 📞 Support & Questions

For security concerns or questions about this system:
1. **Check this documentation first**
2. **Run security validation:** `npm run security:check`
3. **Review error messages** - they contain specific guidance
4. **Contact development team** if issues persist

---

**Remember**: When in doubt, run `npm run security:check` - it will tell you exactly what's wrong and how to fix it! 🔒