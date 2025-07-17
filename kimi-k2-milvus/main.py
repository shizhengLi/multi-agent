#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kimi K2 智能向量数据库助手
该程序使用Kimi K2大语言模型和Milvus向量数据库构建智能检索系统
"""

import os
import sys
import logging

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 导入本地模块
from models.smart_assistant import SmartAssistant
from utils.config import KIMI_API_KEY, OPENAI_API_KEY

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("kimi_agent.log")
    ]
)
logger = logging.getLogger("Main")

def main():
    """主程序"""
    print("🌟 Kimi K2 智能向量数据库助手")
    print("=" * 60)
    
    # 创建数据目录
    os.makedirs("kimi-k2-milvus/data", exist_ok=True)
    os.makedirs("kimi-k2-milvus/data/downloads", exist_ok=True)
    
    # 检查API密钥
    if not KIMI_API_KEY or not OPENAI_API_KEY:
        print("❌ 错误: API密钥未设置，请在.env文件中配置MOONSHOT_API_KEY和OPENAI_API_KEY")
        return
    
    # 创建智能助手
    assistant = SmartAssistant(KIMI_API_KEY, OPENAI_API_KEY)
    
    # 交互模式
    print("\n🎮 交互模式 (输入 'quit' 退出)")
    while True:
        try:
            user_input = input("\n请输入命令: ").strip()
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            
            if user_input:
                assistant.execute_command(user_input)
                print("\n" + "=" * 60)
                
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 发生错误: {str(e)}")

if __name__ == "__main__":
    main()