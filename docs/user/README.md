# Deep Research Agent 用户文档

## 项目简介

Deep Research Agent 是一个**多智能体深度研究系统**，核心价值在于：

- **批量自动化**：一次性研究数百个主题
- **过程可观测**：完整的执行追踪和成本监控
- **知识沉淀**：研究结果自动存储，支持检索和复用
- **标准化输出**：一致的报告格式和质量

## 与 Claude Code 的区别

| 维度 | Claude Code | Deep Research Agent |
|------|-------------|---------------------|
| 定位 | 交互式编程助手 | 自动化研究流水线 |
| 批量处理 | ❌ 不支持 | ✅ 支持数百主题 |
| 可追溯性 | 有限 | 完整的执行trace |
| 成本优化 | 无 | 模型分层路由 |
| 知识沉淀 | 无 | 向量存储积累 |

## 核心优势

### 1. 批量研究能力

```bash
# 从文件批量读取研究主题
deep-research --batch topics.txt --output reports/

# 处理结果：
# reports/topic_1_report.md
# reports/topic_2_report.md
# ...
```

### 2. 完整的可观测性

每次研究生成完整的执行trace：
- 每个Agent的输入输出
- Token消耗和成本
- 搜索来源和引用
- 执行时间和性能指标

### 3. 模型分层策略

智能选择模型，平衡质量和成本：
- 轻量任务 → GPT-4o-mini（低成本）
- 中等任务 → GPT-4o（平衡）
- 复杂任务 → o1/Opus（高质量）

### 4. 知识沉淀

研究结果自动存入向量数据库：
- 支持语义检索
- 跨研究主题关联
- 知识图谱构建（未来）

## 快速开始

### 安装

```bash
git clone https://github.com/Jrx2003/deep-research-agent.git
cd deep-research-agent
pip install -e ".[dev]"
```

### 配置

```bash
cp .env.example .env
# 编辑 .env 文件，填入API密钥
```

必需的环境变量：
```bash
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

可选的环境变量：
```bash
SERPAPI_API_KEY=your_serpapi_key  # 用于Google搜索
LANGCHAIN_API_KEY=your_langsmith_key  # 用于trace追踪
```

### 使用

#### 命令行模式

```bash
# 单主题研究
deep-research "量子计算最新进展"

# 批量研究
deep-research --batch topics.txt

# 指定输出格式
deep-research "AI Agent架构" --format markdown --output report.md
```

#### Web界面

```bash
streamlit run src/app/ui.py
```

打开浏览器访问 `http://localhost:8501`

#### API服务

```bash
uvicorn src.app.api:app --reload
```

API文档：`http://localhost:8000/docs`

## 使用场景

### 场景1：行业调研

需要快速了解一个行业的现状：

```bash
deep-research "2024年中国新能源汽车市场分析"
```

输出：包含市场规模、竞争格局、技术趋势、政策环境的完整报告

### 场景2：技术调研

调研某项技术的最新进展：

```bash
deep-research "RAG技术最新进展和最佳实践"
```

输出：技术原理、主流方案、性能对比、应用案例

### 场景3：竞品分析

批量分析多个竞品：

```bash
# products.txt 内容：
# OpenAI GPT-4
# Anthropic Claude
# Google Gemini
# Meta Llama

deep-research --batch products.txt --template competitor_analysis
```

### 场景4：学术研究

文献综述辅助：

```bash
deep-research "Transformer架构在计算机视觉中的应用综述"
```

## 输出示例

```markdown
# RAG技术最新进展和最佳实践

## 执行摘要

RAG（检索增强生成）技术在2024年取得了显著进展...

## 技术原理

### 基础架构
...

### 检索策略
...

## 主流方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| ... | ... | ... | ... |

## 最佳实践

1. ...
2. ...

## 参考来源

1. [论文标题](链接) - 作者, 年份
2. [博客文章](链接) - 作者, 日期

---
*研究生成时间: 2024-XX-XX*
*总成本: $0.XX*
```

## 高级配置

### 自定义研究深度

```python
# 配置研究深度
config = {
    "max_iterations": 3,  # 最大反馈循环次数
    "search_depth": "deep",  # shallow/normal/deep
    "max_sources": 10,  # 最大引用来源数
}
```

### 自定义输出模板

```bash
# 使用自定义模板
deep-research "主题" --template templates/my_template.j2
```

## 成本估算

以研究一个中等复杂度的主题为例：

| 组件 | Token消耗 | 成本 |
|------|-----------|------|
| Planner | 2K input / 500 output | $0.01 |
| Researcher | 5K input / 2K output | $0.03 |
| Synthesis | 10K input / 3K output | $0.15 |
| Critic | 15K input / 2K output | $0.75 |
| Writer | 10K input / 5K output | $0.50 |
| **总计** | - | **~$1.44** |

使用轻量模型可将成本降至 ~$0.20。

## 常见问题

### Q: 研究结果质量如何保证？

A: 通过多层质量控制：
1. Critic Agent 自动审查
2. 多源交叉验证
3. 引用来源可追溯
4. 人工可介入反馈循环

### Q: 支持哪些语言？

A: 支持中文和英文研究，输出语言可配置。

### Q: 如何处理敏感信息？

A:
- 所有API密钥存储在本地环境变量
- 搜索历史仅在本地存储
- 可选择不向LangSmith发送trace

## 获取帮助

- GitHub Issues: [提交问题](https://github.com/Jrx2003/deep-research-agent/issues)
- 开发文档: [AGENT.md](../AGENT.md)
- 架构详解: [架构详解.md](./架构详解.md)
