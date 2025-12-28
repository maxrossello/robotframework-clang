Tests and Examples
==================

This document serves as both the official documentation for usage examples and the executable test suite for the library.

Settings
--------

First, we import the library and configure the suite setup/teardown. We use `Start Kernel` to initialize the C++ environment (xeus-cpp) and `Shutdown Kernel` to clean it up.
We also use `OperatingSystem` to create temporary header files for testing include paths.

.. code:: robotframework

    *** Settings ***
    Library    clang
    Library    OperatingSystem

    Test Setup       Start Kernel
    Test Teardown    Shutdown Kernel

Basic Execution
---------------

The core keyword is `Source Exec`. It sends C++ code to the REPL.

.. code:: robotframework

    *** Test Cases ***
    Hello World C++
        [Documentation]    Verifies that we can run simple C++ code.
        ${output}=    Source Exec    std::cout << "Hello from Robot!" << std::endl;
        Should Be Equal    ${output}    Hello from Robot!

Variables
---------

Variables defined in the global scope of the REPL persist across calls within the same kernel session.

.. code:: robotframework

    *** Test Cases ***
    Define And Use Variable
        [Documentation]    Defines a variable in one call and uses it in another.
        Source Exec    int x = 42;
        ${result}=    Source Exec    std::cout << x;
        Should Be Equal    ${result}    42

Defining Code Structures
------------------------

Use `Source Parse` to define classes, structs, or functions without producing output. This is useful for setting up the environment.

.. code:: robotframework

    *** Test Cases ***
    Define Function And Class
        [Documentation]    Defines a C++ function and a struct using Source Parse.
        Source Parse    int add(int a, int b) { return a + b; }
        Source Parse    struct Point { int x; int y; };

        # Verify usage
        ${res}=    Source Exec    std::cout << add(10, 20);
        Should Be Equal    ${res}    30

Function Calls
--------------

The `Call Function` keyword simplifies calling global C++ functions and getting their return value (printed to stdout).

.. code:: robotframework

    *** Test Cases ***
    Call Global Function
        [Documentation]    Calls the 'add' function defined in the previous test (same kernel session).
        # We redefine it here just in case tests are reordered or isolated in future, 
        # though currently they share the kernel if not restarted. 
        # Actually, Test Setup 'Start Kernel' restarts it every time! 
        # So we must define it again.
        Source Parse    int multiply(int a, int b) { return a * b; }
        
        ${res}=    Call Function    multiply    6    7
        Should Be Equal    ${res}    42

Expression Evaluation
---------------------

`Get Value` evaluates a C++ expression and returns its string representation.

.. code:: robotframework

    *** Test Cases ***
    Evaluate Expressions
        [Documentation]    Uses Get Value to evaluate math and string ops.
        Source Exec    int base = 10;
        ${val}=    Get Value    base * 5 + 3
        Should Be Equal    ${val}    53

Assertions
----------

We can use standard C++ boolean logic to perform assertions inside the kernel.

.. code:: robotframework

    *** Test Cases ***
    Check Assertion
        [Documentation]    Verifies the Assert keyword.
        Assert    1 == 1
        Run Keyword And Expect Error    *Assertion Failed*    Assert    1 == 0

Type Introspection
------------------

The library provides helpers to identify C++ types, which is useful given the lack of direct Python object mapping.

.. code:: robotframework

    *** Test Cases ***
    Check Type Identification
        [Documentation]    Verifies Typeid and Typename keywords.
        ${id}=    Typeid    42
        Should Be Equal    ${id}    i
        ${name}=    Typename    std::string("hello")
        Should Contain    ${name}    string

Nullptr Support
---------------

The keyword `Nullptr` returns a string literal that is interpreted as a true C++ null pointer by the kernel.

.. code:: robotframework

    *** Test Cases ***
    Verify Nullptr Literal
        [Documentation]    Checks if the string 'nullptr' is recognized as a C++ null pointer.
        ${null_str}=    Nullptr
        # We check if (nullptr == 0) in C++, which is true.
        ${is_null}=    Source Exec    std::cout << (${null_str} == 0);
        Should Be Equal    ${is_null}    1

        # We check the type. It can be 'std::nullptr_t' or 'decltype(nullptr)'
        ${type}=    Typename    ${null_str}
        Should Contain    ${type}    nullptr

Custom Includes
---------------

We can add custom directories to the include path and load specific headers.
**Note:** `Add Include Path` must be called *before* `Start Kernel` (or followed by a restart) for changes to take effect.

.. code:: robotframework

    *** Test Cases ***
    Using Custom Header
        [Documentation]    Creates a temporary header, adds its path, and includes it.
        [Setup]    None
        
        ${temp_dir}=    Join Path    ${OUTPUT DIR}    include_test
        Create Directory    ${temp_dir}
        ${header_path}=    Join Path    ${temp_dir}    mymath.h
        Create File    ${header_path}    const double MY_PI_CONST = 3.14159;

        # Add path BEFORE starting kernel
        Add Include Path    ${temp_dir}
        Start Kernel
        
        Source Include      mymath.h

        ${pi_val}=    Get Value    MY_PI_CONST
        Should Be Equal    ${pi_val}    3.14159
        
        [Teardown]    Run Keywords    Shutdown Kernel    AND    Remove Directory    ${temp_dir}    recursive=True

Shared Libraries
----------------

We can also load compiled shared libraries (.so/.dylib/dll) into the running kernel.

.. code:: robotframework

    *** Test Cases ***
    Load Shared Library Test
        [Documentation]    Compiles a shared lib and loads it at runtime via dlopen.
        [Setup]    None
        
        ${temp_dir}=    Join Path    ${OUTPUT DIR}    dlopen_test
        Create Directory    ${temp_dir}
        ${src_path}=    Join Path    ${temp_dir}    dlopen_lib.cpp
        ${so_path}=     Join Path    ${temp_dir}    libdlopen_lib.so
        
        Create File    ${src_path}    extern "C" int dlopen_func() { return 789; }

        # Compile shared library
        ${rc}    ${out}=    Run And Return Rc And Output    clang++ -shared -fPIC -fvisibility=default -o ${so_path} ${src_path}
        Should Be Equal As Integers    ${rc}    0

        Start Kernel
        Load Shared Library    ${so_path}
        
        Source Parse    extern "C" int dlopen_func();
        ${res}=    Source Exec    std::cout << dlopen_func();
        Should Be Equal    ${res}    789

        [Teardown]    Run Keywords    Shutdown Kernel    AND    Remove Directory    ${temp_dir}    recursive=True

    Link Libraries Test
        [Documentation]    Verifies linking libraries at startup (-L and -l flags).
        [Setup]    None
        
        ${temp_dir}=    Join Path    ${OUTPUT DIR}    link_test
        Create Directory    ${temp_dir}
        ${src_path}=    Join Path    ${temp_dir}    link_lib.cpp
        # Name must start with 'lib' for -l to work
        ${so_path}=     Join Path    ${temp_dir}    libmylink.so
        
        Create File    ${src_path}    extern "C" int link_func() { return 456; }

        # Compile shared library
        ${rc}    ${out}=    Run And Return Rc And Output    clang++ -shared -fPIC -fvisibility=default -o ${so_path} ${src_path}
        Should Be Equal As Integers    ${rc}    0

        # Configure linking BEFORE starting kernel
        Add Link Directory    ${temp_dir}
        Link Libraries    mylink

        Start Kernel
        
        Source Parse    extern "C" int link_func();
        ${res}=    Source Exec    std::cout << link_func();
        Should Be Equal    ${res}    456

        [Teardown]    Run Keywords    Shutdown Kernel    AND    Remove Directory    ${temp_dir}    recursive=True

