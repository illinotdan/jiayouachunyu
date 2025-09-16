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
# 安装依赖
pip install pyyaml requests

# 设置API密钥（可选，用于实际微调）
export DEEPSEEK_API_KEY="your-api-key-here"
```

### 2. 生成训练数据
```bash
cd ai-models/scripts
python training_data_generator.py
```

### 3. 处理为DeepSeek格式
```bash
python deepseek_processor.py
```

### 4. 测试集成示例
```bash
python ai_assistant_demo.py
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
- **功能**: 将比赛数据+评论转换为训练文本
- **输入**: 比赛ID、四数据源、社区评论
- **输出**: 结构化训练文本
- **特色**: 支持后端集成和模拟数据两种模式

### 2. DeepSeekDataProcessor
- **功能**: 转换为DeepSeek API格式
- **处理**: 对话式格式转换、内容优化
- **输出**: 符合微调要求的JSON格式
- **统计**: 生成详细的数据处理报告

### 3. DeepSeekAPIClient
- **功能**: DeepSeek API集成
- **支持**: 文件上传、任务创建、状态监控
- **测试**: 模型测试和评估
- **安全**: 错误处理和重试机制

### 4. Dota2AIAssistant
- **功能**: 社区集成接口
- **能力**: 比赛分析、学习推荐、问答系统
- **定制**: 支持不同用户水平
- **扩展**: 易于添加新功能

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