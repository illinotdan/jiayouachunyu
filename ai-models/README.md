# 🤖 刀塔2 AI智能助手 - 训练数据生成与微调

## 🎯 项目概述

本项目实现了将社区比赛数据与用户评论整合，通过DeepSeek API进行微调，创建专业的刀塔2智能助手的完整解决方案。

## ✨ 核心功能

- **多数据源整合**: 集成OpenDota、Stratz、Liquipedia、DEM四个数据源
- **社区评论融合**: 结合用户精选评论和点赞数据
- **智能文本生成**: 自动生成结构化训练文本
- **DeepSeek微调**: 专业级对话式AI训练
- **社区集成**: 易于在现有社区平台中集成

## 🏗️ 项目结构

```
ai-models/
├── configs/
│   └── deepseek_finetune.yaml      # 微调配置文件
├── data/
│   ├── training_samples.json       # 原始训练样本
│   └── deepseek_training_data.json # DeepSeek格式数据
├── scripts/
│   ├── training_data_generator.py  # 训练数据生成器
│   ├── deepseek_processor.py       # 格式处理器
│   ├── deepseek_api_client.py      # API客户端
│   └── ai_assistant_demo.py        # 集成示例
└── AI_TRAINING_WORKFLOW.md         # 完整工作流文档
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <repository-url>
cd ai-models

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 设置API密钥（可选，用于实际微调）
export DEEPSEEK_API_KEY="your-api-key-here"
```

### 2. 生成训练数据
```bash
# 生成完整训练数据集
cd ai-models/scripts
python training_data_generator.py --config ../configs/training_config.yaml

# 处理社区评论数据
python process_community_comments.py --input ../data/raw/community_comments.json

# 格式化为DeepSeek格式
python deepseek_processor.py --input ../data/processed/training_data.json --output ../data/formatted/deepseek_training_data.json
```

### 3. 模型训练与验证
```bash
# 启动DeepSeek微调训练
python train_deepseek_model.py --data ../data/formatted/deepseek_training_data.json --model deepseek-r1

# 验证训练结果
python validate_model.py --model_path ../models/deepseek_finetuned/ --test_data ../data/test/test_data.json

# 生成模型评估报告
python generate_model_report.py --model_path ../models/deepseek_finetuned/ --output ../reports/model_evaluation.md
```

### 4. 使用示例
```python
# 基础AI分析示例
from ai_models import Dota2AIAssistant

# 初始化AI助手
ai = Dota2AIAssistant(model="deepseek-r1")

# 分析比赛
match_analysis = ai.analyze_match(match_id=1234567890)
print(f"比赛分析: {match_analysis}")

# 生成训练数据
training_data = ai.generate_training_data(
    matches=[1234567890, 1234567891],
    include_comments=True,
    output_format="deepseek"
)

# 个性化推荐
recommendations = ai.get_personalized_recommendations(
    user_id=123,
    skill_level="intermediate",
    preferred_heroes=["invoker", "shadow_fiend"]
)
```

### 5. 测试验证
```bash
# 运行完整测试套件
python -m pytest ../tests/ -v

# 验证训练数据质量
python validate_training_data.py --data ../data/formatted/deepseek_training_data.json

# 生成数据质量报告
python generate_data_report.py --input ../data/formatted/ --output ../reports/data_quality_report.md

# 测试AI分析功能
python test_ai_analysis.py --match_id 1234567890 --model deepseek-r1
```

## 📊 数据流程

### 输入数据格式
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

### 输出数据格式（DeepSeek）
```json
{
  "messages": [
    {"role": "system", "content": "你是专业的刀塔2分析师..."},
    {"role": "user", "content": "请分析这场比赛..."},
    {"role": "assistant", "content": "我来为你深度分析..."}
  ],
  "metadata": {
    "match_id": "1234567890",
    "has_comments": true
  }
}
```

## 🎯 核心组件

### 1. AITrainingDataGenerator
- **功能**: 从多源数据生成AI训练数据
- **输入**: 比赛数据、专家观点、社区讨论、官方攻略
- **输出**: 结构化训练数据
- **配置**: `configs/training_config.yaml`
- **特性**: 支持四源数据整合、质量评估、格式标准化

### 2. DeepSeekDataProcessor
- **功能**: 将训练数据格式化为DeepSeek模型格式
- **输入**: 结构化训练数据
- **输出**: DeepSeek兼容格式数据
- **配置**: `configs/deepseek_config.yaml`
- **特性**: 多模型支持、格式验证、批量处理

### 3. CommunityCommentProcessor
- **功能**: 处理和筛选社区评论
- **输入**: 原始社区评论数据
- **输出**: 高质量评论数据
- **特色**: 基于点赞数和AI质量评估筛选、情感分析、相关性评分

### 4. Dota2AIAssistant
- **功能**: AI助手核心类，提供智能分析服务
- **方法**: 
  - `analyze_match()`: 比赛分析
  - `generate_training_data()`: 训练数据生成
  - `get_personalized_recommendations()`: 个性化推荐
  - `process_community_content()`: 社区内容处理
- **配置**: `configs/ai_assistant_config.yaml`

### 5. ModelValidator
- **功能**: 模型训练和验证工具
- **输入**: 训练数据、测试数据
- **输出**: 模型性能报告、验证结果
- **特性**: 交叉验证、性能指标、A/B测试支持

## 📈 训练数据示例

### 分析内容结构
1. **比赛概况**: 基础信息和关键数据
2. **英雄分析**: 阵容搭配和战术分析
3. **经济走势**: 装备时机和经济差距
4. **社区洞察**: 用户评论和观点总结
5. **AI综合分析**: 深度学习要点和实战建议

### 质量指标
- **数据完整性**: 100%（四数据源+评论）
- **内容结构化**: 高（5个分析维度）
- **社区参与度**: 活跃（平均18.3点赞）
- **专业深度**: 专业级（战术+技术+策略）

## 🔧 配置选项

### 微调参数
```yaml
model_name: "deepseek-chat"
training:
  epochs: 3
  learning_rate: 1e-5
  batch_size: 4
model:
  max_tokens: 2048
  temperature: 0.7
```

### 数据配置
```yaml
data:
  validation_split: 0.2
  max_samples: 1000
  min_comment_quality: 10  # 最小点赞数
```

## 🎮 应用场景

### 1. 比赛分析
- **战术解读**: 关键决策点和胜负手
- **数据可视化**: 结合图表展示分析结果
- **学习要点**: 可应用的实战技巧

### 2. 社区互动
- **智能问答**: 回答用户刀塔相关问题
- **个性化推荐**: 基于用户水平推荐内容
- **讨论引导**: 促进社区深度讨论

### 3. 教学辅助
- **新手指导**: 基础知识和入门技巧
- **进阶提升**: 高级策略和战术思维
- **实战演练**: 具体场景分析和建议

## 🚀 部署建议

### 环境要求
- Python 3.8+
- 依赖包: pyyaml, requests
- DeepSeek API密钥（生产环境）

### 性能优化
- **缓存机制**: 缓存常用分析结果
- **异步处理**: 支持批量数据处理
- **限流控制**: 合理的API调用频率
- **错误处理**: 完善的异常处理机制

### 监控指标
- **响应时间**: API调用耗时
- **成功率**: 模型响应质量
- **用户满意度**: 反馈收集和分析
- **成本控制**: API调用费用管理

## 🔮 未来扩展

### 数据增强
- [ ] 多语言支持（英文、俄文等）
- [ ] 实时数据集成
- [ ] 用户行为分析
- [ ] 个性化学习路径

### 模型优化
- [ ] 多模型集成
- [ ] 领域专业知识增强
- [ ] 上下文理解能力提升
- [ ] 情感分析和用户偏好

### 功能扩展
- [ ] 语音交互支持
- [ ] 图像识别（小地图分析）
- [ ] 实时比赛预测
- [ ] 团队协作建议

## 📞 支持与联系

### 文档资源
- [完整工作流文档](AI_TRAINING_WORKFLOW.md)
- [DeepSeek API文档](https://platform.deepseek.com/docs)
- [配置说明](configs/deepseek_finetune.yaml)

### 问题反馈
- 提交Issue到项目仓库
- 联系开发团队
- 查看常见问题解答

---

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**

**🔧 持续更新中，欢迎贡献代码和建议！**