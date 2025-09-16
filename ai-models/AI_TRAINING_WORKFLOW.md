# 🎯 刀塔2 AI智能助手训练数据工作流

## 📋 概述
本文档描述了如何将社区比赛数据和用户评论整合，通过DeepSeek API进行微调，创建刀塔2智能助手的完整流程。

## 🔄 数据流程

### 1️⃣ 数据收集阶段
- **比赛数据**: 从OpenDota、Stratz、Liquipedia、DEM四个数据源获取
- **社区评论**: 用户精选评论，包含点赞数和用户反馈
- **数据整合**: 通过`AITrainingDataGenerator`类统一处理

### 2️⃣ 数据处理阶段
```
原始数据 → 训练数据生成器 → DeepSeek格式处理器 → API微调
```

#### 训练数据生成器 (`training_data_generator.py`)
- **功能**: 将结构化数据转换为训练文本
- **输入**: 比赛ID + 四数据源 + 社区评论
- **输出**: 结构化训练文本

#### DeepSeek格式处理器 (`deepseek_processor.py`) 
- **功能**: 转换为DeepSeek API格式
- **格式**: 对话式训练数据 (system/user/assistant)
- **优化**: 添加专业提示和结构化回复

### 3️⃣ 模型微调阶段
- **API**: DeepSeek微调API
- **基础模型**: deepseek-chat
- **训练数据**: 多轮对话格式
- **评估**: BLEU、ROUGE、困惑度等指标

## 📁 文件结构
```
ai-models/
├── configs/
│   └── deepseek_finetune.yaml      # 微调配置
├── data/
│   ├── training_samples.json       # 原始训练样本
│   └── deepseek_training_data.json # DeepSeek格式数据
├── scripts/
│   ├── training_data_generator.py  # 训练数据生成器
│   ├── deepseek_processor.py      # 格式处理器
│   └── deepseek_api_client.py     # API客户端
└── README.md                       # 项目说明
```

## 🚀 快速开始

### 环境准备
```bash
# 安装依赖
pip install pyyaml requests

# 设置API密钥
export DEEPSEEK_API_KEY="your-api-key-here"
```

### 生成训练数据
```bash
cd ai-models/scripts
python training_data_generator.py
```

### 处理为DeepSeek格式
```bash
python deepseek_processor.py
```

### 启动微调（需要API密钥）
```bash
python deepseek_api_client.py
```

## 🎯 训练数据格式

### 输入数据示例
```json
{
  "match_id": "1234567890",
  "training_text": "## 比赛数据分析：天辉 vs 夜魇\n...",
  "metadata": {
    "data_sources": ["opendota", "stratz", "liquipedia", "dem"],
    "has_comments": true,
    "generated_at": "2024-01-15T14:30:00Z"
  }
}
```

### DeepSeek格式示例
```json
{
  "messages": [
    {
      "role": "system",
      "content": "你是一个专业的刀塔2比赛分析师..."
    },
    {
      "role": "user",
      "content": "请分析这场比赛的关键战术要点..."
    },
    {
      "role": "assistant", 
      "content": "我来为你深度分析这场精彩的刀塔比赛..."
    }
  ],
  "metadata": {
    "match_id": "1234567890",
    "has_comments": true
  }
}
```

## 📊 数据质量指标

### 训练数据统计
- **总样本数**: 3个（演示数据）
- **平均输入长度**: 58字符
- **平均输出长度**: 250字符  
- **包含评论比例**: 100%
- **多数据源比例**: 100%

### 内容质量评估
- **结构化程度**: 高（包含多个分析维度）
- **社区参与度**: 活跃（平均18.3个点赞）
- **专业深度**: 专业级（战术、技术、策略分析）

## 🔧 配置参数

### 微调配置 (`deepseek_finetune.yaml`)
```yaml
model_name: "deepseek-chat"
fine_tuned_model_name: "dota2-assistant-v1"

training:
  epochs: 3
  learning_rate: 1e-5
  batch_size: 4
  
model:
  max_tokens: 2048
  temperature: 0.7
  top_p: 0.9
```

## 🎮 智能助手功能

### 核心能力
1. **比赛分析**: 基于多数据源的综合分析
2. **战术解读**: 关键决策点和胜负手分析  
3. **学习建议**: 实战技巧和进阶方向
4. **社区洞察**: 整合用户观点和讨论
5. **个性化推荐**: 类似比赛推荐

### 使用场景
- **新手学习**: 理解游戏机制和基础策略
- **进阶提升**: 学习高级技巧和战术思维
- **比赛回顾**: 深度分析职业比赛
- **社区互动**: 获取多维度观点和建议

## 📈 后续优化

### 数据增强
- [ ] 增加更多比赛样本
- [ ] 丰富评论数据来源
- [ ] 添加多语言支持
- [ ] 整合实时比赛数据

### 模型优化
- [ ] 调整微调参数
- [ ] 增加评估指标
- [ ] 优化提示工程
- [ ] 支持流式回复

### 功能扩展
- [ ] 添加可视化分析
- [ ] 支持语音交互
- [ ] 集成实时数据
- [ ] 个性化推荐系统

## 🔗 相关链接

- [DeepSeek API文档](https://platform.deepseek.com/docs)
- [OpenDota API](https://docs.opendota.com/)
- [Stratz API](https://stratz.com/api)
- [Liquipedia API](https://liquipedia.net/api)

## 💡 最佳实践

### 数据准备
1. 确保数据质量和完整性
2. 平衡不同类型比赛的样本
3. 验证评论的相关性和质量
4. 定期更新训练数据

### 模型训练
1. 从小规模数据开始测试
2. 监控训练过程和指标
3. 进行充分的模型评估
4. 保存训练日志和检查点

### 部署应用
1. 设置合适的API限流
2. 实现错误处理和重试机制
3. 添加用户反馈收集
4. 持续监控模型表现

---

*最后更新: 2024-01-15*
*版本: v1.0*