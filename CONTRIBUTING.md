# Contributing Guidelines

## Git Best Practices

### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Keep first line under 50 characters
- Add detailed description after blank line if needed

Examples:
```
Add PDF search functionality
Fix memory leak in PDF renderer
Update dependencies to latest versions
```

### Branch Strategy
- Create feature branches from `master`
- Use descriptive branch names: `feature/pdf-search`, `fix/memory-leak`
- Keep branches small and focused
- Delete branches after merging

### Before Committing

1. **Run quality checks:**
   ```bash
   make qa  # Runs lint, format, type, and test
   ```

2. **Check for secrets:**
   ```bash
   detect-secrets scan
   gitleaks detect --no-git
   ```

3. **Review changes:**
   ```bash
   git diff --staged
   ```

### Security Checklist
- [ ] No hardcoded passwords, tokens, or API keys
- [ ] No sensitive URLs or connection strings
- [ ] No private keys or certificates
- [ ] Environment variables used for configuration
- [ ] Sensitive data excluded in `.gitignore`

### What NOT to Commit
- API keys, tokens, passwords
- `.env` files (use `.env.example` instead)
- Personal configuration files
- Generated files (logs, uploads, cache)
- Large binary files
- IDE-specific settings

### Pull Request Process
1. Ensure all tests pass
2. Update documentation if needed
3. Add tests for new features
4. Request review from maintainers

## Development Setup

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

Never commit `.env` files!