API Reference
=============

**Library Scope:** ``GLOBAL``

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

.. contents:: Keywords
   :local:
   :depth: 1

Add Include Path
----------------

**Arguments:** ``*paths``

Adds directories to the C++ include search path (equivalent to ``-I`` flag).

Paths added here are used by `Start Kernel` (at startup) and `Source Include` 
(to resolve header files).

**Arguments:**

- ``paths``: One or more directory paths to add.

**Example:**

| Add Include Path | /opt/mylib/include | ${CURDIR}/../include |


Add Link Directory
------------------

**Arguments:** ``*paths``

Adds directories to the linker search path (equivalent to ``-L`` flag).

Must be called **before** `Start Kernel`.

**Arguments:**

- ``paths``: One or more directory paths to add.


Assert
------

**Arguments:** ``cond, otherwise=None``

Evaluates a C++ boolean condition and fails the test if it is false.

**Arguments:**

- ``cond``: A string containing a C++ expression that evaluates to ``bool``.
- ``otherwise``: Optional message or value to print/include in the error if the assertion fails.

**Example:**

| Source Exec | int x = 5; |
| Assert | x > 0 | Context: x should be positive |
| Assert | x == 5 |


Call Function
-------------

**Arguments:** ``func, *params``

Calls a global C++ function with the provided arguments and returns its output.

**Arguments:**

- ``func``: Name of the function to call.
- ``params``: Arguments to pass to the function.

**Example:**

| Source Exec | int add(int a, int b) {{ return a + b; }} |
| ${res}= | Call Function | add | 2 | 3 |


Get Value
---------

**Arguments:** ``obj_expression``

Retrieves the string representation of a C++ expression/variable.

Basically executes ``std::cout << (expression)`` and returns the result.

**Arguments:**

- ``obj_expression``: The C++ variable or expression to evaluate.

**Example:**

| Source Exec | int x = 100; |
| ${val}= | Get Value | x * 2 |
| Should Be Equal | ${val} | 200 |


Link Libraries
--------------

**Arguments:** ``*libs``

Specifies libraries to link against at startup (equivalent to ``-l`` flag).

Must be called **before** `Start Kernel`.

**Arguments:**

- ``libs``: Names of libraries (e.g., ``m`` for libm, ``pthread``).


Load Shared Library
-------------------

**Arguments:** ``*libraries``

Loads a shared object (.so) or dynamic library (.dylib/dll) into the process via ``dlopen``.

This allows calling functions from shared libraries that are not linked at startup.
Ensure symbols are loaded with global visibility (RTLD_GLOBAL).

**Arguments:**

- ``libraries``: Paths or names of libraries to load.

**Example:**

| Load Shared Library | /usr/lib/libm.so |


Nullptr
-------

Returns the string ``nullptr``. 

Helper to represent the null pointer in keyword arguments.


Shutdown Kernel
---------------

Stops the running C++ kernel and cleans up resources.

This also clears the accumulated include paths and link settings.


Source Exec
-----------

**Arguments:** ``*parts``

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


Source Include
--------------

**Arguments:** ``*files``

Includes header files in the current session.

This keyword attempts to resolve the provided file names. If a file is not
found in the current directory, it searches through the paths added via
`Add Include Path` and uses an absolute path if a match is found.

**Arguments:**

- ``files``: Names of the header files to include (e.g., ``vector``, ``myheader.h``).

**Example:**

| Source Include | vector | map |


Source Parse
------------

**Arguments:** ``*parts``

Defines C++ code structure (declarations) without expecting output.

Useful for defining classes, functions, or globals.
Alias for `Source Exec`.

**Arguments:**

- ``parts``: Lines of C++ code.


Start Kernel
------------

**Arguments:** ``kernel_name=xcpp20``

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


Typeid
------

**Arguments:** ``expression``

Returns the **mangled** C++ type name of an expression (using ``typeid(...).name()``).

**Arguments:**

- ``expression``: The object or type to inspect.


Typename
--------

**Arguments:** ``expression``

Returns the **demangled** (human-readable) C++ type name of an expression.

Uses ``abi::__cxa_demangle`` internally.

**Arguments:**

- ``expression``: The object or type to inspect.

**Example:**

| ${name}= | Typename | std::string("foo") |
| Should Contain | ${name} | string |


