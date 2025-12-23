Tests and Examples
==================

This document serves as both the official documentation for usage examples and the executable test suite for the library.

Settings
--------

First, we import the library and configure the suite setup/teardown. We use `Start Kernel` to initialize the C++ environment (xeus-cpp) and `Shutdown Kernel` to clean it up.

.. code:: robotframework

    *** Settings ***
    Library    clang

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
