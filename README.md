# Robot Framework Clang Library

[![CI](https://github.com/maxrossello/robotframework-clang/actions/workflows/ci.yml/badge.svg)](https://github.com/maxrossello/robotframework-clang/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/robotframework-clang/badge/?version=latest)](https://robotframework-clang.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

`robotframework-clang` is a Robot Framework library designed to execute and test C++ code interactively using **Clang-REPL** (via the [xeus-cpp](https://github.com/jupyter-xeus/xeus-cpp) extension).

## Goals

The primary goal of this library is to support **unit testing of C++ code directly from Robot Framework**, overcoming the limitations of traditional approaches.

Unlike classic unit test frameworks, `robotframework-clang`:
- **Does not require an explicit `main`**: Code is JIT (Just-In-Time) compiled and executed incrementally.
- **Advanced native C++ support**: By using Clang-REPL, you can leverage the latest language features, including **C++ Modules**, without the configuration complexity of traditional build systems.
- **Isolation and Fast Iteration**: Each suite can manage its own C++ kernel, allowing isolated tests and immediate feedback without full compilation and linking cycles.

## Why Clang-REPL (xeus-cpp) over cppyy?

While `cppyy` (based on Cling) is an excellent tool for creating Pythonic bindings and manipulating C++ objects directly from Python, this library consciously chooses **Clang-REPL** (via `xeus-cpp`) for the specific use case of **Unit Testing**.

Here is why:

1.  **Process Isolation & Stability**:
    *   **xeus-cpp**: Uses a client-server architecture (Jupyter Kernel). If the C++ code segfaults or crashes, only the kernel subprocess dies. Robot Framework detects the failure, reports it, and can restart the kernel for the next test suite.
    *   **cppyy**: Runs in the same process as Python. A C++ crash brings down the entire test runner, causing the loss of test reports and halting execution.

2.  **Future-Proofing & Standards**:
    *   **Clang-REPL**: Is part of the upstream LLVM project. It represents the future of interactive C++ (with ROOT and CppInterOp moving in this direction) and guarantees day-one support for new compiler features.
    *   **Cling**: Is a legacy fork of Clang. While powerful, it often lags behind upstream LLVM versions.

3.  **Mature C++20 Support**:
    *   Thanks to the underlying Clang 20+ engine, this library provides robust support for modern C++ standards, including C++20 Modules and Concepts, which are essential for testing modern codebases.

4.  **Testing vs. Bindings**:
    *   The goal here is not to "write C++ in Python" (bindings), but to **verify C++ behavior** in its native environment. We want to compile and run C++ snippets exactly as a compiler would, without the "magic" or type conversion layers that might obscure bugs in the C++ logic itself.

## Requirements

- Python 3.8+
- **xeus-cpp 0.8.0**
- **Clang 20** (Note: Clang 21 is currently not supported by xeus-cpp 0.8.0)
- **libcxx** (LLVM C++ standard library)
- A working C++ kernel (e.g., `xcpp20`).

## Installation

### Using Conda (Recommended)

Installation via Conda is the preferred method as it automatically manages binary dependencies for the compiler and the JIT kernel.

```bash
conda install -c conda-forge robotframework-clang
```

### Using Pip

If you already have an environment with `xeus-cpp` installed and configured:

```bash
pip install robotframework-clang
```

## Documentation and Testing

This project uses an "executable documentation" approach. Tests are written in reStructuredText format within the `docs/` folder, serving as both usage examples and the actual test suite.

### Running Tests

To execute the tests (which are embedded in the documentation):

```bash
make tests
```

### Building Documentation

To generate the HTML documentation (requires Sphinx and sphinx-rtd-theme):

```bash
# Install documentation requirements
pip install .[docs]

# Build the docs
make docs
```

The output will be available in html/index.html.

## License

This project is distributed under the **Apache License 2.0**. See the [LICENSE](LICENSE.md) file for details.
