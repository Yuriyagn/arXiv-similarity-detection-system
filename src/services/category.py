import requests
from bs4 import BeautifulSoup
from cachetools import TTLCache
import time

class CategoryManager:
    def __init__(self):
        self.base_url = "https://arxiv.org"
        self.categories_url = f"{self.base_url}/archive"
        # 创建缓存，有效期1天
        self.cache = TTLCache(maxsize=100, ttl=86400)
        self._categories = None
        
    def get_categories(self):
        """
        抓取并缓存arXiv分类列表
        返回格式: [{'id': 'cs.CV', 'name': 'Computer Vision and Pattern Recognition'}, ...]
        """
        # 检查缓存
        if self._categories is not None:
            return self._categories
        print("正在抓取arXiv分类列表...")
        response = requests.get(self.categories_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "lxml")
        categories = []
        
        # 查找分类列表
        archive_div = soup.find("div", id="archive")
        if archive_div:
            # 遍历所有学科领域
            for discipline in archive_div.find_all("h2"):
                discipline_name = discipline.text.strip()
                # 查找当前学科下的分类列表
                ul = discipline.find_next_sibling("ul")
                if ul:
                    for li in ul.find_all("li"):
                        a_tag = li.find("a")
                        if a_tag:
                            # 提取分类ID和名称
                            href = a_tag.get("href", "")
                            if href.startswith("/list/"):
                                category_id = href.split("/")[2]
                                category_name = a_tag.text.strip()
                                categories.append({
                                    "id": category_id,
                                    "name": category_name,
                                    "discipline": discipline_name
                                })
        
        print(f"成功获取 {len(categories)} 个arXiv分类")
        # 保存到缓存
        self._categories = categories
        return categories
    
    def get_category_by_id(self, category_id):
        """
        根据分类ID获取分类信息
        """
        categories = self.get_categories()
        for category in categories:
            if category["id"] == category_id:
                return category
        return None
    
    def list_categories(self, discipline=None):
        """
        列出所有分类，可选择按学科过滤
        """
        categories = self.get_categories()
        if discipline:
            return [cat for cat in categories if cat["discipline"].lower() == discipline.lower()]
        return categories

# 测试代码
if __name__ == "__main__":
    manager = CategoryManager()
    
    # 第一次调用会抓取数据
    start_time = time.time()
    categories = manager.get_categories()
    print(f"第一次获取耗时: {time.time() - start_time:.2f}秒")
    
    # 第二次调用会使用缓存
    start_time = time.time()
    categories = manager.get_categories()
    print(f"第二次获取耗时: {time.time() - start_time:.2f}秒")
    
    # 打印部分分类示例
    print("\n部分分类示例:")
    for cat in categories[:10]:
        print(f"{cat['id']}: {cat['name']} ({cat['discipline']})")
    
    # 测试按ID查找
    cv_category = manager.get_category_by_id("cs.CV")
    print(f"\n按ID查找cs.CV: {cv_category}")