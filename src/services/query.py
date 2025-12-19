from datetime import datetime, timedelta

class QueryBuilder:
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        self.params = {
            "search_query": "",
            "start": 0,
            "max_results": 100,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
    def set_time_range(self, start_date=None, end_date=None):
        """
        设置查询的时间范围
        默认：昨天到今天
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=1)
        
        # 格式化为YYYYMMDD格式
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        # 更新查询条件
        time_filter = f"submittedDate:[{start_str}0000 TO {end_str}2359]"
        
        # 如果已有查询条件，添加AND，否则直接设置
        if self.params["search_query"]:
            self.params["search_query"] += f" AND {time_filter}"
        else:
            self.params["search_query"] = time_filter
        
        return self
    
    def add_category_filter(self, categories):
        """
        添加分类过滤
        categories: 可以是单个分类ID字符串，也可以是分类ID列表
        """
        if not categories:
            return self
        
        # 处理单个分类情况
        if isinstance(categories, str):
            categories = [categories]
        
        # 构建分类查询条件
        category_conditions = []
        for category in categories:
            category_conditions.append(f"cat:{category}")
        
        category_filter = f"({' OR '.join(category_conditions)})"
        
        # 如果已有查询条件，添加AND，否则直接设置
        if self.params["search_query"]:
            self.params["search_query"] += f" AND {category_filter}"
        else:
            self.params["search_query"] = category_filter
        
        return self
    
    def add_keyword_filter(self, keywords):
        """
        添加关键词过滤
        keywords: 可以是单个关键词字符串，也可以是关键词列表
        """
        if not keywords:
            return self
        
        # 处理单个关键词情况
        if isinstance(keywords, str):
            keywords = [keywords]
        
        # 构建关键词查询条件
        keyword_conditions = []
        for keyword in keywords:
            keyword_conditions.append(f"all:{keyword}")
        
        keyword_filter = f"({' OR '.join(keyword_conditions)})"
        
        # 如果已有查询条件，添加AND，否则直接设置
        if self.params["search_query"]:
            self.params["search_query"] += f" AND {keyword_filter}"
        else:
            self.params["search_query"] = keyword_filter
        
        return self
    
    def set_start(self, start):
        """
        设置查询起始位置（用于分页）
        """
        self.params["start"] = start
        return self
    
    def set_max_results(self, max_results):
        """
        设置每页最大结果数
        arXiv API限制最大为10000
        """
        # 限制最大结果数为10000
        self.params["max_results"] = min(max_results, 10000)
        return self
    
    def set_sort(self, sort_by="submittedDate", sort_order="descending"):
        """
        设置排序方式
        sort_by: submittedDate, lastUpdatedDate, relevance
        sort_order: ascending, descending
        """
        valid_sort_by = ["submittedDate", "lastUpdatedDate", "relevance"]
        valid_sort_order = ["ascending", "descending"]
        
        if sort_by in valid_sort_by:
            self.params["sortBy"] = sort_by
        if sort_order in valid_sort_order:
            self.params["sortOrder"] = sort_order
        
        return self
    
    def build(self):
        """
        构建最终的查询URL和参数
        返回格式: (url, params)
        """
        # 如果没有设置任何查询条件，默认使用昨天的时间范围
        if not self.params["search_query"]:
            self.set_time_range()
        
        return self.base_url, self.params
    
    def reset(self):
        """
        重置查询参数
        """
        self.params = {
            "search_query": "",
            "start": 0,
            "max_results": 100,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        return self

# 测试代码
if __name__ == "__main__":
    builder = QueryBuilder()
    
    # 测试1: 默认查询（昨天的所有论文）
    url, params = builder.build()
    print("测试1 - 默认查询:")
    print(f"URL: {url}")
    print(f"参数: {params}")
    
    # 测试2: 特定分类查询
    builder.reset()
    url, params = builder.add_category_filter(["cs.CV", "cs.AI"]).build()
    print("\n测试2 - 分类查询:")
    print(f"URL: {url}")
    print(f"参数: {params}")
    
    # 测试3: 时间范围+分类+关键词
    builder.reset()
    start_date = datetime.now() - timedelta(days=7)
    url, params = builder.set_time_range(start_date)\
    .add_category_filter("physics.quant-ph")\
    .add_keyword_filter(["quantum", "computing"])\
    .set_max_results(50)\
    .build()
    print("\n测试3 - 复杂查询:")
    print(f"URL: {url}")
    print(f"参数: {params}")