# Multi-Agent 项目集合

这是一个多智能体系统的项目集合，包含了基于LangGraph、Milvus向量数据库、各种大语言模型的多个演示和应用项目。

## 📁 项目结构

### 🔬 Open Deep Research
基于LangGraph的深度研究代理系统，支持多种模型提供商、搜索工具和MCP服务器。
- **位置**: `open_deep_research/`
- **功能**: 深度研究、自动信息收集、报告生成
- **特点**: 完全开源、可配置、支持多种搜索工具
- **技术栈**: LangGraph、LangSmith、多种LLM模型

### 🔧 Local Deep Researcher
基于LangGraph的深度研究agent，可使用本地LLM。
- **位置**: `local-deep-researcher/`
- **功能**: deep research，生成报告
- **测试**：使用ollama测试本地qwen3:32b模型成功运行

### 🗄️ Milvus Demo
Milvus向量数据库的演示项目，展示混合搜索和文本图像搜索功能。
- **位置**: `milvus_demo/`
- **功能**: 
  - `hybrid_search/`: 混合搜索演示
  - `text_image_search/`: 文本图像搜索演示
- **技术栈**: Milvus、向量检索、相似性搜索

### 🤖 Kimi K2 Milvus Agent
基于Moonshot AI的Kimi K2大语言模型和Milvus向量数据库的智能检索系统。
- **位置**: `kimi-k2-milvus/`
- **功能**: 
  - 网页内容下载和文本提取
  - 文档向量化存储
  - 语义搜索和问答
  - 文件管理
- **技术栈**: Kimi K2、Milvus、向量检索
- **详细说明**: 参见 [kimi-k2-milvus/README.md](kimi-k2-milvus/README.md)



### 📝 基础工具和演示
- `build_basic_chatbot.py`: 基础聊天机器人构建
- `test_langgraph.py`: LangGraph功能测试
- `web_search_tool.py`: 网络搜索工具
- `test_openai_api.py`: OpenAI API测试
- `download_model.py`: 模型下载工具

## 🛠️ 环境配置

### 1. 克隆项目
```bash
git clone git@github.com:shizhengLi/multi-agent.git
cd multi-agent
```

### 2. 创建Conda环境
```bash
# 创建conda环境
conda create -n agent python=3.11
conda activate agent

# 安装基础依赖
pip install -r requirements.txt
```

### 3. 配置环境变量
创建 `.env` 文件并配置所需的API密钥：

```bash
touch .env
```

在 `.env` 文件中添加以下配置：
```bash
# OpenAI 配置
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=xxx

# Tavily 搜索API (每月1000次免费)
TAVILY_API_KEY=xxx

# Moonshot AI (Kimi) 配置
MOONSHOT_API_KEY=xxx

# Anthropic 配置 (可选)
ANTHROPIC_API_KEY=xxx

# 其他配置
LANGCHAIN_API_KEY=xxx
LANGCHAIN_TRACING_V2=true
```

## 🚀 快速开始

### Open Deep Research
```bash
cd open_deep_research
# 安装依赖
uv pip install -r pyproject.toml
# 启动LangGraph服务器
uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking
```
访问: http://127.0.0.1:2024

### Kimi K2 Milvus Agent
```bash
cd kimi-k2-milvus
python main.py
```

### 基础演示
```bash
# 测试OpenAI API
python test_openai_api.py

# 测试LangGraph
python test_langgraph.py

# 构建基础聊天机器人
python build_basic_chatbot.py
```

## 📚 项目特点

- **多模型支持**: 支持OpenAI、Anthropic、Moonshot AI等多种模型
- **向量检索**: 集成Milvus向量数据库，支持语义搜索
- **工具集成**: 包含网络搜索、文档处理、代码生成等多种工具
- **模块化设计**: 每个子项目独立，可单独使用或组合使用
- **易于扩展**: 基于LangGraph框架，易于添加新的代理和工具

## 🔧 依赖管理

```bash
# 导出当前环境包 (开发者用)
conda list --export > requirements.txt
pip freeze > requirements.txt

# 筛选核心依赖
pip freeze | grep -E "langchain|langgraph|openai|anthropic|requests|python-dotenv|tqdm|tiktoken" > requirements.txt
```

## 📖 更多信息

- [Open Deep Research详细文档](open_deep_research/README.md)
- [Kimi K2 Milvus Agent使用说明](kimi-k2-milvus/README.md)
- [Kimi K2 Milvus Agent演示](kimi-k2-milvus/demo.md)

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

本项目遵循相应子项目的许可证。 