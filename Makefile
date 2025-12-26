# Copyright (c) 2025- Massimo Rossello
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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