# Copyright (c) 2025- Massimo Rossello
# 
# Licensed under the Apache License, Version 2.0.

import os
import sys
import subprocess
from jupyter_client import KernelManager

class clang:
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self):
        """
        Initializes the Clang-REPL library. 
        The kernel is NOT started automatically. Call 'Start Kernel' to begin.
        """
        self.km = None
        self.kc = None

    def start_kernel(self, kernel_name='xcpp20'):
        """
        Starts the Clang-REPL kernel (Xeus-cpp).
        This provides an isolated C++ environment.
        """
        if self.km:
            self.shutdown_kernel()

        self.km = KernelManager(kernel_name=kernel_name)
        self.km.start_kernel(stderr=subprocess.DEVNULL)
        self.kc = self.km.client()
        self.kc.start_channels()
        try:
            self.kc.wait_for_ready(timeout=10)
        except RuntimeError:
            self.shutdown_kernel()
            raise RuntimeError("C++ Kernel failed to start. Check your mamba environment.")

        # Force libc++ to ensure isolation from system GCC 13/15
        self.source_exec('%config Interpreter.flags = ["-stdlib=libc++"]')
        self.source_exec('#include <iostream>')
        self.source_exec('#include <stdexcept>')
        self.source_exec('#include <typeinfo>')
        self.source_exec('#include <cxxabi.h>')
        self.source_exec('#include <memory>')
        self.source_exec('#include <cstdlib>')
        
        # Helper for demangling type names
        self.source_exec(r"""
        std::string _robot_demangle(const char* name) {
            int status = -1;
            std::unique_ptr<char, void(*)(void*)> res {
                abi::__cxa_demangle(name, NULL, NULL, &status),
                std::free
            };
            return (status == 0) ? res.get() : name;
        }
        """)

    def shutdown_kernel(self):
        if self.kc:
            self.kc.stop_channels()
            self.kc = None
        if self.km:
            self.km.shutdown_kernel()
            self.km = None

    def add_include_path(self, *paths):
        for p in paths:
            self.source_exec(f'%config Interpreter.flags += ["-I{p}"]')

    def source_include(self, *files):
        for f in files:
            self.source_exec(f'#include "{f}"')

    def source_parse(self, *parts):
        """Defines C++ code (classes, functions) in the JIT session."""
        self.source_exec("\n".join(parts))

    def source_exec(self, *parts):
        """
        Executes C++ code and captures output. 
        Equivalent to source_exec_and_return_output.
        """
        source = "\n".join(parts)
        msg_id = self.kc.execute(source)
        
        output = []
        errors = []
        
        while True:
            try:
                # Poll for messages from the kernel
                msg = self.kc.get_iopub_msg(timeout=5)
                msg_type = msg['header']['msg_type']
                content = msg['content']

                if msg_type == 'stream':
                    output.append(content['text'])
                elif msg_type == 'error':
                    # This captures compilation errors or runtime crashes
                    errors.append("\n".join(content['traceback']))
                
                # 'idle' state means execution is finished
                if msg_type == 'status' and content['execution_state'] == 'idle':
                    break
            except:
                # Timeout or empty queue
                break
                
        if errors:
            # We raise an exception so Robot Framework marks the test as FAILED
            raise Exception(f"C++ Execution Error: {''.join(errors)}")
        
        return "".join(output).strip()

    def source_exec_and_return_output(self, *parts):
        """Legacy compatibility method."""
        return self.source_exec(*parts)

    def load_shared_library(self, *libraries):
        for library in libraries:
            self.source_exec(f'%load_library {library}')

    def assert_(self, cond, otherwise=None):
        """
        Executes an assertion in the C++ kernel.
        """
        # Inclusion of exception is implicit in many modern environments, 
        # but we can add it if needed.
        context_code = f' << " | Context: " << ({otherwise})' if otherwise else ""
        check_code = f"""
        if (!({cond})) {{
            throw std::runtime_error("AssertionError: {cond}" {context_code});
        }}
        """
        try:
            self.source_exec(check_code)
        except Exception as e:
            raise AssertionError(f"C++ Assertion Failed: {cond}") from e

    def get_value(self, obj_expression):
        """Prints a C++ value to stdout to return it to Robot."""
        return self.source_exec(f"std::cout << ({obj_expression});")

    def call_function(self, func, *params):
        """Calls a C++ function and captures its output."""
        params_str = ", ".join(map(str, params))
        return self.source_exec(f"std::cout << {func}({params_str});")

    def typeid(self, expression):
        """Returns the mangled C++ type name of the expression."""
        return self.source_exec(f'std::cout << typeid({expression}).name();')

    def typename(self, expression):
        """Returns the demangled (human-readable) C++ type name of the expression."""
        return self.source_exec(f'std::cout << _robot_demangle(typeid({expression}).name());')

    def nullptr(self):
        """Returns the string representation of nullptr for C++ snippets."""
        return "nullptr"

