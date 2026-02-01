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
        if self.km: self._stop_kernel()
        if self.includes:
            new_inc_env = os.pathsep.join(self.includes)
            for var in ['CPLUS_INCLUDE_PATH', 'CPATH']:
                existing = os.environ.get(var, '')
                os.environ[var] = os.pathsep.join([new_inc_env, existing]) if existing else new_inc_env
        if self.link_dirs:
            new_lib_env = os.pathsep.join(self.link_dirs)
            vars_to_update = ['LD_LIBRARY_PATH', 'LIBRARY_PATH', 'DYLD_LIBRARY_PATH']
            if sys.platform == 'win32': vars_to_update.append('PATH')
            for var in vars_to_update:
                existing = os.environ.get(var, '')
                os.environ[var] = os.pathsep.join([new_lib_env, existing]) if existing else new_lib_env

        prefix = os.environ.get('CONDA_PREFIX') or sys.prefix
        discovered_libs, new_incs = [], []
        if sys.platform == 'win32' and prefix:
            new_paths = [os.path.join(prefix, 'Library', 'bin'), os.path.join(prefix, 'bin')]
            new_libs = [os.path.join(prefix, 'Library', 'lib')]
            new_incs = [os.path.join(prefix, 'Library', 'include')]
            try:
                import json
                vswhere = os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Microsoft Visual Studio', 'Installer', 'vswhere.exe')
                if not os.path.exists(vswhere):
                    try:
                        v_p = subprocess.check_output(['where', 'vswhere'], shell=False).decode().splitlines()[0].strip()
                        if os.path.exists(v_p): vswhere = v_p
                    except: vswhere = None
                if vswhere and os.path.exists(vswhere):
                    out = subprocess.check_output([vswhere, '-latest', '-products', '*', '-format', 'json'], shell=False, cwd='C:\\')
                    info = json.loads(out)
                    if info:
                        install_path = info[0]['installationPath']
                        tools_path = os.path.join(install_path, 'VC', 'Tools', 'MSVC')
                        if os.path.exists(tools_path):
                            versions = sorted(os.listdir(tools_path), reverse=True)
                            if versions:
                                v = versions[0]; new_incs.append(os.path.join(tools_path, v, 'include'))
                                discovered_libs.append(os.path.join(tools_path, v, 'lib', 'x64'))
                        sdk_base = os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Windows Kits', '10')
                        sdk_inc_base = os.path.join(sdk_base, 'Include')
                        if os.path.exists(sdk_inc_base):
                            sdk_versions = sorted(os.listdir(sdk_inc_base), reverse=True)
                            if sdk_versions:
                                sv = sdk_versions[0]
                                for sub in ['ucrt', 'shared', 'um', 'winrt']:
                                    p = os.path.join(sdk_inc_base, sv, sub)
                                    if os.path.exists(p): new_incs.append(p)
                                for sub in ['ucrt', 'um']:
                                    p = os.path.join(sdk_base, 'Lib', sv, sub, 'x64')
                                    if os.path.exists(p): discovered_libs.append(p)
            except Exception as e: print(f"*WARN* MSVC discovery failed: {e}")
            os.environ['PATH'] = os.pathsep.join(filter(None, new_paths + [os.environ.get('PATH', '')]))
            os.environ['LIB'] = os.pathsep.join(filter(None, discovered_libs + new_libs + [os.environ.get('LIB', '')]))
            os.environ['INCLUDE'] = os.pathsep.join(filter(None, new_incs + [os.environ.get('INCLUDE', '')]))
            p_paths = [os.path.join(prefix, 'share', 'jupyter'), os.path.join(prefix, 'Library', 'share', 'jupyter'), os.path.join(os.environ.get('ALLUSERSPROFILE', 'C:\\ProgramData'), 'jupyter')]
            cur_j = os.environ.get('JUPYTER_PATH', '')
            path_list = cur_j.split(os.pathsep) if cur_j else []
            for p in p_paths:
                if os.path.exists(p) and p not in path_list: path_list.insert(0, p)
            os.environ['JUPYTER_PATH'] = os.pathsep.join(path_list)

        try:
            self.km = KernelManager(kernel_name=kernel_name)
            extra_args = ["-std=c++20"]
            if sys.platform == 'win32':
                extra_args.extend(["-D_DLL", "-D_MT", "-D_CRT_SECURE_NO_WARNINGS", "-fms-extensions", "-fms-compatibility", "-fms-runtime-lib=dll", "-fno-sized-deallocation", "-Xlinker", "/NODEFAULTLIB:libcmt", "-lmsvcprt", "-lmsvcrt", "-lvcruntime", "-lucrt"])
                if prefix:
                    for lp in discovered_libs + [os.path.join(prefix, 'Library', 'lib')]:
                        if lp and os.path.exists(lp):
                            lp_f = lp.replace("\\", "/"); extra_args.append(f'-L{lp_f}')
                for ip in new_incs:
                    if ip and os.path.exists(ip):
                        ip_f = ip.replace("\\", "/"); extra_args.append(f'-I{ip_f}')
            self.km.start_kernel(stderr=subprocess.DEVNULL, extra_arguments=extra_args)
        except Exception as e: raise RuntimeError(f"Failed to start C++ Kernel '{kernel_name}': {e}")
        
        self.kc = self.km.client(); self.kc.start_channels()
        try: self.kc.wait_for_ready(timeout=60)
        except RuntimeError: self._stop_kernel(); raise RuntimeError("Kernel timed out at startup.")

        if sys.platform == 'win32':
            bootstrap_cpp = r"""
            extern "C" __declspec(dllimport) void* __stdcall _robot_internal_load_lib(const char*) __asm__("LoadLibraryA");
            using _robot_size_t = decltype(sizeof(0));
            extern "C" void* _robot_internal_malloc(_robot_size_t) __asm__("malloc");
            extern "C" void _robot_internal_free(void*) __asm__("free");
            extern "C" void* _robot_init_runtimes() {
                _robot_internal_load_lib("msvcp140.dll"); _robot_internal_load_lib("msvcp140_1.dll"); _robot_internal_load_lib("msvcp140_2.dll");
                _robot_internal_load_lib("vcruntime140.dll"); _robot_internal_load_lib("vcruntime140_1.dll"); _robot_internal_load_lib("ucrtbase.dll");
                _robot_internal_load_lib("msvcrt.dll"); _robot_internal_load_lib("msvcprt.dll"); return (void*)1;
            }
            static void* _dummy_init = _robot_init_runtimes();
            struct __type_info_node { void* _Mem; struct __type_info_node* _Next; };
            __declspec(selectany) struct __type_info_node __robot_type_info_root __asm__("?__type_info_root_node@@3U__type_info_node@@A") = { 0, 0 };
            __declspec(selectany) void* __robot_type_info_vtable [16] __asm__("??_7type_info@@6B@") = { 0 };
            void operator delete(void* p, _robot_size_t n) noexcept { _robot_internal_free(p); }
            """
            try: self.source_exec(bootstrap_cpp, timeout=60)
            except Exception as e: print(f"*WARN* Windows bootstrap failed: {e}")

        common_headers = ['#include <iostream>', '#include <string>', '#include <stdexcept>', '#include <vector>', '#include <memory>', '#include <typeinfo>', '#include <cstdlib>']
        if sys.platform != 'win32': common_headers.extend(['#include <dlfcn.h>', '#include <cxxabi.h>'])
        for header in common_headers:
            try: self.source_exec(header, timeout=60)
            except Exception as e:
                print(f"*WARN* Failed to load {header}: {e}")
                if '<iostream>' in header: self._stop_kernel(); raise RuntimeError(f"Critical header failed: {header}")

        if sys.platform == 'win32':
            cpp_helpers = r"""
            #include <string>
            #include <iostream>
            extern "C" void* _robot_load_lib(const char* path) {
                std::string p = path; for (auto &c : p) if (c == '/') c = '\\';
                void* h = _robot_internal_load_lib(p.c_str());
                if (!h) std::cout << "DEBUG: LoadLibrary failed for " << p << std::endl;
                return h;
            }
            std::string _robot_demangle(const char* name) { return std::string(name); }
            """
        else:
            cpp_helpers = r"""
            void* _robot_load_lib(const char* path) {
                void* h = dlopen(path, RTLD_NOW | RTLD_GLOBAL); 
                if (!h) { const char* err = dlerror(); throw std::runtime_error("dlopen failed: " + std::string(err ? err : "unknown")); }
                return h;
            }
            std::string _robot_demangle(const char* name) {
                int status = -1; char* res = abi::__cxa_demangle(name, NULL, NULL, &status);
                if (status == 0 && res != NULL) { std::string demangled(res); std::free(res); return demangled; }
                return std::string(name);
            }
            """
        try: self.source_exec(cpp_helpers, timeout=60)
        except Exception as e: self._stop_kernel(); raise RuntimeError(f"Failed to inject helper functions: {e}")
        for lib_name in self.link_libs: self._safe_load_library(lib_name)

    def _safe_load_library(self, lib_name):
        resolved_path = None
        candidates = []
        if sys.platform == 'win32':
            if not lib_name.lower().endswith('.dll'): candidates.append(f"{lib_name}.dll")
            candidates.extend([lib_name, f"lib{lib_name}.dll"])
        else:
            if not lib_name.endswith(('.so', '.dylib', '.dll')): candidates.extend([f"lib{lib_name}.dylib", f"lib{lib_name}.so", lib_name])
            else: candidates.append(lib_name)
        for cand in candidates:
            for d in self.link_dirs:
                path = os.path.join(d, cand)
                if os.path.exists(path): resolved_path = os.path.abspath(path); break
            if resolved_path: break
        target = resolved_path if resolved_path else candidates[0]
        target_f = target.replace("\\", "/")
        try: self.source_exec(f'_robot_load_lib("{target_f}");', timeout=60)
        except Exception as e: self._stop_kernel(); raise RuntimeError(f"Failed to load linked library {lib_name}: {e}")
                     
    def _stop_kernel(self):
        """Internal helper to stop the kernel process without clearing config."""
        if self.kc:
            try: self.kc.stop_channels()
            except: pass
            self.kc = None
        if self.km:
            try:
                if self.km.has_kernel: self.km.shutdown_kernel()
            except: pass
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

    def source_file(self, path):
        """
        Reads a C++ source file and executes its content in the REPL.

        **Arguments:**

        - ``path``: Path to the C++ source file (.cpp, .h, etc.).

        **Example:**

        | Source File | ${CURDIR}/my_impl.cpp |
        """
        with open(path, 'r') as f:
            content = f.read()
        return self.source_exec(content)

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
        output, errors = [], []
        while True:
            try:
                msg = self.kc.get_iopub_msg(timeout=timeout)
                msg_type = msg['header']['msg_type']
                content = msg['content']
                if msg_type == 'stream': output.append(content['text'])
                elif msg_type == 'error': errors.append("\n".join(content['traceback']))
                if msg_type == 'status' and content['execution_state'] == 'idle': break
            except:
                if not errors:
                    raise TimeoutError(f"C++ execution timed out (no response from kernel for {timeout}s).")
                break
        if errors:
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
            lib_f = lib.replace("\\", "/")
            self.source_exec(f'_robot_load_lib("{lib_f}");', timeout=60)

    def assert_(self, cond, otherwise=None):
        """
        Evaluates a C++ boolean condition and fails the test if it is false.

        **Arguments:**

        - ``cond``: A string containing a C++ expression that evaluates to ``bool``.
        - ``otherwise``: Optional message or value to include in the error if the assertion fails.

        **Example:**

        | Source Exec | int x = 5; |
        | Assert | x > 0 | Context: x should be positive |
        | Assert | x == 5 |
        """
        context_code = f' << " | Context: " << ({otherwise})' if otherwise else ''
        check_code = f"""
        if (!({cond})) {{
            throw std::runtime_error("AssertionError: {cond}" {context_code});
        }}
        """
        try:
            self.source_exec(check_code, timeout=60)
        except Exception as e:
            raise AssertionError(f"C++ Assertion Failed: {cond}") from e

    def get_value(self, obj_expression):
        """
        Retrieves the string representation of a C++ expression/variable.

        Basically executes ``std::cout << (expression)`` and returns the result.

        **Arguments:**

        - ``obj_expressionencode``: The C++ variable or expression to evaluate.

        **Example:**

        | Source Exec | int x = 100; |
        | ${val}= | Get Value | x * 2 |
        | Should Be Equal | ${val} | 200 |
        """
        return self.source_exec(f"std::cout << ({obj_expression});", timeout=60)

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
        return self.source_exec(f"std::cout << {func}({params_str});", timeout=60)

    def typeid(self, expression):
        """
        Returns the **mangled** C++ type name of an expression (using ``typeid(...).name()``).

        **Arguments:**

        - ``expression``: The object or type to inspect.
        """
        return self.source_exec(f'std::cout << typeid({expression}).name();', timeout=60)

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
        return self.source_exec(f'std::cout << _robot_demangle(typeid({expression}).name());', timeout=60)

    def nullptr(self):
        """
        Returns the string ``nullptr``. 
        
        Helper to represent the null pointer in keyword arguments.
        """
        return "nullptr"
