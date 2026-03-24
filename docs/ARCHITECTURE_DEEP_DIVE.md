# 架构深度分析：多Agent设计的必要性与优化

**测试日期**: 2026-03-24
**测试查询**: "MCP协议是什么？有什么优势和应用场景？"
**API**: Kimi (Moonshot)

---

## 真实性能数据

```
总耗时: 340.53s (5.7分钟)
总成本: $0.2192

各阶段耗时:
├── Planner:    28.24s  (8%)   - 生成4个子查询
├── Researcher: 30.69s  (9%)   - 搜索2个查询，10个来源
├── Synthesis:  194.51s (57%)  - 生成4个章节 (最慢！)
├── Critic:     53.73s  (16%)  - 评分0.60 (失败)
└── Writer:     33.37s  (10%)  - 组装报告
```

---

## 核心问题：多Agent架构的合理性

### 当前架构的问题

#### 1. Synthesis成为瓶颈 (194秒！)

**当前做法**:
```python
# Synthesis为每个章节调用一次LLM
for section in expected_sections:
    content = llm.generate(section_prompt)  # 每次40-50秒
```

4个章节 = 4次串行调用 = 194秒

**问题**:
- 章节生成是独立的，为什么要串行？
- 每个章节的prompt都包含相同的findings（重复输入）
- 每次调用都有API往返延迟

#### 2. Agent之间信息传递损耗

```
Findings (研究数据)
    ↓ (提取summary)
Sections (合成内容)
    ↓ (提取title+content)
Report (最终组装)
```

每一步都在丢失信息：
- Researcher的sources没有在section中引用
- Synthesis的章节结构没有利用findings的query关系
- Writer重新生成摘要，而不是提取已有信息

#### 3. 伪并行：没有真正利用多Agent优势

当前架构所谓的"多Agent"实际上是**串行执行**：

```
Planner → Researcher → Synthesis → Critic → Writer
   (1)      (1)          (4)        (1)      (1)  = 8次串行调用
```

真正的多Agent应该是：
```
Planner
   ↓
Researcher (并行搜索多个查询)
   ↓
Synthesis (并行生成多个章节)  ← 未实现
   ↓
Critic + Writer (可以并行)    ← 未实现
```

---

## 关键洞察：哪些Agent真的需要分离？

### 应该合并的Agent

#### Researcher + Synthesis → ResearchSynthesizer

**理由**:
- Researcher生成summary后，Synthesis又基于同样的findings重新理解
- 可以直接在搜索后实时合成，不需要二次传递
- 减少一次完整的LLM调用链

**新流程**:
```python
for query in sub_queries:
    findings = search(query)
    section = synthesize(query, findings)  # 搜索后立即合成
```

#### Critic的困境

**当前问题**:
- Critic评分0.60，但报告还是生成了
- 没有真正的反馈循环（max_iterations=1）
- 用户不关心中间评分，只关心最终质量

**重新思考**:
Critic应该成为一个**质量门控**而不是独立Agent：
```python
# 在Synthesis内部进行自评
section = synthesize(findings)
quality_score = self_critique(section)
if quality_score < 0.7:
    section = regenerate_with_feedback(section, feedback)
```

### 应该保留分离的Agent

#### Planner必须独立

- 规划需要全局视角，不能边做边规划
- 规划结果影响后续所有Agent的执行策略
- 可以复用规划结果（用户可编辑）

#### Writer应该简化

- 不应该重新生成内容，只做格式化
- 利用已有sections直接组装
- 只调用LLM生成Executive Summary

---

## 重构方案：从5个Agent到3个Agent

### 新架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Planner Agent                           │
│              (策略制定 + 查询分解 + 结构设计)                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              ResearchSynthesizer Agent                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Search Q1    │  │ Search Q2    │  │ Search Q3    │      │
│  │      ↓       │  │      ↓       │  │      ↓       │      │
│  │ Synthesize   │  │ Synthesize   │  │ Synthesize   │      │
│  │ Section 1    │  │ Section 2    │  │ Section 3    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ↓                                  │
│              Self-Critique & Refine                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Writer Agent                            │
│              (格式化 + Executive Summary)                   │
└─────────────────────────────────────────────────────────────┘
```

### 优势

1. **真正的并行**：多个查询的搜索和合成都可并行
2. **减少延迟**：从8次串行调用减少到3个阶段
3. **信息保留**：搜索和合成在一个上下文中，避免信息损耗
4. **自包含质量**：ResearchSynthesizer内部自评自纠

### 预期性能提升

```
当前: 340秒
优化后:
├── Planner: 30s
├── ResearchSynthesizer (并行):
│   ├── 搜索3个查询: max(10s, 12s, 8s) = 12s
│   └── 合成3个章节: max(45s, 50s, 40s) = 50s
│   └── 自评优化: 20s
│   └── 小计: 82s (vs 194s+54s=248s)
└── Writer: 30s

总计: ~142s (节省58%时间)
```

---

## 更深层次的问题：没有利用工具调用的力量

### 当前架构的LLM使用方式

```python
# 每个Agent都是：Prompt → LLM → Parse Output
# 这是"文本进文本出"模式
```

### 现代LLM的最佳实践：Function Calling

```python
# Planner应该输出结构化的执行计划
{
    "sub_queries": [...],
    "expected_sections": [...],
    "search_tools": ["duckduckgo", "arxiv"],
    "synthesis_strategy": "parallel"
}

# ResearchSynthesizer应该调用工具
functions = {
    "search": search_tool,
    "synthesize": synthesize_tool,
    "critique": critique_tool
}
```

### 为什么这很重要？

1. **可靠性**: 结构化输出比文本解析可靠
2. **可观测性**: 每个工具调用都可追踪
3. **灵活性**:  Planner可以动态选择策略
4. **成本优化**: 小模型决定策略，大模型执行内容

---

## 具体改进建议

### 短期改进（保留当前架构，优化性能）

1. **并行化Synthesis**
```python
import asyncio

async def synthesize_section(section_title, findings):
    ...

# 并行生成所有章节
sections = await asyncio.gather(*[
    synthesize_section(title, findings)
    for title in expected_sections
])
```

2. **移除Critic或改为可选**
- 只有当用户明确要求迭代优化时才启用
- 默认单次通过，节省53秒

3. **Synthesis和Research合并**
- 在researcher.py中直接合成section
- 消除数据传递损耗

### 中期重构（3-Agent架构）

1. 创建 `ResearchSynthesizer` 替换 Researcher + Synthesis
2. 内部实现并行搜索+合成
3. 添加自评机制

### 长期演进（工具调用架构）

1. 使用 OpenAI Functions / LangChain Tools
2. Planner生成执行计划（JSON）
3. 执行引擎并行调度工具

---

## 结论

### 用户的质疑是正确的

当前5-Agent架构存在**过度设计**：

1. **复杂度不匹配**: 每个Agent做的事情太简单（基本都是一次LLM调用）
2. **伪并行**: 实际是串行执行，没有利用多Agent优势
3. **信息损耗**: 每经过一个Agent，信息就丢失一部分

### 多Agent的真正价值

多Agent架构在以下场景有价值：

1. **真正需要不同专业能力**: 医学诊断（症状分析→检查建议→诊断→治疗方案）
2. **需要人类介入的节点**: Planner生成计划后，人类编辑，再执行
3. **长周期任务**: 每个Agent可以异步执行，人类随时查看进度

对于**单次研究报告生成**，3-Agent架构足够：
- Planner: 策略制定
- ResearchSynthesizer: 并行搜索+合成+自评
- Writer: 格式化输出

### 下一步行动

1. 实现Synthesis并行化（立即可做，节省2分钟）
2. 合并Researcher和Synthesis（减少信息损耗）
3. 评估3-Agent架构的收益
