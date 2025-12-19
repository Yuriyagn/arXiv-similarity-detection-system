import re
from collections import Counter
import math

class SimilarityMatcher:
    def __init__(self):
        self.stop_words = {
            'the', 'of', 'and', 'in', 'to', 'a', 'is', 'that', 'it', 'on', 'for', 'with', 'as',
            'by', 'at', 'from', 'this', 'was', 'are', 'be', 'were', 'which', 'an', 'or', 'not',
            'but', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might',
            'shall', 'who', 'whom', 'whose', 'what', 'where', 'when', 'why', 'how', 'all',
            'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'too', 'very', 'so', 'than', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'
        }
    
    def preprocess_text(self, text):
        """
        文本预处理：转换为小写，去除标点符号，去除停用词
        """
        # 转换为小写
        text = text.lower()
        # 去除标点符号
        text = re.sub(r'[^\w\s]', '', text)
        # 分词
        words = text.split()
        # 去除停用词
        words = [word for word in words if word not in self.stop_words]
        return words
    
    def jaccard_similarity(self, text1, text2):
        """
        计算Jaccard相似度：交集大小 / 并集大小
        """
        words1 = set(self.preprocess_text(text1))
        words2 = set(self.preprocess_text(text2))
        
        # 计算交集和并集
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        # 避免除以零
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def cosine_similarity(self, text1, text2):
        """
        计算余弦相似度
        """
        words1 = self.preprocess_text(text1)
        words2 = self.preprocess_text(text2)
        
        # 计算词频
        freq1 = Counter(words1)
        freq2 = Counter(words2)
        
        # 获取所有唯一词
        all_words = set(freq1.keys()).union(set(freq2.keys()))
        
        # 计算点积
        dot_product = sum(freq1.get(word, 0) * freq2.get(word, 0) for word in all_words)
        
        # 计算模长
        norm1 = math.sqrt(sum(freq1.get(word, 0) ** 2 for word in all_words))
        norm2 = math.sqrt(sum(freq2.get(word, 0) ** 2 for word in all_words))
        
        # 避免除以零
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def word_frequency_similarity(self, text1, text2):
        """
        基于词频的相似度：计算共同词的频率总和
        """
        words1 = self.preprocess_text(text1)
        words2 = self.preprocess_text(text2)
        
        # 计算词频
        freq1 = Counter(words1)
        freq2 = Counter(words2)
        
        # 计算共同词的频率总和
        common_words = set(freq1.keys()).intersection(set(freq2.keys()))
        if not common_words:
            return 0.0
        
        # 计算相似度分数
        total_freq1 = sum(freq1.values())
        total_freq2 = sum(freq2.values())
        
        if total_freq1 == 0 or total_freq2 == 0:
            return 0.0
        
        # 计算共同词在两个文本中的频率比例之和
        similarity = 0.0
        for word in common_words:
            similarity += (freq1[word] / total_freq1) * (freq2[word] / total_freq2)
        
        return similarity
    
    def calculate_similarity(self, test_text, article, method='cosine'):
        """
        计算测试文本与单篇文章的相似度
        article: 文章字典，包含title和summary字段
        method: 相似度计算方法，可选值：cosine, jaccard, word_frequency
        """
        # 组合文章标题和摘要
        article_text = article.get('title', '') + ' ' + article.get('summary', '')
        
        # 根据选择的方法计算相似度
        if method == 'jaccard':
            return self.jaccard_similarity(test_text, article_text)
        elif method == 'word_frequency':
            return self.word_frequency_similarity(test_text, article_text)
        else: # 默认使用余弦相似度
            return self.cosine_similarity(test_text, article_text)
    
    def rank_articles(self, test_text, articles, method='cosine', top_n=None):
        """
        对文章列表按相似度进行排序
        articles: 文章列表
        method: 相似度计算方法
        top_n: 返回前n篇文章，None表示返回所有
        """
        # 计算每篇文章的相似度
        ranked_articles = []
        for article in articles:
            similarity_score = self.calculate_similarity(test_text, article, method)
            ranked_articles.append({
                'article': article,
                'similarity_score': similarity_score
            })
        
        # 按相似度降序排序
        ranked_articles.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # 返回前n篇文章
        if top_n:
            ranked_articles = ranked_articles[:top_n]
        
        return ranked_articles