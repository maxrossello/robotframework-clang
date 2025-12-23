*** Settings ***
Library    clang

Test Setup       Start Kernel
Test Teardown    Shutdown Kernel

*** Test Cases ***
Hello World C++
    [Documentation]    Verifies that we can run simple C++ code.
    ${output}=    Source Exec    std::cout << "Hello from Robot!" << std::endl;
    Should Be Equal    ${output}    Hello from Robot!

Define And Use Variable
    [Documentation]    Defines a variable in one call and uses it in another.
    Source Exec    int x = 42;
    ${result}=    Source Exec    std::cout << x;
    Should Be Equal    ${result}    42

Check Assertion
    [Documentation]    Verifies the Assert keyword.
    Assert    1 == 1
    Run Keyword And Expect Error    *Assertion Failed*    Assert    1 == 0

Check Type Identification
    [Documentation]    Verifies Typeid and Typename keywords.
    ${id}=    Typeid    42
    Should Be Equal    ${id}    i
    ${name}=    Typename    std::string("hello")
    # Note: Depending on the implementation/compiler, it might be std::string 
    # or std::__cxa11::basic_string... but with demangle it should be readable.
    Should Contain    ${name}    string
