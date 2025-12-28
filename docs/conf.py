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

import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

# Configuration file for the Sphinx documentation builder.

project = 'robotframework-clang'
copyright = '2025- Massimo Rossello'
author = 'Massimo Rossello'
# The full version, including alpha/beta/rc tags
release = '0.1.0'
# The short X.Y version
version = '0.1.0'
root_doc = 'index'

templates_path = ['_templates']
exclude_patterns = ['*.in']
suppress_warnings = ['toc.excluded']
extensions = [
    'sphinx_rtd_theme',
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

pygments_style = 'default'

from pygments.lexers.c_cpp import CppLexer
from sphinx.highlighting import lexers

lexers['c++'] = CppLexer()

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options = {
    'analytics_anonymize_ip': False,
    'logo_only': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Pass display_version directly to the template context
html_context = {
    'display_version': True,
}

html_css_files = ['sphinx_display.css']
html_js_files = ['sphinx_display.js']

# Ensure LICENSE is available in the build output
html_extra_path = ['../LICENSE']

latex_documents = [(root_doc, 'robotframework-clang.tex', project, author, 'manual')]

numfig = True