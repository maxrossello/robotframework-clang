#!/usr/bin/env python3
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

import sys
import os
import textwrap
from robot.libdocpkg import LibraryDocumentation

def generate_rst(library_path, output_path):
    # Load library documentation using Robot's Libdoc
    libdoc = LibraryDocumentation(library_path)
    
    with open(output_path, 'w') as f:
        # Title
        f.write("API Reference\n")
        f.write("=============\n\n")
        
        # Library Scope/Version info
        f.write(f"**Library Scope:** ``{libdoc.scope}``\n\n")
        if libdoc.version:
            f.write(f"**Version:** ``{libdoc.version}``\n\n")
            
        f.write(f"{textwrap.dedent(libdoc.doc)}\n\n")
        
        f.write(".. contents:: Keywords\n")
        f.write("   :local:\n   :depth: 1\n\n")
        
        # Keywords
        for i, kw in enumerate(libdoc.keywords):
            # Keyword Title as a subsection
            f.write(f"{kw.name}\n")
            f.write("-" * len(kw.name) + "\n\n")
            
            # Arguments
            args = ", ".join(str(arg) for arg in kw.args)
            if args:
                f.write(f"**Arguments:** ``{args}``\n\n")
            
            # Documentation
            if kw.doc:
                f.write(f"{textwrap.dedent(kw.doc)}\n\n")
            
            # Add explicit spacing but NOT a transition (----) at the end
            # unless we want a visible separator. 
            # In Sphinx themes, headers usually suffice.
            f.write("\n")

if __name__ == "__main__":
    # Adjust paths relative to project root
    src_path = os.path.abspath("src/clang/clang.py")
    out_path = os.path.abspath("docs/api.rst")
    
    print(f"Generating RST from {src_path} to {out_path}...")
    try:
        generate_rst(src_path, out_path)
        print("Done.")
    except Exception as e:
        print(f"Error generating docs: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
