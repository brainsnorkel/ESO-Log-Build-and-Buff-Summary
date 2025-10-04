# Contributing to ESO Top Builds

Thank you for your interest in contributing to ESO Top Builds! This document provides guidelines for contributing to the project.

## 🌟 How to Contribute

### Reporting Issues

- **Bug Reports**: Use the GitHub issue tracker to report bugs
- **Feature Requests**: Describe the feature and why it would be useful
- **Questions**: Feel free to ask questions about usage or implementation

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Test your changes**: Run the test suite
5. **Commit your changes**: Use clear, descriptive commit messages
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Submit a Pull Request**: Target the `develop` branch

## 📋 Development Guidelines

### Branch Strategy

- **`main`**: Production-ready code
- **`develop`**: Integration branch for features
- **`feature/*`**: Feature development branches
- **`bugfix/*`**: Bug fix branches

### Commit Messages

Use clear, descriptive commit messages:

```
Add set abbreviations to Discord webhook reports

- Import abbreviate_set_name function
- Apply set abbreviations to webhook reports
- Remove comment about not using abbreviations
```

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

### Testing

- Run existing tests: `pytest tests/`
- Add tests for new features (see user rules)
- Document test cases in TESTING.md

### Configuration Files

When adding new abbreviations or mappings:

- **`config/ability_abbreviations.json`**: Ability name abbreviations
- **`config/set_abbreviations.json`**: Gear set abbreviations
- **`config/skill_line_abbreviations.json`**: Skill line abbreviations
- **`config/build_name_mappings.json`**: Common build combinations

## 🧪 Testing

Before submitting a PR:

```bash
# Run tests
pytest tests/ -v

# Test with a real report
python single_report_tool.py <report_code> --output discord --discord-webhook-post

# Check for linting issues
flake8 src/
```

## 📝 Documentation

- Update relevant documentation when adding features
- Add examples for new functionality
- Update README.md if changing user-facing behavior
- Document breaking changes clearly

## 🔄 Pull Request Process

1. **Update documentation** for any user-facing changes
2. **Add tests** for new features
3. **Update CHANGELOG.md** with your changes
4. **Ensure all tests pass**
5. **Request review** from maintainers

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts with develop
- [ ] Commit messages are clear and descriptive

## 🎯 Areas for Contribution

### High Priority

- Additional set abbreviations and build name mappings
- Performance optimizations for large reports
- Additional trial support
- UI/UX improvements for Discord reports

### Good First Issues

- Add missing ability abbreviations
- Improve error messages
- Add more unit tests
- Documentation improvements

## 🤝 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help maintain a positive community

## 📧 Contact

- **GitHub Issues**: For bugs and feature requests
- **Pull Requests**: For code contributions
- **Discussions**: For general questions and ideas

## 🙏 Thank You!

Your contributions help make ESO Top Builds better for everyone!

