# Milvus Hybrid Search Demo

这个项目演示了如何使用[Milvus](https://milvus.io/)向量数据库和[BGE-M3模型](https://github.com/FlagOpen/FlagEmbedding/tree/master/FlagEmbedding/BGE_M3)进行混合搜索。项目展示了如何执行和比较稠密、稀疏和混合搜索方法的效果。

## 概述

Milvus支持三种类型的向量搜索方法：
- **稠密检索 (Dense Retrieval)**：利用语义上下文来理解查询背后的含义
- **稀疏检索 (Sparse Retrieval)**：强调关键词匹配，相当于全文搜索
- **混合检索 (Hybrid Retrieval)**：结合稠密和稀疏方法，提供更全面的搜索结果

本演示通过在真实世界数据集上比较不同的检索方法，展示了混合搜索的优势。

## 前提条件

此脚本需要以下依赖项：
- Python 3.8+
- pymilvus (启用model功能)
- pandas (用于数据集处理)
- matplotlib (用于可视化)
- numpy

## 数据集

演示使用了[Quora重复问题数据集](https://www.quora.com/q/quoradata/First-Quora-Dataset-Release-Question-Pairs)，该数据集包含了成对的问题以及它们是否重复的标记。这为评估不同搜索策略提供了良好的测试语料库。

## 设置和安装

脚本会自动处理所需包的安装和数据集的下载。您需要有一个可用的Python环境和pip。

## 使用方法

1. 激活conda环境：
```bash
conda activate agent
```

2. 运行脚本：
```bash
python hybrid_search_with_milvus.py
```

脚本会：
- 安装所需依赖项（如果需要）
- 下载Quora重复问题数据集
- 创建Milvus集合
- 处理数据集中的问题样本，并用BGE-M3模型生成向量嵌入
- 将稠密和稀疏向量存储到Milvus中
- 使用所有三种方法进行初始示例搜索
- 比较并可视化结果
- 进入交互模式，您可以输入自己的查询

## 交互模式

在初始设置和示例搜索后，您可以输入自己的文本查询来比较不同的搜索方法。输入'q'退出交互模式。

## 示例查询

尝试这些示例查询：
- "How do I learn to code?"（如何学习编程？）
- "What is the best programming language to start with?"（初学者选择什么编程语言最好？）
- "How do I improve my English pronunciation?"（如何提高英语发音？）
- "What's the difference between AI and machine learning?"（AI和机器学习的区别是什么？）
- "How do I prepare for a job interview?"（如何准备工作面试？）

## 可视化

脚本会生成一个比较图表，显示每种搜索方法的相关性得分，让您直观地看到不同类型查询下哪种方法表现更好。

## 注意事项

- 脚本使用Milvus Lite实现简单部署，数据存储在本地文件`milvus.db`中。
- 搜索结果和可视化会保存到当前目录的'search_comparison.png'文件中。
- 对于生产环境，建议使用完整的Milvus服务器部署。

## 源代码

本演示基于[Milvus Bootcamp教程](https://github.com/milvus-io/bootcamp/blob/master/tutorials/quickstart/hybrid_search_with_milvus.ipynb) 