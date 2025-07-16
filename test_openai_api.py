import os
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings  # Updated import path

# 加载环境变量
load_dotenv()

# 设置 HTTP 和 HTTPS 代理
#os.environ["HTTP_PROXY"] = os.getenv("HTTP_PROXY", "http://127.0.0.1:7890")
#os.environ["HTTPS_PROXY"] = os.getenv("HTTPS_PROXY", "http://127.0.0.1:7890")

# 获取API配置
api_key = os.getenv('OPENAI_API_KEY')
api_base = os.getenv('OPENAI_API_BASE')

print(f"API Key: {api_key}")
print(f"API Base URL: {api_base}")

# 确保非空值设置到环境变量
if api_key:
    os.environ["OPENAI_API_KEY"] = api_key
if api_base:
    os.environ["OPENAI_API_BASE"] = api_base

# 测试直接使用OpenAI客户端
print("\n1. 测试直接使用OpenAI客户端:")
try:
    client = OpenAI(
        api_key=api_key,
        base_url=api_base
    )
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "你好，请给我一个简短的回答。"}
        ],
        max_tokens=50
    )
    print("回答:", response.choices[0].message.content)
    print("✅ 直接OpenAI客户端测试成功")
except Exception as e:
    print(f"❌ 直接OpenAI客户端测试失败: {str(e)}")

# 测试LangChain的ChatOpenAI
print("\n2. 测试LangChain的ChatOpenAI:")
try:
    llm = ChatOpenAI(temperature=0, model="gpt-4o")
    response = llm.invoke("你好，请给我一个简短的回答。")
    print("回答:", response.content)
    print("✅ ChatOpenAI测试成功")
except Exception as e:
    print(f"❌ ChatOpenAI测试失败: {str(e)}")

# 测试OpenAI Embeddings
print("\n3. 测试OpenAI Embeddings:")
try:
    embeddings = OpenAIEmbeddings()
    result = embeddings.embed_query("测试嵌入向量")
    print(f"嵌入向量维度: {len(result)}")
    print("✅ OpenAIEmbeddings测试成功")
except Exception as e:
    print(f"❌ OpenAIEmbeddings测试失败: {str(e)}")

print("\n所有测试完成!")
