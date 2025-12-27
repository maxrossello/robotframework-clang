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
import subprocess
from jupyter_client import KernelManager

class clang:
    """
    Robot Framework library for interactive C++ execution using **Clang-REPL** (via xeus-cpp).

    This library allows you to write, execute, and test C++ code snippets directly within Robot Framework test suites.
    It relies on a Jupyter kernel (specifically ``xeus-cpp``) to maintain a persistent C++ interpreter session.

    **Key Features:**
    
    - **JIT Compilation**: No need to create a `main.cpp` or compile a binary.
    - **State Persistence**: Variables defined in one test case (within the same suite/session) are available in subsequent ones.
    - **Modern C++**: Supports C++20 and potentially C++ modules.
    - **Libc++ Support**: Configured to use LLVM's libc++ by default.

    **Basic Usage Example:**

    .. code-block:: robotframework

        *** Settings ***
        Library    clang

        *** Test Cases ***
        Example Test
            Start Kernel
            Source Exec    int answer = 42;
            ${result}=     Source Exec    std::cout << answer;
            Should Be Equal    ${result}    42
            Shutdown Kernel
    """
    
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self):
        """
        Initializes the library instance. 
        
        Note: This does **not** start the C++ kernel. You must call `Start Kernel` explicitly.
        """
        self.km = None
        self.kc = None
        self.includes = []

    def start_kernel(self, kernel_name='xcpp20'):
        """
        Starts the Clang-REPL kernel (Xeus-cpp) in a subprocess.

        This keyword must be called before executing any C++ code. It initializes the 
        standard library and prepares the environment.

        **Arguments:**

        - ``kernel_name``: The name of the Jupyter kernel to use. Defaults to ``xcpp20``. 
          Ensure this kernel is installed in your environment (``jupyter kernelspec list``).

        The initialization process also defines a helper function ``_robot_demangle`` 
        to assist with type introspection.
        
        It configures the kernel to use ``libc++``.

        **Example:**

        | Start Kernel | kernel_name=xcpp17 |
        """
        if self.km:
            self._stop_kernel()

        self.km = KernelManager(kernel_name=kernel_name)
        self.km.start_kernel(stderr=subprocess.DEVNULL)
        
        self.kc = self.km.client()
        self.kc.start_channels()
        try:
            self.kc.wait_for_ready(timeout=10)
        except RuntimeError:
            self._stop_kernel()
            raise RuntimeError("C++ Kernel failed to start. Check your mamba environment.")

        # Configure kernel via magics
        try:
            self.source_exec('%config Interpreter.flags += ["-stdlib=libc++"]')
            # Try adding include paths via magic as well, for compiler-level resolution
            for p in self.includes:
                self.source_exec(f'%config Interpreter.flags += ["-I{p}"]')
        except Exception as e:
            self._stop_kernel()
            raise RuntimeError(f"Failed to configure kernel: {e}")

        # Standard headers
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

    def _stop_kernel(self):
        """Internal helper to stop the kernel process without clearing config."""
        if self.kc:
            self.kc.stop_channels()
            self.kc = None
        if self.km:
            self.km.shutdown_kernel()
            self.km = None

    def shutdown_kernel(self):
        """
        Stops the running C++ kernel and cleans up resources.

        This also clears the accumulated include paths.
        """
        self._stop_kernel()
        self.includes = []

    def add_include_path(self, *paths):
        """
        Adds directories to the C++ include search path (equivalent to ``-I`` flag).
        
        Paths added here are used by `Start Kernel` (at startup) and `Source Include` 
        (to resolve header files).

        **Arguments:**

        - ``paths``: One or more directory paths to add.

        **Example:**

        | Add Include Path | /opt/mylib/include | ${CURDIR}/../include |
        """
        for p in paths:
            abs_p = os.path.abspath(p)
            if abs_p not in self.includes:
                self.includes.append(abs_p)

    def source_include(self, *files):
        """
        Includes header files in the current session.

        This keyword attempts to resolve the provided file names. If a file is not
        found in the current directory, it searches through the paths added via
        `Add Include Path` and uses an absolute path if a match is found.

        **Arguments:**

        - ``files``: Names of the header files to include (e.g., ``vector``, ``myheader.h``).

        **Example:**

        | Source Include | vector | map |
        """
        for f in files:
            target = f
            # If not an absolute path and file doesn't exist locally, 
            # resolve it using registered include paths
            if not os.path.isabs(f) and not os.path.exists(f):
                for p in self.includes:
                    full_path = os.path.join(p, f)
                    if os.path.exists(full_path):
                        target = full_path
                        print(f"*INFO* Resolved {f} to {target}")
                        break
            
            self.source_exec(f'#include "{target}"')

    def source_parse(self, *parts):
        """
        Defines C++ code structure (declarations) without expecting output.
        
        Useful for defining classes, functions, or globals.
        Alias for `Source Exec`.

        **Arguments:**

        - ``parts``: Lines of C++ code.
        """
        self.source_exec("\n".join(parts))

    def source_exec(self, *parts):
        """
        Executes C++ code and returns the standard output.

        This is the primary keyword for interacting with the REPL. 
        If the C++ code prints to ``std::cout``, that output is captured and returned.
        If the code throws an exception or fails to compile, the test fails.

        **Arguments:**

        - ``parts``: One or more strings constituting the C++ code to run.

        **Returns:**

        - The captured ``stdout`` as a string, stripped of trailing whitespace.

        **Example:**

        | ${out}= | Source Exec | std::cout << "Hello"; |
        """
        source = "\n".join(parts)
        if not self.kc:
            raise RuntimeError("Kernel client not initialized. Did you call 'Start Kernel'?")

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
        """
        Legacy alias for `Source Exec`.
        """
        return self.source_exec(*parts)

    def load_shared_library(self, *libraries):
        """
        Loads a shared object (.so) or dynamic library (.dylib/dll) into the process.

        **Arguments:**

        - ``libraries``: Paths or names of libraries to load.

        **Example:**

        | Load Shared Library | /usr/lib/libm.so |
        """
        for library in libraries:
            self.source_exec(f'%load_library {library}')

    def assert_(self, cond, otherwise=None):
        """
        Evaluates a C++ boolean condition and fails the test if it is false.

        **Arguments:**

        - ``cond``: A string containing a C++ expression that evaluates to ``bool``.
        - ``otherwise``: Optional message or value to print/include in the error if the assertion fails.

        **Example:**

        | Source Exec | int x = 5; |
        | Assert | x > 0 | Context: x should be positive |
        | Assert | x == 5 |
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
        """
        Retrieves the string representation of a C++ expression/variable.

        Basically executes ``std::cout << (expression)`` and returns the result.

        **Arguments:**

        - ``obj_expression``: The C++ variable or expression to evaluate.

        **Example:**

        | Source Exec | int x = 100; |
        | ${val}= | Get Value | x * 2 |
        | Should Be Equal | ${val} | 200 |
        """
        return self.source_exec(f"std::cout << ({obj_expression});")

    def call_function(self, func, *params):
        """
        Calls a global C++ function with the provided arguments and returns its output.

        **Arguments:**

        - ``func``: Name of the function to call.
        - ``params``: Arguments to pass to the function.

        **Example:**

        | Source Exec | int add(int a, int b) {{ return a + b; }} |
        | ${res}= | Call Function | add | 2 | 3 |
        """
        params_str = ", ".join(map(str, params))
        return self.source_exec(f"std::cout << {func}({params_str});")

    def typeid(self, expression):
        """
        Returns the **mangled** C++ type name of an expression (using ``typeid(...).name()``).

        **Arguments:**

        - ``expression``: The object or type to inspect.
        """
        return self.source_exec(f'std::cout << typeid({expression}).name();')

    def typename(self, expression):
        """
        Returns the **demangled** (human-readable) C++ type name of an expression.

        Uses ``abi::__cxa_demangle`` internally.

        **Arguments:**

        - ``expression``: The object or type to inspect.

        **Example:**

        | ${name}= | Typename | std::string("foo") |
        | Should Contain | ${name} | string |
        """
        return self.source_exec(f'std::cout << _robot_demangle(typeid({expression}).name());')

    def nullptr(self):
        """
        Returns the string ``nullptr``. 
        
        Helper to represent the null pointer in keyword arguments.
        """
        return "nullptr"
