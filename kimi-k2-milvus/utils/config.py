import os
from dotenv import load_dotenv

# 加载环境变量
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path)

# API密钥配置
KIMI_API_KEY = os.getenv("MOONSHOT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")

# 数据库配置
MILVUS_COLLECTION_PREFIX = "kimi_agent_"

# 其他配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50 