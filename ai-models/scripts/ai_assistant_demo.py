#!/usr/bin/env python3
"""
刀塔2 AI智能助手集成示例
展示如何在社区应用中调用训练好的模型
"""

import os
import json
import requests
from typing import Dict, Optional


class Dota2AIAssistant:
    """刀塔2 AI智能助手"""
    
    def __init__(self, api_key: str = None, model_name: str = "deepseek-chat"):
        """初始化AI助手
        
        Args:
            api_key: DeepSeek API密钥
            model_name: 使用的模型名称（基础模型或微调后的模型）
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.model_name = model_name
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def analyze_match(self, match_id: str, match_data: Dict) -> Dict[str, str]:
        """分析比赛并提供智能洞察
        
        Args:
            match_id: 比赛ID
            match_data: 比赛数据（包含四数据源信息）
            
        Returns:
            分析结果和建议
        """
        
        # 构建分析请求
        user_prompt = self._build_analysis_prompt(match_id, match_data)
        
        # 调用AI模型
        response = self._call_ai_model(user_prompt)
        
        # 解析和格式化结果
        analysis = self._parse_analysis_response(response, match_id)
        
        return analysis
    
    def get_learning_recommendations(self, user_level: str = "intermediate") -> Dict[str, list]:
        """获取个性化学习推荐
        
        Args:
            user_level: 用户水平 (beginner, intermediate, advanced)
            
        Returns:
            学习推荐内容
        """
        
        prompt = f"""作为刀塔2智能助手，请为{user_level}水平的玩家推荐学习内容：

**推荐要求：**
1. 3个核心技能练习重点
2. 2个适合观看的职业比赛
3. 1个实战练习建议
4. 针对当前版本的注意事项

请提供具体、实用的建议。"""
        
        response = self._call_ai_model(prompt)
        
        return {
            "recommendations": response,
            "user_level": user_level,
            "timestamp": "2024-01-15T14:30:00Z"
        }
    
    def answer_community_question(self, question: str, context: Dict = None) -> str:
        """回答社区用户问题
        
        Args:
            question: 用户问题
            context: 上下文信息（可选）
            
        Returns:
            AI回答
        """
        
        # 构建问题提示
        prompt = f"""作为刀塔2智能助手，请回答社区用户的问题：

**用户问题：** {question}

**回答要求：**
1. 基于专业知识和数据
2. 提供具体建议
3. 语言友好易懂
4. 鼓励进一步学习

**上下文信息：** {context or '无额外上下文'}"""
        
        return self._call_ai_model(prompt)
    
    def _build_analysis_prompt(self, match_id: str, match_data: Dict) -> str:
        """构建分析提示"""
        
        return f"""作为刀塔2专家分析师，请深度分析这场比赛 #{match_id}：

**比赛数据：**
{json.dumps(match_data, ensure_ascii=False, indent=2)}

**分析要求：**
1. 关键战术要点分析
2. 可学习的技巧和策略
3. 基于数据的客观评价
4. 实战应用建议
5. 类似比赛推荐

请提供专业、详细的分析，帮助玩家提升水平。"""
    
    def _call_ai_model(self, prompt: str) -> str:
        """调用AI模型"""
        
        if not self.api_key:
            return "API密钥未配置，请设置 DEEPSEEK_API_KEY 环境变量"
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的刀塔2比赛分析师和智能助手。你将基于比赛数据、社区讨论和战术分析，为用户提供深度的比赛洞察和学习建议。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                return f"API调用失败: {response.status_code}"
                
        except Exception as e:
            return f"API调用异常: {e}"
    
    def _parse_analysis_response(self, response: str, match_id: str) -> Dict[str, str]:
        """解析分析响应"""
        
        return {
            "match_id": match_id,
            "analysis": response,
            "summary": response[:200] + "..." if len(response) > 200 else response,
            "has_recommendations": "推荐" in response or "建议" in response,
            "confidence": "高" if len(response) > 500 else "中"
        }


def demo_community_integration():
    """演示社区集成"""
    
    print("🎮 刀塔2 AI智能助手社区集成演示")
    print("=" * 50)
    
    # 创建AI助手（使用基础模型演示）
    assistant = Dota2AIAssistant(model_name="deepseek-chat")
    
    # 演示1: 比赛分析
    print("\n📊 演示1: 比赛分析")
    match_data = {
        "duration": "45:30",
        "winner": "天辉",
        "teams": "天辉 vs 夜魇",
        "key_moments": ["20分钟肉山团战", "35分钟高地推进"],
        "economy_gap": "15000金币"
    }
    
    analysis = assistant.analyze_match("1234567890", match_data)
    print(f"比赛分析摘要: {analysis['summary']}")
    print(f"分析置信度: {analysis['confidence']}")
    
    # 演示2: 学习推荐
    print("\n📚 演示2: 个性化学习推荐")
    recommendations = assistant.get_learning_recommendations("intermediate")
    print(f"推荐内容: {recommendations['recommendations'][:200]}...")
    
    # 演示3: 社区问答
    print("\n💬 演示3: 社区问答")
    question = "如何提高团战中的定位能力？"
    answer = assistant.answer_community_question(question)
    print(f"用户问题: {question}")
    print(f"AI回答: {answer[:200]}...")
    
    print("\n✅ 演示完成！")
    print("\n💡 集成建议:")
    print("1. 在Web界面中添加AI分析按钮")
    print("2. 为不同用户水平提供个性化推荐")
    print("3. 集成到社区讨论和问答功能")
    print("4. 添加用户反馈收集机制")


if __name__ == '__main__':
    demo_community_integration()