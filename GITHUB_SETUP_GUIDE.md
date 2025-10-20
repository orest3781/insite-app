# GitHub Repository Setup Guide

This guide will help you create a GitHub repository for the InSite App project.

---

## Step 1: Initialize Git Repository (Local)

Run these commands in the project directory:

```powershell
# Initialize git repository
git init

# Add all files (respecting .gitignore)
git add .

# Create initial commit
git commit -m "Initial commit: Previewless Insight Viewer - Production Ready"
```

---

## Step 2: Create GitHub Repository (Web)

1. **Go to GitHub:**
   - Navigate to: https://github.com/new
   - Or click the "+" icon → "New repository"

2. **Repository Settings:**
   ```
   Repository name: insite-app
   Description: Local-first document analysis with OCR and AI classification
   Visibility: ☑ Public (or Private if you prefer)
   
   DO NOT initialize with:
   ☐ Add a README file
   ☐ Add .gitignore
   ☐ Choose a license
   ```
   
3. **Click:** "Create repository"

---

## Step 3: Connect Local to GitHub

After creating the repository on GitHub, you'll see a setup page. Use these commands:

```powershell
# Add GitHub as remote origin
git remote add origin https://github.com/YOUR_USERNAME/insite-app.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

**Replace `YOUR_USERNAME`** with your actual GitHub username.

---

## Step 4: Add Repository Details (Web)

Go to your repository settings on GitHub and add:

### About Section
1. Click ⚙️ (gear icon) next to "About"
2. Add description:
   ```
   Local-first document analysis with OCR and AI classification. Process PDFs and images without cloud services.
   ```
3. Add website (optional): Your project URL
4. Add topics (tags):
   ```
   python, ocr, ai, document-processing, pdf, image-processing, 
   tesseract, ollama, pyside6, sqlite, desktop-app, local-first
   ```

### Repository Settings
- Settings → Features:
  - ☑ Wikis (optional)
  - ☑ Issues
  - ☑ Projects (optional)

---

## Step 5: Add License (Recommended)

If you want to add a license:

```powershell
# Create LICENSE file (example: MIT License)
# Copy license text to LICENSE file

git add LICENSE
git commit -m "Add MIT License"
git push
```

**Popular choices:**
- MIT License (permissive)
- GPL v3 (copyleft)
- Apache 2.0 (permissive with patent grant)

---

## Step 6: Create Releases

When ready to release v1.0:

1. **Tag the release:**
   ```powershell
   git tag -a v1.0.0 -m "Release v1.0.0 - Production Ready"
   git push origin v1.0.0
   ```

2. **Create GitHub Release:**
   - Go to: `https://github.com/YOUR_USERNAME/insite-app/releases/new`
   - Choose tag: `v1.0.0`
   - Release title: `v1.0.0 - Production Ready`
   - Description: Copy from `P1_COMPLETE.md` or write release notes
   - Click "Publish release"

---

## Step 7: Set Up GitHub Actions (Optional)

Create `.github/workflows/tests.yml` for automated testing:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: pytest tests/
```

---

## Repository Structure

Your GitHub repository will include:

```
insite-app/
├── .github/                    # GitHub workflows (optional)
├── config/                     # Configuration files
│   ├── presets/
│   ├── prompts/
│   └── themes/
├── data/                       # Database (excluded via .gitignore)
├── docs/                       # Documentation
├── logs/                       # Log files (excluded via .gitignore)
├── models/                     # AI models (excluded via .gitignore)
├── samples/                    # Sample files
├── src/                        # Source code
│   ├── core/                   # Core services
│   ├── models/                 # Database models
│   ├── processing/             # Processing logic
│   ├── ui/                     # UI components
│   └── utils/                  # Utilities
├── tests/                      # Test files
├── .gitignore                  # Git ignore rules
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── main.py                     # Application entry point
├── setup.bat                   # Windows setup script
└── run.bat                     # Windows run script
```

---

## Useful Git Commands

### Daily Workflow
```powershell
# Check status
git status

# Stage changes
git add .

# Commit changes
git commit -m "Your commit message"

# Push to GitHub
git push

# Pull latest changes
git pull
```

### Branch Management
```powershell
# Create new branch
git checkout -b feature/new-feature

# Switch branches
git checkout main

# Merge branch
git merge feature/new-feature

# Delete branch
git branch -d feature/new-feature
```

### Viewing History
```powershell
# View commit history
git log --oneline

# View changes
git diff

# View remote info
git remote -v
```

---

## Best Practices

### Commit Messages
Use clear, descriptive commit messages:
- ✅ "Fix: Resolve database attribute error in menu handlers"
- ✅ "Feature: Add processed files viewer with file operations"
- ✅ "Docs: Update README with installation instructions"
- ❌ "fixed stuff"
- ❌ "update"

### Branching Strategy
- `main` - production-ready code
- `develop` - integration branch
- `feature/*` - new features
- `bugfix/*` - bug fixes
- `hotfix/*` - critical fixes

### Commit Frequency
- Commit logical units of work
- Don't commit broken code to main
- Push at least daily

---

## Troubleshooting

### "Permission denied" error
```powershell
# Use HTTPS instead of SSH
git remote set-url origin https://github.com/YOUR_USERNAME/insite-app.git
```

### "Repository not found"
```powershell
# Verify remote URL
git remote -v

# Update URL if incorrect
git remote set-url origin https://github.com/YOUR_USERNAME/insite-app.git
```

### Large files error
```powershell
# Remove large files from git
git rm --cached path/to/large/file

# Add to .gitignore
echo "path/to/large/file" >> .gitignore

# Commit
git add .gitignore
git commit -m "Remove large files, update .gitignore"
```

---

## Repository URL

Once created, your repository will be available at:
```
https://github.com/YOUR_USERNAME/insite-app
```

---

## Next Steps After Setup

1. **Add repository badges** to README (build status, version, license)
2. **Create CONTRIBUTING.md** if you want contributors
3. **Set up GitHub Pages** for documentation (optional)
4. **Enable Dependabot** for security updates
5. **Add code owners** file (CODEOWNERS)
6. **Configure branch protection** rules (for main branch)

---

## Resources

- [GitHub Docs](https://docs.github.com/)
- [Git Handbook](https://guides.github.com/introduction/git-handbook/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

---

**Status:** Ready to create repository  
**Last Updated:** October 19, 2025
