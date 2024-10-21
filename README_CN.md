# Pylang

[English](https://github.com/xia-mc/Pylang/blob/master/README.md)

> [!NOTE]
> Pylang 处于早期开发阶段，常见运行错误、崩溃和性能不佳的问题。请勿在任何项目中使用。

**Pylang** 是一个基于抽象语法树（AST）的Python代码优化器，执行静态分析以提高代码效率。它旨在帮助Python开发者编写简洁、可维护的代码，同时通过优化减少运行时开销。

## 功能

- **常量折叠**：在编译时计算常量表达式，减少运行时计算。
- **循环展开**：展开循环以减少开销，提升某些场景下的性能。
- **未使用变量移除**：自动移除未使用的变量，清理代码并减少内存占用。

## 待办事项

- [ ] **变量内联**：在适用的情况下自动内联变量以提高性能。
- [ ] **高级装饰器**：支持 `@inline`、`@const` 和 `@native` 等装饰器，以实现高级优化。
- [ ] **发布版本**：打包项目，提供发布说明和可分发的二进制文件以便更轻松地分发。
- [ ] **文档**：提供详细的API文档和示例，以帮助开发者将Pylang集成到他们的项目中。

## 快速开始

1. 克隆此仓库：
    ```bash
    git clone https://github.com/xia-mc/Pylang.git
    ```
2. 安装依赖：
    ```bash
    pip install -r requirements.txt
    ```
3. 在你的Python项目上运行优化器 (要求Python 3.7+)：
    ```bash
    python Pylang.py <flags>
    ```

### 命令行参数：

- F <文件路径>/D <目录路径>：需要优化的文件或目录路径。
- O <目录路径>：输出文件夹路径。
- O0/O1/O2/O3：优化级别。
    - O0：仅格式化代码，使其更小。
    - O1：进行一些简单推导，不会影响程序功能。
    - O2：进行更激进的优化，某些函数（如 `exec`）的行为可能会发生变化。
- tofile：将日志写入 `latest.log` 文件，而不是输出到标准输出。

示例：

```bash
python ./src/main/Pylang.py -D ./src/test -O2
```

## 贡献

欢迎提交问题、拉取请求或功能请求，帮助改进Pylang。我们非常感谢您的贡献和反馈！

## 致谢

此项目得益于以下工具和平台的支持：

- **[PyCharm](https://www.jetbrains.com/pycharm/)**：为提供了一个出色的集成开发环境，使开发过程更加顺畅高效。
- **[ChatGPT](https://openai.com/chatgpt/)**：在解决问题、提供代码建议以及开发过程中的宝贵见解方面提供了帮助。
- **[CodeGeeX](https://www.codegeex.cn/)**：通过AI增强代码编写体验，并提供了有用的代码自动补全功能。
- **[CPython](https://github.com/python/cpython)**：作为Python的核心，提供了强大的运行时环境，使得Pylang得以构建和运行。
