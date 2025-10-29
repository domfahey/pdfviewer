# Support

## Getting Help

We want to help you get the most out of the PDF Viewer POC. Here are the best ways to get support:

### 📚 Documentation

Before asking for help, please check our comprehensive documentation:

- **[README](README.md)** - Quick start and overview
- **[Technical Guide](docs/TECHNICAL.md)** - Detailed setup and development
- **[API Reference](docs/API.md)** - Complete API documentation
- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute
- **[Security Policy](docs/SECURITY.md)** - Security practices
- **[FAQ](#frequently-asked-questions)** - Common questions answered

### 🐛 Found a Bug?

If you've found a bug, please:

1. **Search existing issues** to see if it's already reported
2. **Check the documentation** to ensure it's not expected behavior
3. **Create a bug report** using our [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)

### 💡 Have a Feature Request?

We love hearing your ideas! Please:

1. **Search existing feature requests** to avoid duplicates
2. **Review our roadmap** in [Technical Debt](docs/TECHNICAL_DEBT.md)
3. **Submit a feature request** using our [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)

### ❓ Have a Question?

For general questions:

1. **Check the documentation** first
2. **Review closed issues** - your question might already be answered
3. **Open a discussion** in GitHub Discussions (if enabled)
4. **Email the author** at domfahey@gmail.com for specific inquiries

### 🔒 Security Issues

**Do NOT open public issues for security vulnerabilities.**

Please review our [Security Policy](docs/SECURITY.md) and email security concerns to domfahey@gmail.com.

## Frequently Asked Questions

### Installation & Setup

**Q: Why is libmagic required?**  
A: The backend uses libmagic for secure file type validation. See [Technical Debt](docs/TECHNICAL_DEBT.md#1-replace-libmagic-dependency) for planned improvements.

**Q: Installation fails on Windows?**  
A: python-magic-bin is automatically installed on Windows. If issues persist, install Visual C++ Redistributable.

**Q: How do I fix "libmagic.dylib not found" on macOS?**  
A: Run `brew reinstall libmagic`

### Development

**Q: How do I run tests?**  
A: Use `make test` for all tests, or see [Test Guide](tests/README.md) for specific test categories.

**Q: Pre-commit hooks are failing?**  
A: Run `make qa` to ensure all quality checks pass before committing.

**Q: How do I update dependencies?**  
A: Backend: `uv pip install -U -e ".[dev]"`, Frontend: `npm update`

### Usage

**Q: What's the maximum file size?**  
A: 50MB limit configured for this POC. See [API docs](docs/API.md) for details.

**Q: Can I edit PDFs?**  
A: No, this is a viewer-only POC. See [Limitations](README.md#limitations).

**Q: Does it support authentication?**  
A: No, this is a single-user POC without authentication. See [Limitations](README.md#limitations).

### Contributing

**Q: How do I contribute?**  
A: See our [Contributing Guide](docs/CONTRIBUTING.md) for detailed instructions.

**Q: What coding standards do you use?**  
A: Python: Black + Ruff, TypeScript: ESLint + Prettier. Run `make format` to auto-format.

**Q: Do I need to add tests?**  
A: Yes, new features should include tests. See [Test Guide](tests/README.md).

## Response Times

This is an open-source project maintained by volunteers:

- **Bug reports**: We aim to respond within 1-2 weeks
- **Feature requests**: Response times vary based on complexity
- **Security issues**: Prioritized and addressed ASAP
- **Questions**: Response times may vary

## Community Guidelines

When seeking support:

- ✅ Be respectful and constructive
- ✅ Provide clear, detailed information
- ✅ Search for existing solutions first
- ✅ Follow our [Code of Conduct](docs/CONTRIBUTING.md)
- ❌ Don't demand immediate responses
- ❌ Don't cross-post the same issue
- ❌ Don't share sensitive information publicly

## Additional Resources

- **GitHub Discussions**: (Enable if available)
- **Issue Tracker**: https://github.com/domfahey/pdfviewer/issues
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **License**: [MIT License](LICENSE)

---

**Thank you for using the PDF Viewer POC!** We appreciate your interest and support.
