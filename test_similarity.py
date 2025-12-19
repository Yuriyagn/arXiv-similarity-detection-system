from src.services.query import QueryBuilder
from src.services.pagination import PaginationProcessor
from src.utils.similarity import SimilarityMatcher

# 示例文本
sample_text = "Multi-Modal Change Detection, Application to the Detection of Flooded Areas: Outcome of the 2009–2010 Data Fusion Contest。 The 2009-2010 Data Fusion Contest organized by the Data Fusion Technical Committee of the IEEE Geoscience and Remote Sensing Society was focused on the detection of flooded areas using multi-temporal and multi-modal images. Both high spatial resolution optical and synthetic aperture radar data were provided. The goal was not only to identify the best algorithms (in terms of accuracy), but also to investigate the further improvement derived from decision fusion. This paper presents the four awarded algorithms and the conclusions of the contest, investigating both supervised and unsupervised methods and the use of multi-modal data for flood detection. Interestingly, a simple unsupervised change detection method provided similar accuracy as supervised approaches, and a digital elevation model-based predictive method yielded a comparable projected change detection map without using post-event data."

print("测试相似度匹配功能...")

# 创建查询构建器
builder = QueryBuilder()
builder.set_time_range()  # 默认昨天
builder.add_category_filter(['cs.CV', 'cs.AI'])  # 计算机视觉和AI分类
builder.set_max_results(20)

# 创建分页处理器和相似度匹配器
processor = PaginationProcessor(batch_size=20)
matcher = SimilarityMatcher()

try:
    # 获取论文数据
    print("\n正在获取论文数据...")
    result = processor.fetch_single_batch(builder)
    print(f"获取到 {len(result['entries'])} 篇论文")
    
    # 计算相似度并排序
    print("\n正在计算相似度...")
    ranked_articles = matcher.rank_articles(sample_text, result['entries'], method='cosine', top_n=5)
    
    # 显示结果
    print(f"\n相似度排名前{len(ranked_articles)}的论文:")
    print("=" * 80)
    
    for i, item in enumerate(ranked_articles, 1):
        article = item['article']
        score = item['similarity_score']
        print(f"\n{i}. 相似度: {score:.4f}")
        print(f"   标题: {article['title']}")
        print(f"   作者: {', '.join(article['authors'][:3])}")
        print(f"   发布时间: {article['published']}")
        print(f"   分类: {', '.join(article['categories'])}")
        print(f"   摘要: {article['summary'][:150]}...")
    
    print("=" * 80)
    print("\n测试完成!")
    
except Exception as e:
    print(f"测试失败: {e}")