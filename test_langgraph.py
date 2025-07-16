import os
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model

from dotenv import load_dotenv

load_dotenv()


# 获取API配置
api_key = os.getenv('OPENAI_API_KEY')
api_base = os.getenv('OPENAI_API_BASE')

print(f"API Key: {api_key}")
print(f"API Base URL: {api_base}")


def get_weather(city: str) -> str:  
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_react_agent(
    model="openai:gpt-4o",
    #"anthropic:claude-3-7-sonnet-latest",  
    tools=[get_weather],  
    prompt="You are a helpful assistant"  
)

# Run the agent
response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)

print(response)  # 打印助手的最终回复    