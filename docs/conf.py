import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

# Configuration file for the Sphinx documentation builder.

project = 'robotframework-clang'
copyright = '2025- Massimo Rossello'
author = 'Massimo Rossello'
release = '0.1.0'
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
    '.txt': 'markdown',
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
    'style_nav_header_background': 'white',
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}
html_css_files = ['sphinx_display.css']
html_js_files = ['sphinx_display.js']

# Ensure LICENSE is available in the build output
html_extra_path = ['../LICENSE']

latex_documents = [(root_doc, 'robotframework-clang.tex', project, author, 'manual')]

numfig = True
