from src.services.query import QueryBuilder
from src.services.pagination import PaginationProcessor

# 创建查询构建器
builder = QueryBuilder()
builder.set_time_range()  # 默认昨天
builder.add_category_filter('cs.CV')  # 计算机视觉分类
builder.set_max_results(20)

# 创建分页处理器
processor = PaginationProcessor(batch_size=20)

# 获取单个批次数据
print("测试查询构建器和分页处理器...")
try:
    result = processor.fetch_single_batch(builder)
    print(f"总结果数: {result['total_results']}")
    print(f"当前批次: {len(result['entries'])} 篇论文")
    
    # 打印第一篇论文的基本信息
    if result['entries']:
        print("\n第一篇论文信息:")
        paper = result['entries'][0]
        print(f"标题: {paper['title']}")
        print(f"作者: {', '.join(paper['authors'])}")
        print(f"发布时间: {paper['published']}")
        print(f"分类: {', '.join(paper['categories'])}")
except Exception as e:
    print(f"测试失败: {e}")