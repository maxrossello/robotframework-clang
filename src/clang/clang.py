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
        self.link_dirs = []
        self.link_libs = []

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

        if self.includes:
            new_inc_env = os.path.pathsep.join(self.includes)
            for var in ['CPLUS_INCLUDE_PATH', 'CPATH']:
                existing = os.environ.get(var, '')
                os.environ[var] = os.pathsep.join([new_inc_env, existing]) if existing else new_inc_env

        if self.link_dirs:
            new_lib_env = os.path.pathsep.join(self.link_dirs)
            vars_to_update = ['LD_LIBRARY_PATH', 'LIBRARY_PATH', 'DYLD_LIBRARY_PATH']
            if sys.platform == 'win32':
                vars_to_update.append('PATH')
            for var in vars_to_update:
                existing = os.environ.get(var, '')
                os.environ[var] = os.pathsep.join([new_lib_env, existing]) if existing else new_lib_env

        # Windows Kernel Discovery Fix
        prefix = os.environ.get('CONDA_PREFIX') or sys.prefix
        if prefix:
            potential_paths = [
                os.path.join(prefix, 'share', 'jupyter'),
                os.path.join(prefix, 'Library', 'share', 'jupyter')
            ]
            current_jupyter_path = os.environ.get('JUPYTER_PATH', '')
            path_list = current_jupyter_path.split(os.pathsep) if current_jupyter_path else []
            updated = False
            for p in potential_paths:
                if os.path.exists(p) and p not in path_list:
                    path_list.insert(0, p)
                    updated = True
            if updated:
                os.environ['JUPYTER_PATH'] = os.pathsep.join(path_list)

        try:
            self.km = KernelManager(kernel_name=kernel_name)
            extra_args = []
            if sys.platform == 'win32':
                # Configure Windows Linking
                # We need to tell Clang-REPL where to find the standard libraries.
                # In a Conda environment, these are in <prefix>/Library/lib.
                if sys.prefix:
                    lib_path = os.path.join(sys.prefix, 'Library', 'lib')
                    if os.path.exists(lib_path):
                        extra_args.append(f'-L{lib_path}')

                # Debugging: Check library existence
                print(f"DEBUG: sys.prefix is {sys.prefix}")
                lib_paths_from_env = os.environ.get('LIB', '').split(os.pathsep)
                print(f"DEBUG: LIB environment variable: {os.environ.get('LIB', 'Not set')}")
                
                required_libs = ["msvcp140.lib", "vcruntime140.lib", "ucrt.lib"]
                
                # Check conda env lib path first
                conda_lib_path = os.path.join(sys.prefix, 'Library', 'lib')
                print(f"DEBUG: Checking conda lib path: {conda_lib_path}")
                if os.path.exists(conda_lib_path):
                    for lib_name in required_libs:
                        full_path = os.path.join(conda_lib_path, lib_name)
                        if os.path.exists(full_path):
                            print(f"DEBUG: Found {lib_name} at {full_path}")
                        else:
                            print(f"DEBUG: WARNING: {lib_name} not found in {conda_lib_path}")

                # Check paths from LIB env var
                found_all_libs_in_lib = True
                for lib_name in required_libs:
                    found_lib = False
                    for path in lib_paths_from_env:
                        if not path: continue
                        full_path = os.path.join(path, lib_name)
                        if os.path.exists(full_path):
                            print(f"DEBUG: Found {lib_name} at {full_path} (from LIB env var)")
                            found_lib = True
                            break
                    if not found_lib:
                        print(f"DEBUG: WARNING: {lib_name} not found in any LIB path.")
                        found_all_libs_in_lib = False
                
                if not found_all_libs_in_lib:
                    print("DEBUG: Some required libraries were not found in LIB env var. This might be the cause of linking errors.")

                # Explicitly link against MSVC and UCRT runtimes
                # This ensures symbols like std::string, std::cout, type_info are found.
                extra_args.extend([
                    "-lmsvcp140",
                    "-lvcruntime140",
                    "-lucrt",
                    "-fms-extensions",
                    "-fms-compatibility",
                    "-fdelayed-template-parsing",
                    "-fexceptions",
                    "-fcxx-exceptions",
                    "-std=c++20"
                ])
            else:
                extra_args.extend(["-stdlib=libc++", "-std=c++20"])
                            
            self.km.start_kernel(stderr=subprocess.DEVNULL, extra_arguments=extra_args)
        except Exception as e:
            raise RuntimeError(f"Failed to start C++ Kernel '{kernel_name}': {e}")
        
        self.kc = self.km.client()
        self.kc.start_channels()
        try:
            self.kc.wait_for_ready(timeout=20)
        except RuntimeError:
            self._stop_kernel()
            raise RuntimeError("Kernel timed out at startup.")

        common_headers = [
            '#include <iostream>', '#include <string>', '#include <stdexcept>',
            '#include <vector>', '#include <memory>', '#include <typeinfo>',
            '#include <cstdlib>'
        ]
        
        if sys.platform == 'win32':
            common_headers.append('#include <windows.h>')
        else:
            common_headers.extend(['#include <dlfcn.h>', '#include <cxxabi.h>'])

        try:
            self.source_exec('\n'.join(common_headers), timeout=30)
        except Exception as e:
            self._stop_kernel()
            raise RuntimeError(f"Failed to load standard headers: {e}")

        cpp_helpers = ""
        
        if sys.platform == 'win32':
            # --- WINDOWS IMPLEMENTATION ---
            cpp_helpers = r"""
            void* _robot_load_lib(const char* path) {
                std::string p = path;
                for (auto &c : p) if (c == '/') c = '\\';
                HMODULE h = LoadLibrary(p.c_str());
                if (!h) {
                    DWORD err = GetLastError();
                    std::cout << "DEBUG: LoadLibrary failed for " << p << " Error: " << err << std::endl;
                    throw std::runtime_error("LoadLibrary failed: " + p);
                }
                return static_cast<void*>(h);
            }
            std::string _robot_demangle(const char* name) {
                return std::string(name);
            }
            """
        else:
            # --- LINUX/MAC IMPLEMENTATION ---
            cpp_helpers = r"""
            void* _robot_load_lib(const char* path) {
                // RTLD_GLOBAL is crucial for symbols to be seen by subsequent JIT code
                void* h = dlopen(path, RTLD_NOW | RTLD_GLOBAL); 
                if (!h) {
                    const char* err = dlerror();
                    std::cout << "DEBUG: dlopen failed for " << path << " Error: " << (err ? err : "unknown") << std::endl;
                    throw std::runtime_error("dlopen failed: " + std::string(err ? err : "unknown"));
                }
                return h;
            }

            std::string _robot_demangle(const char* name) {
                int status = -1;
                // __cxa_demangle allocates memory that must be freed
                char* res = abi::__cxa_demangle(name, NULL, NULL, &status);
                if (status == 0 && res != NULL) {
                    std::string demangled(res);
                    std::free(res); // Important: free the buffer
                    return demangled;
                }
                return std::string(name);
            }
            """

        try:
            self.source_exec(cpp_helpers, timeout=30)
        except Exception as e:
            self._stop_kernel()
            raise RuntimeError(f"Failed to inject helper functions: {e}")
        
        for lib_name in self.link_libs:
            self._safe_load_library(lib_name)

    def _safe_load_library(self, lib_name):
        """Helper interno per gestire la logica di path search delle librerie"""
        resolved_path = None
        candidates = []
        
        if sys.platform == 'win32':
            if not lib_name.lower().endswith('.dll'): candidates.append(f"{lib_name}.dll")
            candidates.append(lib_name)
        else:
            if not lib_name.endswith(('.so', '.dylib', '.dll')):
                candidates.extend([f"lib{lib_name}.dylib", f"lib{lib_name}.so", lib_name])
            else:
                candidates.append(lib_name)
        
        for cand in candidates:
            for d in self.link_dirs:
                path = os.path.join(d, cand)
                if os.path.exists(path):
                    resolved_path = os.path.abspath(path)
                    break
            if resolved_path: break
        
        target = resolved_path if resolved_path else candidates[0]
        # Normalize path for C++ string (handle Windows backslashes)
        safe_target = target.replace("\\", "/")
        try:
            self.source_exec(f'_robot_load_lib("{safe_target}");')
        except Exception as e:
             self._stop_kernel()
             raise RuntimeError(f"Failed to load linked library {lib_name}: {e}")
                     
    def _stop_kernel(self):
        """Internal helper to stop the kernel process without clearing config."""
        if self.kc:
            try:
                self.kc.stop_channels()
            except:
                pass
            self.kc = None
        if self.km:
            try:
                if self.km.has_kernel:
                    self.km.shutdown_kernel()
            except:
                pass
            self.km = None

    def shutdown_kernel(self):
        """
        Stops the running C++ kernel and cleans up resources.

        This also clears the accumulated include paths and link settings.
        """
        self._stop_kernel()
        self.includes = []
        self.link_dirs = []
        self.link_libs = []

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

    def add_link_directory(self, *paths):
        """
        Adds directories to the linker search path (equivalent to ``-L`` flag).
        
        Must be called **before** `Start Kernel`.

        **Arguments:**

        - ``paths``: One or more directory paths to add.
        """
        for p in paths:
            abs_p = os.path.abspath(p)
            if abs_p not in self.link_dirs:
                self.link_dirs.append(abs_p)

    def link_libraries(self, *libs):
        """
        Specifies libraries to link against at startup (equivalent to ``-l`` flag).

        Must be called **before** `Start Kernel`.
        
        **Arguments:**

        - ``libs``: Names of libraries (e.g., ``m`` for libm, ``pthread``).
        """
        for l in libs:
            if l not in self.link_libs:
                self.link_libs.append(l)

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

    def source_exec(self, *parts, timeout=30):
        """
        Executes C++ code and returns the standard output.

        This is the primary keyword for interacting with the REPL. 
        If the C++ code prints to ``std::cout``, that output is captured and returned.
        If the code throws an exception or fails to compile, the test fails.

        **Arguments:**

        - ``parts``: One or more strings constituting the C++ code to run.
        - ``timeout``: Maximum time (seconds) to wait for kernel response. Default 30s.

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
                msg = self.kc.get_iopub_msg(timeout=timeout)
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
                # Timeout or empty queue - assume timeout if we haven't seen 'idle'
                if not errors:
                    raise TimeoutError(f"C++ execution timed out (no response from kernel for {timeout}s).")
                break
                
        if errors:
            # We raise an exception so Robot Framework marks the test as FAILED
            raise Exception(f"C++ Execution Error: {''.join(errors)}")
        
        return "".join(output).strip()

    def load_shared_library(self, *libraries):
        """
        Loads a shared object (.so) or dynamic library (.dylib/dll) into the process via ``dlopen``.

        This allows calling functions from shared libraries that are not linked at startup.
        Ensure symbols are loaded with global visibility (RTLD_GLOBAL).

        **Arguments:**

        - ``libraries``: Paths or names of libraries to load.

        **Example:**

        | Load Shared Library | /usr/lib/libm.so |
        """
        for lib in libraries:
            # Su Windows bisogna raddoppiare i backslash per le stringhe C++
            # O meglio, forzare l'uso di forward slash che Windows supporta
            safe_lib = lib.replace("\\", "/")
            
            # Chiamata alla funzione C++ definita nello shim
            self.source_exec(f'_robot_load_lib("{safe_lib}");')

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
