# 编写 OmniAI Edu 项目说明 Word 文档 Spec

## Why
用户希望把仓库中的 OmniAI Edu 项目，按照其提供的「图纸审核智能体系统」格式模板，编写一份与之结构对齐、内容贴合本项目的功能说明文档，并输出为 Word 文档保存在仓库中。该文档用于对外/对内说明系统能力，不修改仓库任何代码。

## What Changes
- 在仓库根目录生成一份 Word 文档 `OmniAI_Edu_功能清单.docx`，内容依据项目实际能力（OmniAI Edu：学知识、看效果、动手做、得反馈 + OpenMAIC 智慧课堂 + 统一 API 管理）编写。
- 严格沿用用户提供的格式模板结构：标题 + 功能清单 + 版本日期 + 概述段 + 七个一级章节，章节用「一、二、三…」编号，每章以「•」列表陈述能力。
- 版本日期使用 2026-06-30（与模板一致）。
- 不改动仓库中任何代码、配置、依赖文件；仅新增一个 .docx 文档。

## Impact
- Affected specs: 无（本仓库为普通项目，无既有 spec）
- Affected code: 不影响任何代码；仅新增 `OmniAI_Edu_功能清单.docx` 一个产物文件。
- 依据来源：`README.md`、`README_EN.md`、前端组件 `frontend/src/components/`、后端服务目录 `backend/`。

## ADDED Requirements
### Requirement: 按模板格式生成项目功能说明 Word 文档
系统 SHALL 在仓库根目录生成 `OmniAI_Edu_功能清单.docx`，内容描述 OmniAI Edu 平台能力，结构对齐用户提供的模板。

#### Scenario: 文档结构对齐模板
- **WHEN** 打开生成的 .docx
- **THEN** 文档包含：一级标题「OmniAI Edu — AI 通识教育一站式实践平台」、二级标题「功能清单」、版本日期行、一段概述、以及七节用「一、二、三…」编号的章节，每节以「•」项目符号列出能力点

#### Scenario: 内容贴合本项目实际能力
- **WHEN** 阅读各章节
- **THEN** 章节覆盖：系统定位、平台底座、学知识（知识路线图）、看效果（手写数字识别与 CNN 可视化）、动手做（AI 出题/判分/错题本）、得反馈（五维能力/学习报告/排行榜/智能助教师小助）、智慧课堂（OpenMAIC）与统一 API 管理

#### Scenario: 不修改仓库代码
- **WHEN** 文档生成完成
- **THEN** 仓库中除新增的 `OmniAI_Edu_功能清单.docx` 外，无任何源码、配置或依赖文件被改动

#### Scenario: 排版专业可用
- **WHEN** 在 Word/WPS/LibreOffice 中打开
- **THEN** 标题层级清晰、正文使用项目符号列表、中文字体正确显示、段落间距合理，可直接用于技术评审与归档
