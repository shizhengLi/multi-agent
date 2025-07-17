import time
import json
import os
import logging
from typing import List, Dict, Any, Union, Optional
from openai import OpenAI
from utils import VectorDatabase, WebDownloader
from utils.config import KIMI_API_KEY, OPENAI_API_KEY

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SmartAssistant")

class SmartAssistant:
    """智能决策中心，使用Kimi K2理解用户意图并调用合适的工具"""
    
    def __init__(self, kimi_api_key: str = None, openai_api_key: str = None):
        """初始化智能助手"""
        print("🚀 启动智能助手...")
        
        # API密钥配置
        self.kimi_api_key = kimi_api_key if kimi_api_key else KIMI_API_KEY
        self.openai_api_key = openai_api_key if openai_api_key else OPENAI_API_KEY
        
        # Kimi客户端
        self.kimi_client = OpenAI(
            api_key=self.kimi_api_key,
            base_url="https://api.moonshot.cn/v1"
        )
        
        # 向量数据库
        self.vector_db = VectorDatabase(self.openai_api_key)
        
        # 网页下载器
        self.web_downloader = WebDownloader()
        
        # 定义可用工具
        self.available_tools = [
            {
                "type": "function",
                "function": {
                    "name": "connect_database",
                    "description": "连接到向量数据库",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_collection",
                    "description": "创建新的文档集合",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "collection_name": {"type": "string", "description": "集合名称"},
                            "description": {"type": "string", "description": "集合描述"}
                        },
                        "required": ["collection_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_documents",
                    "description": "向集合添加文档",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "collection_name": {"type": "string", "description": "集合名称"},
                            "documents": {"type": "array", "items": {"type": "string"}, "description": "文档列表"}
                        },
                        "required": ["collection_name", "documents"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_documents",
                    "description": "搜索相似文档",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "collection_name": {"type": "string", "description": "集合名称"},
                            "query": {"type": "string", "description": "搜索内容"},
                            "limit": {"type": "integer", "description": "结果数量", "default": 5}
                        },
                        "required": ["collection_name", "query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_collection_content",
                    "description": "直接获取集合中的所有文档内容，不使用向量搜索",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "collection_name": {"type": "string", "description": "集合名称"}
                        },
                        "required": ["collection_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_all_collections",
                    "description": "查询数据库中所有集合的信息",
                    "parameters": {"type": "object", "properties": {}, "required": []}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_and_chunk_file",
                    "description": "读取本地文件并切分成文本块",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "文件路径"},
                            "chunk_size": {"type": "integer", "description": "每个文本块的大小", "default": 500},
                            "overlap": {"type": "integer", "description": "文本块之间的重叠字符数", "default": 50}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "upload_file_to_collection",
                    "description": "上传本地文件到指定集合，自动切分并向量化",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "文件路径"},
                            "collection_name": {"type": "string", "description": "目标集合名称"},
                            "chunk_size": {"type": "integer", "description": "每个文本块的大小", "default": 500},
                            "overlap": {"type": "integer", "description": "文本块之间的重叠字符数", "default": 50}
                        },
                        "required": ["file_path", "collection_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "download_webpage",
                    "description": "下载网页并保存为文本文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "网页URL"},
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "batch_download_webpages",
                    "description": "批量下载多个网页并保存为文本文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "urls": {"type": "array", "items": {"type": "string"}, "description": "网页URL列表"}
                        },
                        "required": ["urls"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "download_free_books",
                    "description": "下载几本经典免费文学作品用于测试",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "count": {"type": "integer", "description": "要下载的文档数量", "default": 3}
                        },
                        "required": []
                    }
                }
            }
        ]
        print("✅ 智能助手启动完成")

    def _execute_tool(self, tool_name: str, args: dict) -> dict:
        """执行具体工具"""
        logger.info(f"执行工具: {tool_name}, 参数: {args}")
        
        if tool_name == "connect_database":
            return self.vector_db.connect_database()
        
        elif tool_name == "create_collection":
            return self.vector_db.create_collection(**args)
        
        elif tool_name == "add_documents":
            return self.vector_db.add_documents(**args)
        
        elif tool_name == "search_documents":
            return self.vector_db.search_documents(**args)
        
        elif tool_name == "get_collection_content":
            return self.vector_db.get_collection_content(**args)
        
        elif tool_name == "list_all_collections":
            return self.vector_db.list_all_collections()
        
        elif tool_name == "read_and_chunk_file":
            return self.vector_db.read_and_chunk_file(**args)
        
        elif tool_name == "upload_file_to_collection":
            return self.vector_db.upload_file_to_collection(**args)
        
        elif tool_name == "download_webpage":
            return self.web_downloader.download_webpage(**args)
        
        elif tool_name == "batch_download_webpages":
            return {
                "results": self.web_downloader.batch_download(args["urls"]),
                "success": True,
                "message": f"批量下载完成，共 {len(args['urls'])} 个URL"
            }
        
        elif tool_name == "download_free_books":
            return {
                "results": self.web_downloader.download_free_books(**args),
                "success": True,
                "message": f"下载完成，请查看 kimi-k2-milvus/data/downloads 目录"
            }
        
        else:
            return {"success": False, "message": f"未知工具: {tool_name}"}

    def execute_command(self, user_command: str) -> str:
        """执行用户命令"""
        print(f"\n📝 用户命令: {user_command}")
        print("=" * 60)
        
        # 准备对话消息
        messages = [
            {
                "role": "system",
                "content": """你是一个智能助手，可以帮助用户管理向量数据库和回答问题。
    智能决策原则：
    1. 优先考虑回答速度和质量，选择最优的回答方式
    2. 对于通用知识问题，直接使用你的知识快速回答
    3. 只在以下情况使用数据库搜索：
    - 用户明确要求搜索数据库中的内容
    - 问题涉及用户上传的特定文档或专业资料
    - 需要查找具体的、专门的信息时
    4. 你可以处理文件上传、数据库管理等任务
    5. 始终以提供最快速、最准确的答案为目标
    重要提醒：
    - 在执行任何数据库操作之前，请先调用 connect_database 连接数据库
    - 如果遇到API限制错误，系统会自动重试，请耐心等待
    记住：不要为了使用工具而使用工具，而要以最优的方式解决用户的问题。"""
            },
            {
                "role": "user",
                "content": user_command
            }
        ]
        
        # 开始对话和工具调用循环
        while True:
            try:
                # 调用Kimi模型 - 添加重试机制处理API限制
                max_retries = 5
                retry_delay = 20  # 秒
                for attempt in range(max_retries):
                    try:
                        response = self.kimi_client.chat.completions.create(
                            model="kimi-k2-0711-preview",  # 使用Kimi K2模型
                            messages=messages,
                            temperature=0.3,
                            tools=self.available_tools,
                            tool_choice="auto"
                        )
                        break  # 成功则跳出重试循环
                    except Exception as e:
                        if "rate_limit" in str(e).lower() or "429" in str(e) and attempt < max_retries - 1:
                            print(f"⏳ Kimi API限制，等待 {retry_delay} 秒后重试... (尝试 {attempt + 1}/{max_retries})")
                            time.sleep(retry_delay)
                            retry_delay *= 1.5  # 适度增加延迟
                            continue
                        else:
                            raise e
                else:
                    raise Exception("调用Kimi API失败：超过最大重试次数")
                    
                choice = response.choices[0]
                
                # 如果需要调用工具
                if choice.finish_reason == "tool_calls":
                    messages.append(choice.message)
                    
                    # 执行每个工具调用
                    for tool_call in choice.message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        print(f"🔧 调用工具: {tool_name}")
                        print(f"📋 参数: {tool_args}")
                        
                        # 如果是搜索文档，确保使用正确的集合名称
                        if tool_name == "search_documents":
                            # 先连接数据库
                            db_result = self.vector_db.connect_database()
                            if not db_result.get("success", False):
                                error_msg = f"❌ 错误: 无法连接到数据库: {db_result.get('message', '未知错误')}"
                                print(error_msg)
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": tool_name,
                                    "content": json.dumps({"success": False, "message": error_msg})
                                })
                                continue
                            
                            # 获取所有集合
                            collections_result = self.vector_db.list_all_collections()
                            if not collections_result.get("success", False):
                                error_msg = f"❌ 错误: 无法获取集合列表: {collections_result.get('message', '未知错误')}"
                                print(error_msg)
                                messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": tool_name,
                                    "content": json.dumps({"success": False, "message": error_msg})
                                })
                                continue
                            
                            # 查找目标集合（带前缀）
                            available_collections = collections_result.get("collections", [])
                            print(f"可用集合: {available_collections}")
                            
                            target_collection = tool_args["collection_name"]
                            
                            # 自动添加前缀
                            from utils.config import MILVUS_COLLECTION_PREFIX
                            prefixed_collection = f"{MILVUS_COLLECTION_PREFIX}{target_collection}"
                            
                            # 如果目标集合不在列表中，但带前缀的在，使用带前缀的
                            if target_collection not in available_collections and prefixed_collection in available_collections:
                                print(f"使用集合: {prefixed_collection} 替代 {target_collection}")
                                tool_args["collection_name"] = prefixed_collection  # 直接使用带前缀的名称
                            
                            # 如果是查询sample_data，确保使用正确的名称
                            if target_collection == "sample_data" and "kimi_agent_sample_data" in available_collections:
                                print(f"使用集合: kimi_agent_sample_data (已有前缀)")
                                tool_args["collection_name"] = "kimi_agent_sample_data"
                        
                        # 执行工具
                        result = self._execute_tool(tool_name, tool_args)
                        print(f"✅ 结果: {result}")
                        print("-" * 40)
                        
                        # 向量搜索无结果时，对于搜索操作，尝试直接获取集合内容
                        if tool_name == "search_documents" and result.get("success", False) and len(result.get("results", [])) == 0:
                            print("向量搜索没有找到结果，尝试直接获取集合内容...")
                            collection_name = tool_args["collection_name"]
                            content_result = self._execute_tool("get_collection_content", {"collection_name": collection_name})
                            
                            if content_result.get("success", False) and content_result.get("count", 0) > 0:
                                print(f"找到集合内容: {content_result.get('count')} 个文档")
                                # 将集合内容添加到result中
                                result["collection_content"] = content_result.get("documents", [])
                                result["message"] = "向量搜索未找到结果，但集合中存在文档"
                        
                        # 将工具结果添加到对话
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": json.dumps(result)
                        })
                # 如果完成了任务
                else:
                    final_response = choice.message.content
                    print(f"🎯 任务完成: {final_response}")
                    return final_response
                    
            except Exception as e:
                error_msg = f"执行出错: {str(e)}"
                print(f"❌ {error_msg}")
                return error_msg