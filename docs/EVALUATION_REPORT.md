# Deep Research Agent - 质量评估报告

**评估日期**: 2026-03-24
**评估方式**: Mock模式测试 + Kimi API测试
**测试查询**: "MCP协议是什么", "RAG技术最新进展", "向量数据库对比"

---

## 执行摘要

经过真实API测试，项目核心流程已跑通，但报告质量和用户体验存在多个问题需要解决。主要问题集中在：**报告格式不规范、内容重复、章节结构混乱、成本追踪不准确**。

---

## 发现问题清单

### 🔴 严重问题 (P0)

#### 1. 报告格式混乱
**问题描述**: Writer Agent生成的报告格式混乱，包含大量冗余文本

**具体表现**:
```markdown
# Research Report: MCP协议是什么

## 1. Introduction
Section Title: 1. Introduction

The field of RAG technology has witnessed significant advancements...
```

**问题分析**:
- 章节标题重复出现（"## 1. Introduction" 后又出现 "Section Title: 1. Introduction"）
- Synthesis Agent在内容中硬编码了"Section Title:"前缀
- Writer没有清理这些冗余标记

**影响**: 报告专业度极低，无法直接使用

---

#### 2. 章节结构失控
**问题描述**: Synthesis Agent生成过多章节，且命名不规范

**具体表现**:
- 生成8个章节，远超过预期的3-5个
- 章节名以数字开头（"1. Introduction", "2. Literature Review"）
- 与预期章节不匹配

**日志证据**:
```
Sections: 8
Section 1: 1. Introduction
Section 2: 2. Literature Review
Section 3: 3. Latest Advancements in RAG Technology
...
```

**影响**: 报告冗长、结构不清

---

#### 3. 内容高度重复
**问题描述**: 多个章节内容几乎完全相同

**具体表现**:
- "Latest Advancements" 和 "Applications" 章节开头都是 "The field of RAG technology has witnessed significant advancements..."
- 每个章节都包含类似的模板化语言
- 缺乏实质性的差异化内容

**影响**: 报告信息密度低，浪费token成本

---

### 🟠 中等问题 (P1)

#### 4. 成本追踪不准确
**问题描述**: Cost计算显示为0或明显偏低

**具体表现**:
```
Cost: $0.0000  # Writer阶段显示为0
```

**问题分析**:
- Writer Agent调用了3次LLM（报告主体 + 摘要 + 结论），但成本只计算了一次
- Researcher Agent聚合成本时使用了placeholder
- 缺乏细粒度的token计数

**影响**: 用户无法准确了解实际成本

---

#### 5. 引用来源格式错误
**问题描述**: 引用格式不统一，且Mock来源显示为example.com

**具体表现**:
```markdown
## References
1. [Understanding MCP协议是什么](https://example.com/mcp协议是什么)
```

**影响**: 报告可信度低

---

#### 6. Review评分偏低
**问题描述**: Critic Agent评分过于宽松或过于严格

**具体表现**:
- 缺少章节时评分仍为0.70（应更低）
- 只有1条feedback，缺乏详细建议

**影响**: 质量控制机制失效

---

### 🟡 轻微问题 (P2)

#### 7. 搜索查询处理不当
**问题描述**: 子查询被逐字符搜索（已修复）

**状态**: ✅ 已修复

---

#### 8. 缺乏执行摘要和结论
**问题描述**: Writer生成的执行摘要质量差

**具体表现**:
- 执行摘要只是简单复制内容开头
- 缺乏关键要点提炼
- 结论部分空泛

---

## 根本原因分析

### 架构层面

1. **Agent职责不清**
   - Synthesis既负责内容生成又负责章节结构设计
   - Writer只是简单拼接，没有真正的"写作"

2. **Prompt工程不足**
   - Synthesis Prompt要求生成"Section Title:"前缀
   - Writer Prompt没有要求清理输入
   - 缺乏输出格式约束

3. **State管理问题**
   - 没有统一的章节命名规范
   - 缺乏内容去重机制

---

## 解决方案

### 短期修复 (1-2天)

#### Fix 1: 清理章节标题前缀
**文件**: `deep_research_agent/agents/synthesis.py`

```python
# 移除内容中的 "Section Title:" 前缀
content = content.replace(f"Section Title: {section_title}\n\n", "")
content = content.replace(f"Section Title: {section_title}\n", "")
```

#### Fix 2: 限制章节数量
**文件**: `deep_research_agent/agents/planner.py`

```python
# 限制子查询数量
max_sub_queries = 3
plan_data["sub_queries"] = plan_data["sub_queries"][:max_sub_queries]
plan_data["expected_sections"] = plan_data["expected_sections"][:max_sub_queries]
```

#### Fix 3: 修复成本追踪
**文件**: `deep_research_agent/agents/writer.py`

```python
# 汇总所有调用的成本
total_input_tokens = sum(tokens_list)
total_output_tokens = sum(tokens_list)
```

---

### 中期优化 (3-5天)

#### Improvement 1: 重写Writer Agent
- 使用模板驱动的方式生成报告
- 添加章节去重逻辑
- 生成高质量的执行摘要

#### Improvement 2: 增强Critic Agent
- 增加更多评估维度
- 根据缺失章节动态调整分数
- 提供可执行的改进建议

#### Improvement 3: 内容去重
- 在Synthesis阶段添加相似度检测
- 合并重复内容

---

### 长期改进 (1-2周)

#### Feature 1: 结构化输出
- 使用Pydantic模型约束输出格式
- 添加JSON Schema验证

#### Feature 2: 人机协作
- 允许用户编辑生成的计划
- 支持迭代优化

---

## 测试计划

### 回归测试
1. 运行 `pytest tests/` - 确保单元测试通过
2. 运行完整pipeline 5次 - 验证稳定性
3. 检查生成的报告格式 - 人工审查

### 性能测试
1. 测试不同长度查询的处理时间
2. 测试成本估算准确性
3. 测试并发处理能力

---

## 附录：测试日志片段

### 测试1：Planner
```
✅ Plan generated!
   Strategy: To approach the research on MCP protocol...
   Sub-queries (6):
      - What is the MCP protocol and its purpose?
      - How does the MCP protocol work?
   Cost: $0.0166
```

### 测试2：Synthesis
```
✅ Synthesis complete!
   Sections: 8
   Section 1: 1. Introduction  ← 命名问题
   Content: Section Title: 1. Introduction  ← 冗余前缀
```

### 测试3：Writer
```
✅ Report generated: 102 chars  ← 内容过短
Cost: $0.0000  ← 成本追踪错误
```

---

## 结论

项目架构正确，核心流程已打通，但输出质量需要大幅提升。建议优先修复P0问题（格式、结构、重复），然后优化P1问题（成本、引用、Review）。预计需要3-5天完成主要修复。
