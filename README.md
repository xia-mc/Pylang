# Pylang
[简体中文](https://github.com/xia-mc/Pylang/blob/master/README_CN.md)

**Pylang** is a Python code optimizer based on Abstract Syntax Tree (AST) that performs static analysis to improve code efficiency. It is designed to allow Python developers to write clean, maintainable code while benefiting from optimizations that reduce runtime overhead.

## Features
- **Constant Folding**: Evaluate constant expressions at compile time to reduce runtime calculations.
- **Loop Unfolding**: Unroll loops to reduce overhead, improving performance for certain scenarios.
- **Unused Variable Remover**: Automatically remove unused variables to clean up code and reduce memory usage.

## TODO
- [ ] **Variable Inlining**: Automatically inline variables where applicable for improved performance.
- [ ] **Advanced Decorators**: Add support for decorators like `@inline`, `@const`, and `@native` for advanced optimizations.
- [ ] **Releases**: Packaging the project with proper release notes and binaries for easier distribution.
- [ ] **Documentation**: Detailed API documentation and examples to guide developers in integrating Pylang into their projects.

## Getting Started
1. Clone the repository:
    ```bash
    git clone https://github.com/xia-mc/Pylang.git
    ```
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Run the optimizer on your Python project:
    ```bash
    python Pylang.py <flags>
    ```
### Flags:
- F <filepath>/D <dirpath>: Path to the file to be optimized.
- O <dirpath>: Path to the output folder.
- O0/O1/O2/O3: Optimize level.
    - O0: Only format codes to make smaller.
    - O1: Do some simple derivations and the functionality of the program will not be affected.
    - O2: Do more aggressive optimizations, the behavior of certain functions (like exec) may change.
- tofile: Write logs to `latest.log` instead of printing to stdout.
example:
```bash
python ./src/main/Pylang.py -D ./src/test -O2
```

## Contribution

Feel free to submit issues, pull requests, or feature requests to help improve Pylang. Contributions and feedback are greatly appreciated!

## Acknowledgements

This project would not have been possible without the help of the following tools and platforms:

- **[PyCharm](https://www.jetbrains.com/pycharm/)**: For providing an excellent IDE that made the development process smooth and efficient.
- **[ChatGPT](https://openai.com/chatgpt/)**: For assisting in problem-solving, code suggestions, and providing valuable insights during the development process.
- **[CodeGeeX](https://www.codegeex.cn/)**: For enhancing the code-writing experience and providing helpful AI-powered code completion features.
- **[CPython](https://github.com/python/cpython)**: The core of Python itself, which made this project possible by providing the powerful runtime environment on which Pylang is based.
