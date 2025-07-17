# Kimi K2 Milvus Agent

基于Kimi K2大语言模型和Milvus向量数据库的智能检索系统

## 项目简介

本项目利用Moonshot AI的Kimi K2大语言模型和Milvus向量数据库构建了一个智能检索系统，可以执行以下功能：

- 下载网页并保存为文本文件
- 将文本内容进行向量化并存储到Milvus数据库
- 执行语义搜索找到相关内容
- 基于检索到的内容回答用户问题
- 文件管理和向量数据库操作

## 系统架构

系统由以下几个主要组件构成：

1. **智能决策中心(SmartAssistant)**: 使用Kimi K2模型理解用户意图并调用合适的工具
2. **向量数据库管理(VectorDatabase)**: 管理Milvus向量数据库的连接、集合创建和数据检索
3. **网页下载工具(WebDownloader)**: 负责从互联网下载内容并提取文本
4. **配置管理(Config)**: 管理API密钥和系统配置

## 工具集

系统提供以下工具:

### 基础工具:
- `connect_database`: 数据库连接管理
- `create_collection`: 集合创建
- `add_documents`: 文档批量添加
- `list_all_collections`: 集合管理

### 搜索工具:
- `search_documents`: 指定集合搜索

### 文件工具:
- `read_and_chunk_file`: 文件预览切分
- `upload_file_to_collection`: 文件上传处理

### 网页工具:
- `download_webpage`: 单个网页下载
- `batch_download_webpages`: 批量网页下载

## 安装与配置

### 环境需求

- Python 3.8+
- Conda环境: agent

### 安装步骤

1. 克隆代码库:
```bash
git clone https://github.com/shizhengLi/multi-agent.git
cd multi-agent
```

2. 激活环境:
```bash
conda activate agent
```

3. 创建环境变量文件`.env`，包含以下内容:
```
MOONSHOT_API_KEY=你的Kimi K2 API密钥
OPENAI_API_KEY=你的OpenAI API密钥
OPENAI_API_BASE=https://api.gpt.ge/v1 # 或其他适用的基础URL
```

## 使用方法

运行主程序:

```bash
cd multiagent
#python -m kimi-k2-milvus.main
python kimi-k2-milvus/main.py
```

### 示例命令:

1. 下载网页并添加到向量库:
```
下载几本免费的电子书
```



2. 上传本地文件:
```
上传文件 ./kimi-k2-milvus/data/example_text.txt 到集合 sample_data
上传文件 ./kimi-k2-milvus/data/downloads/www_gutenberg_org_1752756442.txt 到集合 alice
Alice’s Adventures in Wonderland by Lewis Carroll


```

3. 搜索内容:
```
在集合 example_data 中搜索与"杨贵妃"相关的内容
```

## 开发者

- Li Shizheng

## 许可证

MIT License 

# 引用与致谢

本项目的部分设计和实现参考了以下文章和资源：

- 王舒虹 (Zilliz Social Media Advocate), [深度教程|Milvus + Kimi K2，打造生产级的专业问答助手], 发布于微信公众号: https://mp.weixin.qq.com/s/qfYMXGRJp9hwm0BIoQYUXA

本项目仅作为学习和研究之用，非商业目的。