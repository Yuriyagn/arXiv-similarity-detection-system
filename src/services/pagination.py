import requests
import xml.etree.ElementTree as ET
import time
from src.services.query import QueryBuilder

class PaginationProcessor:
    def __init__(self, batch_size=100, max_retries=3, retry_delay=5):
        self.batch_size = batch_size  # 每次请求的结果数
        self.max_retries = max_retries  # 最大重试次数
        self.retry_delay = retry_delay  # 重试延迟（秒）
        self.query_builder = QueryBuilder()
        self.ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        
    def fetch_batch(self, url, params):
        """
        获取单个批次的数据
        """
        for attempt in range(self.max_retries):
            try:
                print(f"正在请求数据 - 起始位置: {params.get('start', 0)}, 数量: {params.get('max_results', 100)}")
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                print(f"请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    print(f"{self.retry_delay}秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    print("达到最大重试次数，请求失败")
                    raise
    
    def parse_response(self, xml_text):
        """
        解析arXiv API返回的XML数据
        """
        root = ET.fromstring(xml_text)
        entries = []
        
        # 获取总结果数
        total_results = root.find("./atom:totalResults", self.ns)
        total = int(total_results.text) if total_results is not None else 0
        
        # 解析每条论文数据
        for entry in root.findall("./atom:entry", self.ns):
            paper = {
                "id": entry.find("./atom:id", self.ns).text if entry.find("./atom:id", self.ns) is not None else "",
                "title": entry.find("./atom:title", self.ns).text.strip() if entry.find("./atom:title", self.ns) is not None else "",
                "summary": entry.find("./atom:summary", self.ns).text.strip() if entry.find("./atom:summary", self.ns) is not None else "",
                "published": entry.find("./atom:published", self.ns).text if entry.find("./atom:published", self.ns) is not None else "",
                "updated": entry.find("./atom:updated", self.ns).text if entry.find("./atom:updated", self.ns) is not None else "",
                "categories": [],
                "authors": [],
                "links": []
            }
            
            # 解析分类
            for category in entry.findall("./atom:category", self.ns):
                if category.get("term"):
                    paper["categories"].append(category.get("term"))
            
            # 解析作者
            for author in entry.findall("./atom:author", self.ns):
                name = author.find("./atom:name", self.ns)
                if name is not None:
                    paper["authors"].append(name.text.strip())
            
            # 解析链接
            for link in entry.findall("./atom:link", self.ns):
                link_dict = {
                    "href": link.get("href"),
                    "rel": link.get("rel"),
                    "type": link.get("type")
                }
                paper["links"].append(link_dict)
            
            # 解析arXiv特定字段
            arxiv_id = entry.find("./arxiv:id", self.ns)
            if arxiv_id is not None:
                paper["arxiv_id"] = arxiv_id.text
            
            arxiv_doi = entry.find("./arxiv:doi", self.ns)
            if arxiv_doi is not None:
                paper["doi"] = arxiv_doi.text
            
            entries.append(paper)
        
        return {
            "total_results": total,
            "entries": entries
        }
    
    def fetch_all(self, query_builder, max_total=None):
        """
        分页获取所有结果
        query_builder: QueryBuilder对象，已配置好查询参数
        max_total: 最大获取结果数，None表示获取所有
        """
        all_entries = []
        start = 0
        
        # 设置批次大小
        query_builder.set_max_results(self.batch_size)
        
        # 获取初始URL和参数
        url, base_params = query_builder.build()
        
        while True:
            # 更新起始位置
            params = base_params.copy()
            params["start"] = start
            
            # 获取当前批次数据
            xml_text = self.fetch_batch(url, params)
            result = self.parse_response(xml_text)
            
            # 添加到结果列表
            all_entries.extend(result["entries"])
            
            # 打印进度
            print(f"已获取 {len(all_entries)} / {result['total_results']} 篇论文")
            
            # 检查是否已获取所有结果或达到最大限制
            start += len(result["entries"])
            
            if (max_total and len(all_entries) >= max_total) or start >= result["total_results"] or len(result["entries"]) == 0:
                break
            
            # 防止请求过快，添加延迟
            print("等待1秒后继续请求...")
            time.sleep(1)
        
        # 如果设置了最大结果数，截断结果
        if max_total:
            all_entries = all_entries[:max_total]
        
        print(f"完成数据获取，共获取 {len(all_entries)} 篇论文")
        return all_entries
    
    def fetch_single_batch(self, query_builder):
        """
        获取单个批次的数据
        """
        query_builder.set_max_results(self.batch_size)
        url, params = query_builder.build()
        xml_text = self.fetch_batch(url, params)
        result = self.parse_response(xml_text)
        return result

# 测试代码
if __name__ == "__main__":
    processor = PaginationProcessor(batch_size=50)
    
    # 创建查询构建器
    builder = QueryBuilder()
    builder.set_time_range()  # 默认昨天
    builder.add_category_filter("cs.CV")  # 计算机视觉分类
    
    # 测试获取单个批次
    print("测试1 - 获取单个批次数据:")
    result = processor.fetch_single_batch(builder)
    print(f"总结果数: {result['total_results']}")
    print(f"当前批次: {len(result['entries'])} 篇论文")
    
    # 测试获取前100篇
    print("\n测试2 - 获取前100篇论文:")
    all_papers = processor.fetch_all(builder, max_total=100)
    print(f"最终获取: {len(all_papers)} 篇论文")
    
    # 打印第一篇论文的基本信息
    if all_papers:
        print("\n第一篇论文信息:")
        paper = all_papers[0]
        print(f"标题: {paper['title']}")
        print(f"作者: {', '.join(paper['authors'])}")
        print(f"发布时间: {paper['published']}")
        print(f"分类: {', '.join(paper['categories'])}")