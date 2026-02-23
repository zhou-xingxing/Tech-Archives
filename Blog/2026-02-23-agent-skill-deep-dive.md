# 让 AI Agent 真正“会干活”: Agent skills 深度解析

## Agent skills 是什么

Agent Skills is an open format maintained by Anthropic

Skills are folders of instructions, scripts, and resources that agents can discover and use to perform better at specific tasks. Write once, use everywhere.

 Agent Skills: organized folders of instructions, scripts, and resources that agents can discover and load dynamically to perform better at specific tasks.
 Skills extend Claude’s capabilities by packaging your expertise into composable resources for Claude, transforming general-purpose agents into specialized agents that fit your needs.
 Building a skill for an agent is like putting together an onboarding guide for a new hire.

 随着这些智能体变得更加强大，我们需要更具可组合性、可扩展性和可移植性的方式来为它们配备特定领域的专业知识

 ```
my-skill/
├── SKILL.md          # Required: instructions + metadata
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
└── assets/           # Optional: templates, resources
 ```

### Agent skills 是如何工作的
简单来说，技能是一个包含SKILL.md file的目录。该文件必须以包含一些必填元数据的YAML前置内容开头：name和description。启动时，智能体会将每个已安装技能的name和description预加载到其系统提示中。
这些元数据是渐进式披露的第一级：它提供了足够的信息，让Claude知道何时应该使用每个技能，而无需将所有内容加载到上下文中。

此文件的实际内容是详细信息的第二级。如果Claude认为该技能与当前任务相关，它会通过将其完整的SKILL.md读入上下文来加载该技能。
![SKILL.md](image.png)

随着技能的复杂度不断提升，它们可能包含过多内容，无法放入单个SKILL.md文件中，或者有些内容仅与特定场景相关。在这种情况下，技能可以在技能目录中捆绑附加文件，并在SKILL.md中通过名称引用这些文件。这些附加的链接文件属于第三级（及更高级别）的详细信息，Claude可以根据需要选择浏览和发现它们。

三种 Skill 内容类型，三个加载级别
Skills 可以包含三种类型的内容，每种在不同时间加载：

级别 1：元数据（始终加载）
内容类型：指令。Skill 的 YAML 前置信息提供发现信息：

---
name: pdf-processing
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
---
Claude 在启动时加载此元数据并将其包含在系统提示中。这种轻量级方法意味着您可以安装许多 Skills 而不会产生上下文开销；Claude 只知道每个 Skill 的存在及其使用时机。

级别 2：指令（触发时加载）
内容类型：指令。SKILL.md 的主体包含程序性知识：工作流程、最佳实践和指导：

# PDF Processing

## Quick start

Use pdfplumber to extract text from PDFs:

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

For advanced form filling, see [FORMS.md](FORMS.md).
当您的请求与某个 Skill 的描述匹配时，Claude 通过 bash 从文件系统读取 SKILL.md。只有在此时，这些内容才会进入上下文窗口。

级别 3：资源和代码（按需加载）
内容类型：指令、代码和资源。Skills 可以捆绑额外的材料：

pdf-skill/
├── SKILL.md (main instructions)
├── FORMS.md (form-filling guide)
├── REFERENCE.md (detailed API reference)
└── scripts/
    └── fill_form.py (utility script)
指令：额外的 markdown 文件（FORMS.md、REFERENCE.md），包含专门的指导和工作流程

代码：可执行脚本（fill_form.py、validate.py），Claude 通过 bash 运行；脚本提供确定性操作而不消耗上下文

资源：参考材料，如数据库模式、API 文档、模板或示例

Claude 仅在被引用时才访问这些文件。文件系统模型意味着每种内容类型都有不同的优势：指令用于灵活指导，代码用于可靠性，资源用于事实查询。

级别	加载时机	Token 开销	内容
级别 1：元数据	始终（启动时）	每个 Skill 约 100 tokens	YAML 前置信息中的 name 和 description
级别 2：指令	Skill 被触发时	5k tokens 以内	SKILL.md 主体，包含指令和指导
级别 3+：资源	按需	实际上无限制	通过 bash 执行的捆绑文件，无需将内容加载到上下文中
渐进式披露确保在任何给定时间只有相关内容占用上下文窗口。

### 渐进式披露的优势
按需文件访问：Claude 只读取每个特定任务所需的文件。一个 Skill 可以包含数十个参考文件，但如果您的任务只需要销售模式，Claude 只加载那一个文件。其余文件保留在文件系统上，消耗零 tokens。

高效脚本执行：当 Claude 运行 validate_form.py 时，脚本的代码永远不会加载到上下文窗口中。只有脚本的输出（如"验证通过"或特定错误消息）消耗 tokens。这使得脚本比让 Claude 即时生成等效代码要高效得多。

捆绑内容无实际限制：因为文件在被访问之前不消耗上下文，Skills 可以包含全面的 API 文档、大型数据集、大量示例或您需要的任何参考材料。未使用的捆绑内容不会产生上下文开销。

这种基于文件系统的模型使渐进式披露得以实现。

大型语言模型在许多任务上表现出色，但某些操作更适合用传统代码执行。当然也可以现场让 LLM 生成一段代码，但是除了效率问题，许多应用还需要只有代码才能提供的确定性可靠性。工作流程是一致且可重复的。

#### VS MCP

## 谨慎使用别人的 Agent skills
### 一些skills攻击方式

### 注意防范
识别恶意的 skills
从可信来源安装技能；使用前务必进行彻底审核。首先阅读技能中捆绑文件的内容，以了解其功能，尤其要注意代码依赖项以及图像或脚本等捆绑资源。同样，要留意技能中指示Claude连接到潜在不可信外部网络源的指令或代码。

所有发布到ClawHub的技能现在都使用VirusTotal的威胁情报进行扫描，VirusTotal基于大语言模型的代码洞察（由Gemini提供支持）会对整个技能包进行以安全为重点的分析，分析从SKILL.md开始，包括所有引用的脚本或资源。它不仅关注该技能声称能做什么，还会从安全角度总结代码实际的功能：是否下载并执行外部代码、访问敏感数据、执行网络操作，或者嵌入可能迫使智能体做出不安全行为的指令。

一方面，我们看到许多技能被标记为危险，因为它们包含不良的安全实践或明显的漏洞：不安全的API使用、不安全的命令执行、硬编码的密钥、过度的权限，或者对用户输入的草率处理。这在“氛围编程”时代越来越常见，在这个时代，代码生成迅速，往往没有真正的安全模型，就直接发布到生产环境中。
但更令人担忧的是第二类：那些明显且有意带有恶意的技能。它们被包装成合法工具，但其真正目的是执行诸如敏感数据窃取、通过后门进行远程控制或在主机系统上直接安装恶意软件等操作。

https://blog.virustotal.com/2026/02/from-automation-to-infection-how.html


## Agent skills 编写最佳实践




【参考】
1. https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills
2. https://agentskills.io/what-are-skills
3. https://platform.claude.com/docs/zh-CN/agents-and-tools/agent-skills/best-practices
