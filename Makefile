# ESO Builds Tool - Makefile
# Common tasks for development and maintenance

.PHONY: help install test clean lint format setup run-example

# Default target
help:
	@echo "ESO Builds Tool - Available Commands:"
	@echo ""
	@echo "  setup      - Set up the development environment"
	@echo "  install    - Install dependencies"
	@echo "  test       - Run all tests"
	@echo "  test-config - Test configuration manager"
	@echo "  test-abbr  - Test abbreviations"
	@echo "  lint       - Run linting checks"
	@echo "  format     - Format code with black and isort"
	@echo "  clean      - Clean up temporary files"
	@echo "  run-example - Run example Discord webhook"
	@echo "  structure  - Show project structure"
	@echo ""

# Set up development environment
setup:
	@echo "Setting up ESO Builds Tool development environment..."
	@python3 -m venv venv
	@echo "Virtual environment created. Run 'source venv/bin/activate' to activate."
	@echo "Then run 'make install' to install dependencies."

# Install dependencies
install:
	@echo "Installing dependencies..."
	@pip install -r requirements.txt
	@echo "Dependencies installed successfully."

# Run all tests
test:
	@echo "Running all tests..."
	@python3 tests/test_config_manager.py
	@python3 tests/test_abbreviations.py
	@echo "All tests completed."

# Test configuration manager
test-config:
	@echo "Testing configuration manager..."
	@python3 tests/test_config_manager.py

# Test abbreviations
test-abbr:
	@echo "Testing abbreviations..."
	@python3 tests/test_abbreviations.py

# Run linting
lint:
	@echo "Running linting checks..."
	@python3 -m flake8 src/ --max-line-length=100 --ignore=E203,W503
	@echo "Linting completed."

# Format code
format:
	@echo "Formatting code..."
	@python3 -m black src/ tests/ --line-length=100
	@python3 -m isort src/ tests/ --profile=black
	@echo "Code formatting completed."

# Clean up temporary files
clean:
	@echo "Cleaning up temporary files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name ".coverage" -delete
	@echo "Cleanup completed."

# Run example Discord webhook
run-example:
	@echo "Running Discord webhook example..."
	@python3 examples/discord_webhook_example.py

# Show project structure
structure:
	@echo "Project Structure:"
	@tree -I 'venv|__pycache__|*.pyc|.git' -a

# Generate a test report
test-report:
	@echo "Generating test report..."
	@python3 single_report_tool.py N37HBwrjQGYJ6mbv --output all

# Check configuration files
check-config:
	@echo "Checking configuration files..."
	@python3 -c "from src.eso_builds.config_manager import get_config_manager; config = get_config_manager(); print('Config validation:', config.validate_config_files())"
