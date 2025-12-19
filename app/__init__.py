from flask import Flask, render_template, request, jsonify
from src.services.category import CategoryManager
from src.services.query import QueryBuilder
from src.services.pagination import PaginationProcessor
from src.utils.similarity import SimilarityMatcher
from app.main import translate_summary
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 创建Flask应用实例
app = Flask(__name__)

# 设置模板目录
app.template_folder = '../templates'

# 初始化组件
category_manager = CategoryManager()

@app.route('/')
def index():
    """
    主页，显示聊天界面
    """
    return render_template('index.html')

@app.route('/api/match', methods=['POST'])
def match_similarity():
    """
    处理相似度匹配请求
    """
    try:
        data = request.json
        text = data.get('text', '')
        use_sample = data.get('use_sample', False)
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        
        # 使用示例文本
        if use_sample:
            text = "Multi-Modal Change Detection, Application to the Detection of Flooded Areas: Outcome of the 2009–2010 Data Fusion Contest。 The 2009-2010 Data Fusion Contest organized by the Data Fusion Technical Committee of the IEEE Geoscience and Remote Sensing Society was focused on the detection of flooded areas using multi-temporal and multi-modal images. Both high spatial resolution optical and synthetic aperture radar data were provided. The goal was not only to identify the best algorithms (in terms of accuracy), but also to investigate the further improvement derived from decision fusion. This paper presents the four awarded algorithms and the conclusions of the contest, investigating both supervised and unsupervised methods and the use of multi-modal data for flood detection. Interestingly, a simple unsupervised change detection method provided similar accuracy as supervised approaches, and a digital elevation model-based predictive method yielded a comparable projected change detection map without using post-event data."
        
        if not text:
            return jsonify({'error': '文本不能为空'}), 400
        
        # 创建查询构建器 - 使用默认参数
        builder = QueryBuilder()
        
        # 设置时间范围
        if start_date_str and end_date_str:
            try:
                from datetime import datetime
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                builder.set_time_range(start_date, end_date)
            except ValueError as e:
                return jsonify({'error': f'日期格式错误: {e}'}), 400
        else:
            builder.set_time_range()  # 默认昨天
            
        # 获取请求中的分类参数
        categories = data.get('categories', [])
        if categories and len(categories) > 0:
            builder.add_category_filter(categories)
        else:
            builder.add_category_filter(['cs.CV', 'cs.AI', 'physics.ao-ph', 'eess.IV'])  # 默认分类
        
        # 获取前端传递的查询参数
        max_query_count = data.get('max_query_count', 20)  # 默认查询20篇
        max_results_count = data.get('max_results_count', 10)  # 默认返回10篇
        
        builder.set_max_results(max_query_count)  # 使用用户设定的查询数量
        
        # 创建分页处理器
        processor = PaginationProcessor(batch_size=max_query_count)
        
        # 获取论文数据
        result = processor.fetch_single_batch(builder)
        
        # 创建相似度匹配器
        matcher = SimilarityMatcher()
        
        # 计算相似度并排序，使用用户设定的返回数量
        ranked_articles = matcher.rank_articles(text, result['entries'], method='cosine', top_n=max_results_count)
        
        # 处理结果，添加中文摘要
        results = []
        for item in ranked_articles:
            article = item['article']
            # 尝试翻译摘要
            try:
                chinese_summary = translate_summary(article['summary'])
            except Exception as e:
                chinese_summary = f"翻译失败: {str(e)}"
            
            # 提取arxiv_id
            arxiv_id = article.get('arxiv_id', '')
            if not arxiv_id and article.get('id'):
                # 从id字段提取
                import re
                match = re.search(r'/abs/([0-9\.]+)', article['id'])
                if match:
                    arxiv_id = match.group(1)
            
            results.append({
                'similarity_score': round(item['similarity_score'], 4),
                'title': article['title'],
                'authors': ', '.join(article['authors']),
                'published': article['published'],
                'categories': ', '.join(article['categories']),
                'summary': article['summary'],
                'chinese_summary': chinese_summary,
                'arxiv_id': arxiv_id,
                'id': article.get('id', '')
            })
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)