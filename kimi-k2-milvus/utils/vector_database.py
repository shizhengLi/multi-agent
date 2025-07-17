import time
import numpy as np
import json
import uuid
from pymilvus import (
    connections, 
    utility,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    MilvusClient
)
from openai import OpenAI
import os
from typing import List, Dict, Any, Union
import logging
import re
from .config import OPENAI_API_KEY, OPENAI_API_BASE, MILVUS_COLLECTION_PREFIX, CHUNK_SIZE, CHUNK_OVERLAP

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VectorDatabase")

class VectorDatabase:
    """向量数据库管理类"""
    def __init__(self, openai_api_key: str = None):
        """初始化向量数据库"""
        self.openai_api_key = openai_api_key if openai_api_key else OPENAI_API_KEY
        self.openai_client = OpenAI(
            api_key=self.openai_api_key,
            base_url=OPENAI_API_BASE
        )
        self.dimension = 1536  # 使用OpenAI嵌入模型维度
        self.milvus_client = None
    
    def connect_database(self) -> dict:
        """连接到Milvus数据库"""
        try:
            # 使用Milvus Lite嵌入式向量数据库，使用绝对路径
            #import os
            #current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            #db_path = os.path.join(current_dir, "kimi_agent.db")
            # 使用相对路径
            db_path = "./kimi-k2-milvus/kimi_agent.db"
            self.milvus_client = MilvusClient(db_path)
            #self.milvus_client = MilvusClient(uri="http://localhost:19530")
            return {
                "success": True,
                "message": f"成功连接到向量数据库，路径: {db_path}",
                "client": "Milvus Lite"
            }
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return {
                "success": False,
                "message": f"连接数据库失败: {str(e)}"
            }
    
    def list_all_collections(self) -> dict:
        """列出所有集合"""
        try:
            if not self.milvus_client:
                return {"success": False, "message": "数据库未连接，请先调用connect_database"}
            
            collections = self.milvus_client.list_collections()
            return {
                "success": True,
                "collections": collections
            }
        except Exception as e:
            logger.error(f"列出集合失败: {str(e)}")
            return {
                "success": False,
                "message": f"列出集合失败: {str(e)}"
            }
    
    def create_collection(self, collection_name: str, description: str = "") -> dict:
        """创建集合"""
        try:
            if not self.milvus_client:
                return {"success": False, "message": "数据库未连接，请先调用connect_database"}
            
            # 处理集合名称，将空格替换为下划线
            collection_name = collection_name.replace(" ", "_")
            
            # 添加前缀以区分项目集合
            full_collection_name = f"{MILVUS_COLLECTION_PREFIX}{collection_name}"
            
            # 检查集合是否已存在
            if self.milvus_client.has_collection(collection_name=full_collection_name):
                return {
                    "success": True,
                    "message": f"集合 '{collection_name}' 已存在"
                }
            
            # 创建集合 - MilvusClient的create_collection参数
            self.milvus_client.create_collection(
                collection_name=full_collection_name,
                dimension=self.dimension,
                metric_type="COSINE",
                auto_id=True  # 让Milvus自动生成ID
            )
            
            # 存储集合元数据（如描述信息）
            metadata_collection_name = f"{MILVUS_COLLECTION_PREFIX}metadata"
            if not self.milvus_client.has_collection(collection_name=metadata_collection_name):
                self.milvus_client.create_collection(
                    collection_name=metadata_collection_name,
                    dimension=self.dimension,
                    metric_type="L2",
                    auto_id=True  # 让Milvus自动生成ID
                )
            
            # 添加集合元数据
            self.milvus_client.insert(
                collection_name=metadata_collection_name,
                data=[{
                    "collection_name": full_collection_name,
                    "description": description,
                    "created_at": time.time(),
                    "vector": [0.0] * self.dimension  # 占位向量
                }]
            )
            
            return {
                "success": True,
                "message": f"成功创建集合 '{collection_name}'",
                "collection": collection_name
            }
        except Exception as e:
            logger.error(f"创建集合失败: {str(e)}")
            return {
                "success": False,
                "message": f"创建集合失败: {str(e)}"
            }
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成文本嵌入向量"""
        try:
            if not texts:
                return []
                
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {str(e)}")
            raise
    
    def add_documents(self, collection_name: str, documents: List[str]) -> dict:
        """向集合添加文档"""
        try:
            if not self.milvus_client:
                return {"success": False, "message": "数据库未连接，请先调用connect_database"}
                
            # 处理集合名称，将空格替换为下划线
            collection_name = collection_name.replace(" ", "_")
            
            # 检查是否已经包含前缀
            if collection_name.startswith(MILVUS_COLLECTION_PREFIX):
                full_collection_name = collection_name  # 已有前缀，直接使用
            else:
                # 添加前缀
                full_collection_name = f"{MILVUS_COLLECTION_PREFIX}{collection_name}"
            
            # 检查集合是否存在
            if not self.milvus_client.has_collection(collection_name=full_collection_name):
                return {
                    "success": False,
                    "message": f"集合 '{collection_name}' 不存在，请先创建集合"
                }
            
            # 生成嵌入向量
            embeddings = self.generate_embeddings(documents)
            
            # 准备数据 - 使用auto_id，无需提供id字段
            data = [
                {
                    "vector": embeddings[i],
                    "text": documents[i],
                }
                for i in range(len(documents))
            ]
            
            # 插入数据
            result = self.milvus_client.insert(
                collection_name=full_collection_name,
                data=data
            )
            
            return {
                "success": True,
                "message": f"成功添加 {len(documents)} 个文档到集合 '{collection_name}'",
                "insert_count": result.get("insert_count", 0)
            }
        except Exception as e:
            logger.error(f"添加文档失败: {str(e)}")
            return {
                "success": False,
                "message": f"添加文档失败: {str(e)}"
            }
    
    def search_documents(self, collection_name: str, query: str, limit: int = 5) -> dict:
        """搜索相似文档"""
        try:
            if not self.milvus_client:
                return {"success": False, "message": "数据库未连接，请先调用connect_database"}
                
            # 处理集合名称，将空格替换为下划线
            collection_name = collection_name.replace(" ", "_")
                
            # 检查是否已经包含前缀
            if collection_name.startswith(MILVUS_COLLECTION_PREFIX):
                full_collection_name = collection_name  # 已有前缀，直接使用
            else:
                # 添加前缀
                full_collection_name = f"{MILVUS_COLLECTION_PREFIX}{collection_name}"
            
            # 检查集合是否存在
            if not self.milvus_client.has_collection(collection_name=full_collection_name):
                return {
                    "success": False,
                    "message": f"集合 '{collection_name}' 不存在，请先创建集合"
                }
            
            # 生成查询嵌入向量
            query_embedding = self.generate_embeddings([query])[0]
            
            # 执行向量搜索
            results = self.milvus_client.search(
                collection_name=full_collection_name,
                data=[query_embedding],
                limit=limit,
                output_fields=["text"]
            )
            
            # 解析搜索结果
            search_results = []
            if results and hasattr(results, "data") and len(results.data) > 0:
                for hit in eval(results.data[0]):
                    search_results.append({
                        "text": hit.get("entity", {}).get("text", ""),
                        "score": 1 - hit.get("distance", 1.0)  # 将距离转换为相似度分数
                    })
            
            return {
                "success": True,
                "results": search_results,
                "count": len(search_results)
            }
        except Exception as e:
            logger.error(f"搜索文档失败: {str(e)}")
            return {
                "success": False,
                "message": f"搜索文档失败: {str(e)}"
            }
    
    def read_and_chunk_file(self, file_path: str, chunk_size: int = None, overlap: int = None) -> dict:
        """读取本地文件并切分成文本块"""
        try:
            chunk_size = chunk_size or CHUNK_SIZE
            overlap = overlap or CHUNK_OVERLAP
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "message": f"文件 '{file_path}' 不存在"
                }
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            # 分割文本
            chunks = []
            if len(text) <= chunk_size:
                chunks.append(text)
            else:
                start = 0
                while start < len(text):
                    end = min(start + chunk_size, len(text))
                    # 如果不是最后一个块且不是在句子末尾，尝试在句子边界分割
                    if end < len(text):
                        # 寻找句子结束的位置
                        last_period = text.rfind('.', start, end)
                        last_question = text.rfind('?', start, end)
                        last_exclamation = text.rfind('!', start, end)
                        
                        # 找到最靠后的句子结束符号
                        sentence_end = max(last_period, last_question, last_exclamation)
                        
                        # 如果找到了句子结束符号且它不是在开头附近，使用它作为切分点
                        if sentence_end > start + chunk_size // 2:
                            end = sentence_end + 1
                            
                    chunks.append(text[start:end])
                    start = end - overlap
            
            return {
                "success": True,
                "file_name": os.path.basename(file_path),
                "chunks": chunks,
                "chunk_count": len(chunks)
            }
        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            return {
                "success": False,
                "message": f"读取文件失败: {str(e)}"
            }
    
    def upload_file_to_collection(self, file_path: str, collection_name: str, 
                                 chunk_size: int = None, overlap: int = None) -> dict:
        """上传本地文件到指定集合，自动切分并向量化"""
        try:
            # 检查数据库连接
            if not self.milvus_client:
                return {"success": False, "message": "数据库未连接，请先调用connect_database"}
            
            # 处理集合名称，将空格替换为下划线
            collection_name = collection_name.replace(" ", "_")
            
            # 检查是否已经包含前缀
            if collection_name.startswith(MILVUS_COLLECTION_PREFIX):
                full_collection_name = collection_name  # 已有前缀，直接使用
            else:
                # 添加前缀
                full_collection_name = f"{MILVUS_COLLECTION_PREFIX}{collection_name}"
            
            # 检查集合是否存在，如果不存在则创建
            if not self.milvus_client.has_collection(collection_name=full_collection_name):
                create_result = self.create_collection(collection_name, f"Collection for {os.path.basename(file_path)}")
                if not create_result["success"]:
                    return create_result
            
            # 读取和切分文件
            chunk_result = self.read_and_chunk_file(file_path, chunk_size, overlap)
            if not chunk_result["success"]:
                return chunk_result
            
            # 添加文档到集合
            add_result = self.add_documents(collection_name, chunk_result["chunks"])
            if not add_result["success"]:
                return add_result
            
            return {
                "success": True,
                "message": f"成功上传文件 '{os.path.basename(file_path)}' 到集合 '{collection_name}'",
                "file_name": os.path.basename(file_path),
                "collection": collection_name,
                "chunk_count": chunk_result["chunk_count"],
                "insert_count": add_result.get("insert_count", 0)
            }
        except Exception as e:
            logger.error(f"上传文件失败: {str(e)}")
            return {
                "success": False,
                "message": f"上传文件失败: {str(e)}"
            } 

    def get_collection_content(self, collection_name: str) -> dict:
        """直接获取集合中的所有文档内容，不使用向量搜索"""
        try:
            if not self.milvus_client:
                return {"success": False, "message": "数据库未连接，请先调用connect_database"}
                
            # 处理集合名称，将空格替换为下划线
            collection_name = collection_name.replace(" ", "_")
                
            # 检查是否已经包含前缀
            if collection_name.startswith(MILVUS_COLLECTION_PREFIX):
                full_collection_name = collection_name  # 已有前缀，直接使用
            else:
                # 添加前缀
                full_collection_name = f"{MILVUS_COLLECTION_PREFIX}{collection_name}"
            
            # 检查集合是否存在
            if not self.milvus_client.has_collection(collection_name=full_collection_name):
                return {
                    "success": False,
                    "message": f"集合 '{collection_name}' 不存在，请先创建集合"
                }
            
            # 获取集合信息
            count = self.milvus_client.get_collection_stats(collection_name=full_collection_name)
            row_count = count.get("row_count", 0)
            
            if row_count == 0:
                return {
                    "success": True,
                    "message": f"集合 '{collection_name}' 为空",
                    "count": 0,
                    "documents": []
                }
                
            # 查询所有文档
            try:
                result = self.milvus_client.query(
                    collection_name=full_collection_name,
                    filter="",
                    output_fields=["text"],
                    limit=100
                )
                
                documents = []
                if result:
                    for item in result:
                        if "text" in item:
                            documents.append(item["text"])
                
                return {
                    "success": True,
                    "message": f"成功获取集合 '{collection_name}' 中的文档",
                    "count": len(documents),
                    "documents": documents
                }
            except Exception as e:
                logger.error(f"查询集合内容失败: {str(e)}")
                
                # 尝试替代方案
                try:
                    result = self.milvus_client.get(
                        collection_name=full_collection_name,
                        ids=[],
                        output_fields=["text"]
                    )
                    
                    documents = []
                    if result:
                        for item in result:
                            if "text" in item:
                                documents.append(item["text"])
                    
                    return {
                        "success": True,
                        "message": f"成功获取集合 '{collection_name}' 中的文档 (备用方法)",
                        "count": len(documents),
                        "documents": documents
                    }
                except Exception as e2:
                    logger.error(f"备用方法查询集合内容也失败: {str(e2)}")
                    return {
                        "success": False,
                        "message": f"获取集合内容失败: 主方法错误: {str(e)}, 备用方法错误: {str(e2)}"
                    }
        except Exception as e:
            logger.error(f"获取集合内容失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取集合内容失败: {str(e)}"
            } 