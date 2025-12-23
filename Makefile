.PHONY: docs tests clean

# Variables
DOCS_DIR = docs
BUILD_DIR = html

# Generate HTML documentation
docs:
	python3 utils/libdoc2rst.py
	sphinx-build -b html $(DOCS_DIR) $(BUILD_DIR)
	@echo "Documentation built in $(BUILD_DIR)"

# Run tests (using the .rst file as source)
tests:
	robot --extension rst $(DOCS_DIR)/tests.rst

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR) docs/_build
	rm -rf output.xml log.html report.html
