---
name: skill-weekly-custodian
description: 项目每周自检与资产保洁中枢。以 ~/.agents/custodian/cd-weekly-log.md 为确定性审计线索，执行沉淀防腐核验、同类经验聚类、沙盒清理与移云提请，滚动清算台账并输出零通胀报告。
argument-hint: "[audit|clean|roll]"
disable-model-invocation: true
---

# skill-weekly-custodian: 每周自检与资产保洁中枢

作为全系统定期审计与环境保洁引擎，`skill-weekly-custodian` 负责周期性收敛工程技术债务，保障代码库长期高信噪比运行。

## 运行时边界

当前仓库提供的确定性 CLI 包含 `init`、`audit`、`sweep` 与 `version`；其中 `sweep` 会读取 `~/.agents/custodian/projects.json` 并生成报告。本技能描述的 `/zj`、知识聚类、归档提请和 Cron 调度仍属于宿主 AI 的协作流程，不应视为已部署的后台服务。

## 1. 触发与工作区中枢 (Trigger & Custodian Workspace)

* **交互入口**：统一通过 **`/zj`** 触发（口语：“每周自检”、“跑一下巡检”、“全局周检”）；
* **调度支持**：可由用户自行配置 Cron/任务计划程序调用 `relay.py sweep`；仓库不安装后台任务，也不在无授权时创建系统调度。
* **全局周巡检中枢工作区**：**`~/.agents/custodian/`**
  - **项目注册表**：`~/.agents/custodian/projects.json`（CLI 的机器可读权威记录）；`projects.md` 作为人工阅读索引；
  - **全机周总账**：**`~/.agents/custodian/cd-weekly-log.md`**（汇集全机各项目本周待审流水的唯一中央台账）；
  - **周报归档库**：`~/.agents/custodian/reports/`（存放跨项目汇总的历次全局周检周报）。
* **核心输入源**：全机统一周期沉淀总账 `~/.agents/custodian/cd-weekly-log.md`。

---

## 2. 双模作业流 (Dual-Mode Operations)

### 模式 A：单项目就地周检 (Local Project Mode)
当在某个具体项目工作区中唤起 `/zj` 时：
1. **就地保洁**：扫描当前项目 `scratch/` 临时草稿，提请清理废弃文件；
2. **大资产移云**：提请将已完结的大文件迁出网盘，并在 `.agents/cloud-archive.md` 留指针；
3. **资产完整性体检**：执行 `relay.py audit .` 快速核验当前项目必要顶层资产；
4. **刷新状态**：更新 `~/.agents/custodian/projects.json` 中当前项目的巡检时间与状态。

### 模式 B：全局中枢周检 (Global Cross-Project Mode)
> 💡 **工作区要求**：执行全机跨项目全局总巡检时，**必须在 IDE（Cursor / VSCode / Claude）中将 `~/.agents/` 打开为独立工作区**！只有在此工作区下，AI 才具备全机总管视角与跨项目穿透审计权限。

当在全局中枢工作区发出“全局周检 / 跨项目巡检”时，依序执行五步闭环：

#### 步骤一：项目发现与穿透寻址 (Project Discovery)
读取 `~/.agents/custodian/projects.json`，获取全机所有登记项目清单与活跃状态。若某项目路径已不存在，标记为【路径失效/待核实】安全跳过。

#### 步骤二：定点审计全机周总账 (Central Ledger Audit)
打开全机唯一总账 **`~/.agents/custodian/cd-weekly-log.md`** 的【本周全机待审流水】表格：
1. **逐行核查物理落盘**：依据表格中的【项目物理路径】与【物理落盘位置】，跳转至目标文件核验：
   - 是否真正落实到位；
   - 是否保持极简脱水（无控制台大段日志污染）；
   - 是否严格遵循正向陈述（无反向免责）；
2. *若本周全机待审流水为空*：直接推进至常规物理保洁，保持零通胀。

#### 步骤三：同类经验聚类与技能兼并 (Coalescence & Generalization)
1. **跨项目暗坑聚类**：在全局流水表中横向比对，若发现不同项目攻克了同源、同模块的技术暗坑，主动提炼为全机通用的系统级防坑准则；
2. **全局技能晋升提请**：若某项目沉淀的本地领域技能（`.agents/skills/`）对全机其他工程具有普适价值，主动提请晋升至全局 `~/.agents/skills/`。

#### 步骤四：仓库物理保洁与纪元索引维护 (Physical Housekeeping & Epoch Indexing)
1. **沙盒清理**：扫描各项目 `scratch/` 目录，清理过期草稿；
2. **完结大资产云归档提请**：扫描代码库中已完结的大体积历史资产，提请打包迁移至外部网盘/NAS，并在本地 `.agents/cloud-archive.md` 保留单行检索指针；
3. **长文档纪元索引维护**：超长文档迁出归档时，必须在活跃文档头部维护【历史纪元归档索引表】，严禁粗暴截断。

#### 步骤五：全局台账清算与零通胀汇报 (Ledger Roll & Zero-Inflation Reporting)
1. **全局总账清算**：将 `~/.agents/custodian/cd-weekly-log.md` 中已审计通过的条目清算并归入 `~/.agents/custodian/reports/YYYY-Wxx.md`，重置全局活跃区；
2. **运行确定性扫盘**：调用 `relay.py sweep` 更新各项目最新健康状态；
3. **零通胀汇报**：
   * **全库健康时（极简直报事实）**：
     > `[周检完成] 本周期所有装载项目台账已全部验真合规，已生成 ~/.agents/custodian/reports/2026-Wxx.md。`
   * **发现实质问题时（列出精准变更建议待确认）**：
     > `[周检建议]`  
     > `1. 跨项目聚类：提议将项目 A 与项目 B 的 2 条同类报错笔记归纳为全局通用规则；`  
     > `2. 移云提请：检测到项目 A 中 docs/data.csv (120MB)，提请移至外部存储并留单行指针；`
     > `请确认是否一键执行？`

---

## 3. `.agents/cd-weekly-log.md` 模板与自愈机制

当 `/cd` 或 `/zj` 发现当前项目尚未建立 `.agents/cd-weekly-log.md` 时，按以下规范自动就地初始化：

```markdown
# 周期沉淀与自检台账 (Weekly Distillation Ledger)

> 维护机制：`/cd` 执行时自动追加待审行；`/zj` 周检定点审计后清算归档。
> 尺寸准则：按审计周期自然滚动，完成即清算，杜绝碎片膨胀。

## 本周期待审 (Active Cycle)

| 日期 | 资产类别 | 核心要点 (脱水摘要) | 落盘目标容器 | 验真与状态 |
| :--- | :--- | :--- | :--- | :--- |

## 历史结项记录 (Archived)
```
