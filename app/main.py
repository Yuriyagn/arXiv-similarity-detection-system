from src.services.category import CategoryManager
from src.services.query import QueryBuilder
from src.services.pagination import PaginationProcessor
from src.utils.similarity import SimilarityMatcher
from datetime import datetime, timedelta
import time

def display_menu():
    """
    显示主菜单
    """
    print("\n" + "="*50)
    print("arXiv数据获取服务")
    print("="*50)
    print("1. 查看arXiv分类列表")
    print("2. 按学科查看分类")
    print("3. 搜索文献")
    print("4. 相似度匹配")
    print("5. 退出程序")
    print("="*50)


def display_categories(categories, page=1, page_size=20):
    """
    分页显示分类列表
    """
    total = len(categories)
    start = (page - 1) * page_size
    end = start + page_size
    page_categories = categories[start:end]
    
    print(f"\n分类列表 (第 {page} 页，共 {total} 个分类):")
    print("-" * 60)
    for i, category in enumerate(page_categories, start=start+1):
        print(f"{i:3d}. {category['id']:<15} {category['name']}")
    print("-" * 60)
    
    # 显示分页导航
    total_pages = (total + page_size - 1) // page_size
    if total_pages > 1:
        print(f"页码: {page}/{total_pages}")
        print("输入页码查看其他页，或按Enter返回主菜单")
    
    return total_pages


def search_papers():
    """
    搜索文献功能
    """
    print("\n" + "="*50)
    print("搜索arXiv文献")
    print("="*50)
    
    # 初始化组件
    category_manager = CategoryManager()
    query_builder = QueryBuilder()
    processor = PaginationProcessor(batch_size=50)
    
    # 1. 选择时间范围
    print("\n1. 时间范围设置:")
    print("   1) 昨天 (默认)")
    print("   2) 过去7天")
    print("   3) 过去30天")
    print("   4) 自定义范围")
    
    time_choice = input("请选择时间范围 (1-4，默认1): ").strip() or "1"
    
    if time_choice == "2":
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        query_builder.set_time_range(start_date, end_date)
    elif time_choice == "3":
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        query_builder.set_time_range(start_date, end_date)
    elif time_choice == "4":
        # 简化处理，使用默认时间范围
        print("暂不支持自定义时间范围，使用默认值")
        query_builder.set_time_range()
    else:
        query_builder.set_time_range()
    
    # 2. 选择分类
    print("\n2. 分类选择:")
    print("   1) 查看所有分类")
    print("   2) 输入分类ID")
    print("   3) 不限制分类")
    
    category_choice = input("请选择分类方式 (1-3，默认3): ").strip() or "3"
    
    if category_choice == "1":
        # 显示分类列表供选择
        categories = category_manager.get_categories()
        total_pages = display_categories(categories)
        
        # 让用户选择分类
        cat_choice = input("请输入要选择的分类ID，多个用逗号分隔: ").strip()
        if cat_choice:
            selected_cats = [cat.strip() for cat in cat_choice.split(",")]
            query_builder.add_category_filter(selected_cats)
    elif category_choice == "2":
        # 直接输入分类ID
        cat_input = input("请输入分类ID，多个用逗号分隔: ").strip()
        if cat_input:
            selected_cats = [cat.strip() for cat in cat_input.split(",")]
            query_builder.add_category_filter(selected_cats)
    
    # 3. 关键词搜索
    keyword_input = input("\n3. 输入关键词 (可选，多个用逗号分隔): ").strip()
    if keyword_input:
        keywords = [kw.strip() for kw in keyword_input.split(",")]
        query_builder.add_keyword_filter(keywords)
    
    # 4. 设置最大结果数
    max_results_input = input("\n4. 最大结果数 (默认100，0表示所有): ").strip() or "100"
    max_results = int(max_results_input) if max_results_input.isdigit() else 100
    
    # 5. 执行搜索
    print("\n正在执行搜索...")
    start_time = time.time()
    
    try:
        papers = processor.fetch_all(query_builder, max_total=max_results if max_results > 0 else None)
        
        elapsed_time = time.time() - start_time
        print(f"\n搜索完成! 耗时 {elapsed_time:.2f} 秒")
        print(f"共找到 {len(papers)} 篇论文")
        
        # 显示搜索结果
        if papers:
            print("\n" + "="*80)
            print("搜索结果")
            print("="*80)
            
            for i, paper in enumerate(papers[:10], 1):  # 只显示前10篇
                print(f"\n{i}. {paper['title']}")
                print(f"   作者: {', '.join(paper['authors'])}")
                print(f"   分类: {', '.join(paper['categories'])}")
                print(f"   发布时间: {paper['published']}")
                print(f"   arXiv ID: {paper.get('arxiv_id', paper['id'].split('/')[-1])}")
                print(f"   摘要: {paper['summary'][:200]}...")
            
            if len(papers) > 10:
                print(f"\n... 还有 {len(papers) - 10} 篇论文未显示")
    
    except Exception as e:
        print(f"搜索失败: {e}")


def translate_summary(summary):
    """
    使用大模型翻译英文摘要为中文总结
    """
    import requests
    import time
    
    url = "https://api.siliconflow.cn/v1/chat/completions"
    
    # 构建请求参数 - 简化参数，使用更常见的参数组合
    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": f"请将以下英文摘要翻译成一句中文总结：\n{summary}"
            }
        ],
        "stream": False,
        "max_tokens": 500,  # 减少最大 tokens，只需要简短总结
        "temperature": 0.3,  # 降低温度，生成更确定性的结果
        "top_p": 0.8,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "n": 1
    }
    
    # 从环境变量获取API密钥
    import os
    api_key = os.getenv('SILICONFLOW_API_KEY', '')
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    max_retries = 2  # 最多重试2次
    timeout = 10  # 缩短超时时间
    
    for attempt in range(max_retries):
        try:
            print(f"正在翻译摘要 (尝试 {attempt + 1}/{max_retries})...")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            
            # 只在调试模式下打印响应内容
            # print(f"API响应状态: {response.status_code}")
            # print(f"API响应内容: {response.text}")
            
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            else:
                return f"翻译失败：无法解析响应"
        except requests.exceptions.HTTPError as e:
            print(f"HTTP错误: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)  # 等待1秒后重试
        except requests.exceptions.ConnectionError:
            print(f"连接错误：无法连接到API服务器")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
        except requests.exceptions.Timeout:
            print(f"超时错误：API请求超时")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
        except Exception as e:
            print(f"翻译处理失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)  # 等待1秒后重试
    
    # 所有重试都失败
    return "翻译失败：多次尝试后仍无法获取翻译结果"


def similarity_match():
    """
    相似度匹配功能
    """
    print("\n" + "="*50)
    print("相似度匹配")
    print("="*50)
    
    # 获取用户输入的文本
    print("请输入要匹配的文本 (输入 'sample' 使用示例文本):")
    user_input = input("文本内容: ").strip()
    
    # 示例文本
    sample_text = "Multi-Modal Change Detection, Application to the Detection of Flooded Areas: Outcome of the 2009–2010 Data Fusion Contest。 The 2009-2010 Data Fusion Contest organized by the Data Fusion Technical Committee of the IEEE Geoscience and Remote Sensing Society was focused on the detection of flooded areas using multi-temporal and multi-modal images. Both high spatial resolution optical and synthetic aperture radar data were provided. The goal was not only to identify the best algorithms (in terms of accuracy), but also to investigate the further improvement derived from decision fusion. This paper presents the four awarded algorithms and the conclusions of the contest, investigating both supervised and unsupervised methods and the use of multi-modal data for flood detection. Interestingly, a simple unsupervised change detection method provided similar accuracy as supervised approaches, and a digital elevation model-based predictive method yielded a comparable projected change detection map without using post-event data."
    
    if user_input.lower() == "sample":
        test_text = sample_text
        print("使用示例文本进行匹配...")
    elif not user_input:
        print("文本不能为空，使用示例文本进行匹配...")
        test_text = sample_text
    else:
        test_text = user_input
    
    # 初始化组件
    query_builder = QueryBuilder()
    processor = PaginationProcessor(batch_size=100)
    matcher = SimilarityMatcher()
    
    # 配置查询
    print("\n配置查询参数:")
    
    # 1. 选择时间范围
    print("\n1. 时间范围设置:")
    print("   1) 昨天 (默认)")
    print("   2) 过去7天")
    print("   3) 过去30天")
    
    time_choice = input("请选择时间范围 (1-3，默认1): ").strip() or "1"
    
    if time_choice == "2":
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        query_builder.set_time_range(start_date, end_date)
    elif time_choice == "3":
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        query_builder.set_time_range(start_date, end_date)
    else:
        query_builder.set_time_range()
    
    # 2. 选择分类
    print("\n2. 分类选择 (默认: 相关视觉和AI分类):")
    print("   1) 使用默认分类")
    print("   2) 自定义分类")
    
    category_choice = input("请选择 (1-2，默认1): ").strip() or "1"
    
    if category_choice == "2":
        cat_input = input("请输入分类ID，多个用逗号分隔: ").strip()
        if cat_input:
            selected_cats = [cat.strip() for cat in cat_input.split(",")]
            query_builder.add_category_filter(selected_cats)
        else:
            # 使用默认分类
            query_builder.add_category_filter(['cs.CV', 'cs.AI', 'physics.ao-ph', 'eess.IV'])
    else:
        # 使用默认分类
        query_builder.add_category_filter(['cs.CV', 'cs.AI', 'physics.ao-ph', 'eess.IV'])
    
    # 3. 设置最大结果数
    max_results_input = input("\n3. 最大结果数 (默认100): ").strip() or "100"
    max_results = int(max_results_input) if max_results_input.isdigit() else 100
    query_builder.set_max_results(max_results)
    
    # 4. 选择相似度算法
    print("\n4. 相似度算法选择:")
    print("   1) 余弦相似度 (默认)")
    print("   2) Jaccard相似度")
    print("   3) 词频相似度")
    
    algo_choice = input("请选择算法 (1-3，默认1): ").strip() or "1"
    
    algo_map = {
        "1": "cosine",
        "2": "jaccard",
        "3": "word_frequency"
    }
    
    similarity_method = algo_map.get(algo_choice, "cosine")
    
    # 5. 设置返回结果数
    top_n_input = input("\n5. 返回前N篇论文 (默认10): ").strip() or "10"
    top_n = int(top_n_input) if top_n_input.isdigit() else 10
    
    # 执行搜索和匹配
    print("\n正在执行搜索和相似度匹配...")
    start_time = time.time()
    
    try:
        # 获取论文数据
        result = processor.fetch_single_batch(query_builder)
        print(f"获取到 {len(result['entries'])} 篇论文")
        
        # 计算相似度并排序
        print("\n正在计算相似度...")
        ranked_articles = matcher.rank_articles(test_text, result['entries'], method=similarity_method, top_n=top_n)
        
        elapsed_time = time.time() - start_time
        print(f"\n相似度匹配完成! 耗时 {elapsed_time:.2f} 秒")
        
        # 显示结果
        if ranked_articles:
            print("\n" + "="*80)
            print(f"相似度排名前{len(ranked_articles)}的论文 (使用{similarity_method}算法):")
            print("="*80)
            
            for i, item in enumerate(ranked_articles, 1):
                article = item['article']
                score = item['similarity_score']
                print(f"\n{i}. 相似度: {score:.4f}")
                print(f"   标题: {article['title']}")
                print(f"   作者: {', '.join(article['authors'])}")
                print(f"   发布时间: {article['published']}")
                print(f"   分类: {', '.join(article['categories'])}")
                print(f"   摘要: {article['summary'][:200]}...")
                # 尝试翻译摘要
                try:
                    chinese_summary = translate_summary(article['summary'])
                    print(f"   中文摘要: {chinese_summary}")
                except Exception as e:
                    print(f"   中文摘要: 翻译失败 - {str(e)[:100]}...")
            
            print("="*80)
        else:
            print("未找到匹配的论文")
    
    except Exception as e:
        print(f"相似度匹配失败: {e}")


def main():
    """
    主程序
    """
    print("欢迎使用arXiv数据获取服务!")
    print("正在初始化...")
    
    # 预加载分类列表（缓存）
    category_manager = CategoryManager()
    category_manager.get_categories()
    
    while True:
        display_menu()
        choice = input("请选择功能 (1-5): ").strip()
        
        if choice == "1":
            # 查看所有分类
            categories = category_manager.get_categories()
            page = 1
            total_pages = display_categories(categories, page)
            
            # 处理分页
            while total_pages > 1:
                page_input = input("页码: ").strip()
                if not page_input:
                    break
                if page_input.isdigit():
                    new_page = int(page_input)
                    if 1 <= new_page <= total_pages:
                        page = new_page
                        display_categories(categories, page)
                    else:
                        print(f"页码超出范围 (1-{total_pages})")
        
        elif choice == "2":
            # 按学科查看分类
            # 先获取所有学科
            categories = category_manager.get_categories()
            disciplines = list(set(cat["discipline"] for cat in categories))
            disciplines.sort()
            
            print("\n可用学科:")
            for i, discipline in enumerate(disciplines, 1):
                print(f"{i:2d}. {discipline}")
            
            disc_choice = input("请选择学科编号: ").strip()
            if disc_choice.isdigit():
                disc_idx = int(disc_choice) - 1
                if 0 <= disc_idx < len(disciplines):
                    selected_discipline = disciplines[disc_idx]
                    filtered_categories = category_manager.list_categories(selected_discipline)
                    display_categories(filtered_categories)
                else:
                    print("学科编号无效")
        
        elif choice == "3":
            # 搜索文献
            search_papers()
        
        elif choice == "4":
            # 相似度匹配
            similarity_match()
        
        elif choice == "5":
            # 退出程序
            print("\n感谢使用arXiv数据获取服务，再见!")
            break
        
        else:
            print("无效的选择，请重新输入")


if __name__ == "__main__":
    main()