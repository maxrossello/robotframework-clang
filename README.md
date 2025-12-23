# Robot Framework Clang Library

`robotframework-clang` is a Robot Framework library designed to execute and test C++ code interactively using **Clang-REPL** (via the [xeus-cpp](https://github.com/jupyter-xeus/xeus-cpp) extension).

## Goals

The primary goal of this library is to support **unit testing of C++ code directly from Robot Framework**, overcoming the limitations of traditional approaches.

Unlike classic unit test frameworks, `robotframework-clang`:
- **Does not require an explicit `main`**: Code is JIT (Just-In-Time) compiled and executed incrementally.
- **Advanced native C++ support**: By using Clang-REPL, you can leverage the latest language features, including **C++ Modules**, without the configuration complexity of traditional build systems.
- **Isolation and Fast Iteration**: Each suite can manage its own C++ kernel, allowing isolated tests and immediate feedback without full compilation and linking cycles.

This approach is preferred over `cppyy` + `cling` for several key reasons:
- **Lifecycle Management**: Clang-REPL kernels can be stopped and restarted at will, ensuring strict isolation between tests. In contrast, `cling` cannot be reset once initialized, requiring the entire host process to terminate to clear the state.
- **Performance and Compatibility**: `clang-repl` is built on modern LLVM/Clang infrastructure, proceeding at the same pace and performance as the `clang` compiler itself, whereas `cling` is based on older forks and often introduces overhead.

## Requirements

- Python 3.8+
- **xeus-cpp 0.8.0**
- **Clang 20** (Note: Clang 21 is currently not supported by xeus-cpp 0.8.0)
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

The output will be available in `docs/_build/html/index.html`.

## License

This project is distributed under the **Apache License 2.0**. See the [LICENSE](LICENSE.md) file for details.
