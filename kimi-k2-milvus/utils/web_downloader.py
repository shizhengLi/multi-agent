import requests
import os
import logging
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urlparse
from typing import Optional, Dict, List, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WebDownloader")

class WebDownloader:
    """网页下载和文本提取工具"""
    
    def __init__(self, download_dir: str = "kimi-k2-milvus/data/downloads"):
        """初始化网页下载器"""
        self.download_dir = download_dir
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
        }
        # 创建下载目录
        os.makedirs(self.download_dir, exist_ok=True)
    
    def download_webpage(self, url: str) -> Dict[str, Any]:
        """
        下载并提取网页内容
        
        Args:
            url: 网页URL
            
        Returns:
            包含下载状态和提取内容的字典
        """
        try:
            # 构建保存文件名
            domain = urlparse(url).netloc
            timestamp = int(time.time())
            file_name = f"{domain.replace('.', '_')}_{timestamp}.txt"
            file_path = os.path.join(self.download_dir, file_name)
            
            # 下载网页
            logger.info(f"开始下载: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 移除脚本和样式元素
            for element in soup(["script", "style", "head", "header", "footer", "nav"]):
                element.decompose()
            
            # 提取正文内容
            text = self._extract_main_content(soup)
            
            # 如果内容太少，尝试另一种提取方式
            if len(text.split()) < 100:
                text = self._extract_all_text(soup)
            
            # 清理文本
            text = self._clean_text(text)
            
            # 保存到文件
            with open(file_path, "w", encoding="utf-8") as file:
                # 添加元数据
                file.write(f"URL: {url}\n")
                file.write(f"下载时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write("="*80 + "\n\n")
                # 写入正文
                file.write(text)
            
            logger.info(f"下载完成: {url} -> {file_path}")
            
            return {
                "success": True,
                "url": url,
                "file_path": file_path,
                "file_name": file_name,
                "content": text[:500] + "..." if len(text) > 500 else text,  # 返回预览
                "content_length": len(text)
            }
            
        except Exception as e:
            logger.error(f"下载失败 {url}: {str(e)}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        提取页面主要内容
        尝试找到具有最多文本内容的区域
        """
        # 尝试查找常见的内容容器
        candidates = soup.find_all(["article", "main", "div", "section"])
        
        best_candidate = None
        max_text_length = 0
        
        for candidate in candidates:
            text = candidate.get_text(strip=True)
            if len(text) > max_text_length:
                max_text_length = len(text)
                best_candidate = candidate
        
        if best_candidate:
            paragraphs = best_candidate.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 0)
        
        # 如果没有找到合适的内容，返回整个页面文本
        return soup.get_text(separator="\n\n")
    
    def _extract_all_text(self, soup: BeautifulSoup) -> str:
        """提取所有段落文本"""
        paragraphs = soup.find_all("p")
        if paragraphs:
            return "\n\n".join(p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 0)
        else:
            # 退化情况：返回所有文本
            return soup.get_text(separator="\n\n")
    
    def _clean_text(self, text: str) -> str:
        """清理提取的文本"""
        # 移除多余的空白
        text = re.sub(r'\s+', ' ', text)
        # 移除多余的换行符
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        # 删除非打印字符
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
        return text.strip()
    
    def batch_download(self, urls: List[str]) -> List[Dict[str, Any]]:
        """批量下载多个网页"""
        results = []
        for url in urls:
            result = self.download_webpage(url)
            results.append(result)
            # 添加延迟避免过快请求
            time.sleep(1)
        return results 

    def download_free_books(self, count: int = 3) -> List[Dict[str, Any]]:
        """
        下载几本免费的经典文学作品txt文档
        
        Args:
            count: 要下载的文档数量
            
        Returns:
            包含下载结果的字典列表
        """
        # 一些知名的免费文学作品链接
        free_books = [
            {
                "title": "爱丽丝漫游奇境记",
                "url": "https://www.gutenberg.org/files/11/11-0.txt"
            },
            {
                "title": "傲慢与偏见",
                "url": "https://www.gutenberg.org/files/1342/1342-0.txt"
            },
            {
                "title": "双城记",
                "url": "https://www.gutenberg.org/files/98/98-0.txt"
            },
            {
                "title": "战争与和平",
                "url": "https://www.gutenberg.org/files/2600/2600-0.txt"
            },
            {
                "title": "莎士比亚十四行诗",
                "url": "https://www.gutenberg.org/cache/epub/1041/pg1041.txt"
            }
        ]
        
        # 限制下载数量
        books_to_download = free_books[:min(count, len(free_books))]
        results = []
        
        for book in books_to_download:
            try:
                logger.info(f"正在下载经典文学作品: {book['title']}")
                result = self.download_webpage(book['url'])
                result['title'] = book['title']
                results.append(result)
            except Exception as e:
                logger.error(f"下载 {book['title']} 失败: {str(e)}")
                results.append({
                    "success": False,
                    "title": book['title'],
                    "url": book['url'],
                    "error": str(e)
                })
        
        return results 