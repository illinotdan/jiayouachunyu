#!/usr/bin/env python3
"""
DeepSeek API 集成脚本
用于上传训练数据和创建微调任务
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional
from pathlib import Path
import yaml


class DeepSeekAPIClient:
    """DeepSeek API客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com/v1"):
        """初始化API客户端
        
        Args:
            api_key: DeepSeek API密钥
            base_url: API基础URL
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if not self.api_key:
            raise ValueError("请提供DeepSeek API密钥，通过参数或环境变量 DEEPSEEK_API_KEY 设置")
    
    def upload_training_file(self, file_path: str) -> str:
        """上传训练文件
        
        Args:
            file_path: 训练文件路径
            
        Returns:
            文件ID
        """
        print(f"📤 上传训练文件: {file_path}")
        
        # 注意：DeepSeek API的具体文件上传端点可能需要调整
        # 这里使用假设的端点，实际使用时请参考官方文档
        url = f"{self.base_url}/files"
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(url, headers=self.headers, files=files)
            
            if response.status_code == 200:
                result = response.json()
                file_id = result.get('id')
                print(f"✅ 文件上传成功，ID: {file_id}")
                return file_id
            else:
                print(f"❌ 文件上传失败: {response.status_code} - {response.text}")
                raise Exception(f"文件上传失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 文件上传异常: {e}")
            raise
    
    def create_fine_tuning_job(self, training_file_id: str, model: str, 
                              validation_file_id: str = None, 
                              hyperparameters: Dict = None) -> str:
        """创建微调任务
        
        Args:
            training_file_id: 训练文件ID
            model: 基础模型名称
            validation_file_id: 验证文件ID（可选）
            hyperparameters: 超参数配置
            
        Returns:
            任务ID
        """
        print(f"🎯 创建微调任务...")
        
        # 注意：DeepSeek API的具体微调端点可能需要调整
        # 这里使用假设的端点，实际使用时请参考官方文档
        url = f"{self.base_url}/fine_tuning/jobs"
        
        payload = {
            "training_file": training_file_id,
            "model": model,
            "suffix": "dota2-assistant"
        }
        
        if validation_file_id:
            payload["validation_file"] = validation_file_id
            
        if hyperparameters:
            payload["hyperparameters"] = hyperparameters
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('id')
                print(f"✅ 微调任务创建成功，ID: {job_id}")
                return job_id
            else:
                print(f"❌ 微调任务创建失败: {response.status_code} - {response.text}")
                raise Exception(f"微调任务创建失败: {response.text}")
                
        except Exception as e:
            print(f"❌ 微调任务创建异常: {e}")
            raise
    
    def get_fine_tuning_job_status(self, job_id: str) -> Dict:
        """获取微调任务状态
        
        Args:
            job_id: 任务ID
            
        Returns:
            任务状态信息
        """
        url = f"{self.base_url}/fine_tuning/jobs/{job_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ 获取任务状态失败: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ 获取任务状态异常: {e}")
            return {}
    
    def list_fine_tuning_jobs(self, limit: int = 10) -> List[Dict]:
        """列出微调任务
        
        Args:
            limit: 返回任务数量限制
            
        Returns:
            任务列表
        """
        url = f"{self.base_url}/fine_tuning/jobs?limit={limit}"
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('data', [])
            else:
                print(f"❌ 获取任务列表失败: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ 获取任务列表异常: {e}")
            return []
    
    def test_fine_tuned_model(self, model_name: str, test_question: str) -> str:
        """测试微调后的模型
        
        Args:
            model_name: 模型名称
            test_question: 测试问题
            
        Returns:
            模型回复
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的刀塔2比赛分析师和智能助手。你将基于比赛数据、社区讨论和战术分析，为用户提供深度的比赛洞察和学习建议。"
                },
                {
                    "role": "user",
                    "content": test_question
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                print(f"❌ 模型测试失败: {response.status_code} - {response.text}")
                return ""
                
        except Exception as e:
            print(f"❌ 模型测试异常: {e}")
            return ""


def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        return {}


def main():
    """主函数 - 演示DeepSeek API使用流程"""
    print("🚀 启动DeepSeek API集成演示...")
    
    # 加载配置
    config_path = "c:/Users/yb/PycharmProjects/PythonProject/ai-models/configs/deepseek_finetune.yaml"
    config = load_config(config_path)
    
    if not config:
        print("❌ 无法加载配置文件")
        return
    
    # 创建API客户端
    try:
        client = DeepSeekAPIClient(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=config.get('api', {}).get('base_url', 'https://api.deepseek.com/v1')
        )
        print("✅ API客户端创建成功")
        
    except Exception as e:
        print(f"❌ API客户端创建失败: {e}")
        print("\n💡 请设置环境变量 DEEPSEEK_API_KEY:")
        print("   export DEEPSEEK_API_KEY='your-api-key-here'")
        return
    
    # 演示流程（注释掉实际API调用，因为需要真实的API密钥）
    print("\n📋 演示流程:")
    print("1. 上传训练文件")
    print("2. 创建微调任务") 
    print("3. 监控训练进度")
    print("4. 测试微调模型")
    
    # 实际使用时取消注释以下代码
    """
    try:
        # 1. 上传训练文件
        training_file_path = "c:/Users/yb/PycharmProjects/PythonProject/ai-models/data/deepseek_training_data.json"
        file_id = client.upload_training_file(training_file_path)
        
        # 2. 创建微调任务
        model_name = config.get('model_name', 'deepseek-chat')
        hyperparameters = config.get('training', {})
        
        job_id = client.create_fine_tuning_job(
            training_file_id=file_id,
            model=model_name,
            hyperparameters=hyperparameters
        )
        
        # 3. 监控训练进度
        print(f"⏳ 监控训练进度...")
        while True:
            status = client.get_fine_tuning_job_status(job_id)
            state = status.get('status', 'unknown')
            print(f"训练状态: {state}")
            
            if state in ['succeeded', 'failed']:
                break
                
            time.sleep(60)  # 每分钟检查一次
        
        if state == 'succeeded':
            # 4. 测试微调模型
            fine_tuned_model = status.get('fine_tuned_model')
            if fine_tuned_model:
                print(f"🎉 微调成功！模型名称: {fine_tuned_model}")
                
                # 测试模型
                test_question = "分析一场40分钟比赛的战术要点"
                response = client.test_fine_tuned_model(fine_tuned_model, test_question)
                print(f"测试回复: {response[:200]}...")
        
    except Exception as e:
        print(f"❌ 微调流程失败: {e}")
    """
    
    print("\n✅ 演示完成！")
    print("\n下一步:")
    print("1. 获取DeepSeek API密钥")
    print("2. 设置环境变量 DEEPSEEK_API_KEY")
    print("3. 取消注释main函数中的代码以运行实际微调")
    print("4. 在应用中集成微调后的模型")


if __name__ == '__main__':
    main()