# README

将langgraph的演示jupyter转换为可运行的python文件，方便大家使用。


## 环境配置

```py

git clone git@github.com:shizhengLi/multi-agent.git
cd multi-agent

# 创建conda环境
conda create -n agent python=3.11
conda activate agent

pip install -r requirements.txt

## 导出现在环境的包，读者不用管，这是方便我导出自己用的包，供您参考
conda list --export > requirements.txt
pip freeze > requirements.txt
pip freeze | grep -E "langchain|langgraph|openai|anthropic|requests|python-dotenv|tqdm|tiktoken" > requirements.txt
```

## 创建.env 文件
需要存放使用到的api key：

目前用到的是
- OpenAI的LLM
- tavily的search：每个月1000次免费web search

```py
touch .env

OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=xxx
TAVILY_API_KEY=xxx

``` 