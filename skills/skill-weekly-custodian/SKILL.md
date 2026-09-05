---
name: skill-weekly-custodian
description: 项目每周自检与资产保洁中枢。以 .agents/cd-weekly-log.md 为确定性审计线索，执行沉淀防腐核验、同类经验聚类、沙盒清理与移云提请，滚动清算台账并输出零通胀报告。
argument-hint: "[audit|clean|roll]"
disable-model-invocation: true
---

# skill-weekly-custodian: 每周自检与资产保洁中枢

作为全系统定期审计与环境保洁引擎，`skill-weekly-custodian` 负责周期性收敛工程技术债务，保障代码库长期高信噪比运行。

## 1. 触发与工作区中枢 (Trigger & Custodian Workspace)

* **交互入口**：统一通过 **`/zj`** 触发（口语：“每周自检”、“跑一下巡检”、“全局周检”）；
* **调度支持**：支持后台 Cron 周期性轻量唤醒（如每周日晚自动巡检）；
* **全局周巡检中枢工作区**：**`~/.agents/custodian/`**
  - **项目注册表**：`~/.agents/custodian/projects.md`（记录本机所有装载 Relay 的项目拓扑与周报物理路径）；
  - **周报归档库**：`~/.agents/custodian/reports/`（存放跨项目汇总的历次全局周检周报）。
* **核心输入源**：各项目的周报沉淀台账（如各项目下的 `.agents/cd-weekly-log.md`）。

---

## 2. 双模作业流 (Dual-Mode Operations)

### 模式 A：单项目就地周检 (Local Project Mode)
当在某个具体项目工作区中唤起 `/zj` 时：
1. 定点读取当前项目的 `.agents/cd-weekly-log.md` 执行四步审计闭环；
2. 刷新 `~/.agents/custodian/projects.md` 中当前项目的巡检时间与状态。

### 模式 B：全局中枢周检 (Global Cross-Project Mode)
当在全局中枢或发出“全局周检 / 跨项目巡检”时，依序执行五步闭环：

#### 步骤 1：项目发现与穿透寻址 (Project Discovery)
读取 `~/.agents/custodian/projects.md`，获取所有装载了 Relay 的项目清单与周报路径。若当前所在项目尚未登记，自动就地追加一行。

#### 步骤 2：逐项目定点审计周报 (Ledger-Driven Audit)
穿透到各个装载项目的台账（如 `项目/.agents/cd-weekly-log.md`）：
   * *若台账无待审条目*：跳至第三步继续常规保洁，保持零通胀。
2. **防腐化核验**：
   * **去日志膨胀**：跳转至落盘目标文件，核查是否存在终端完整报错或长篇输出；若有，当场脱水为【现象 - 根因 - 最小解法/单行命令】；
   * **正向语言核验**：核查新增内容是否保持纯正向陈述，消除防御性免责或反向辩白。

### 第二步：同类聚类与技能兼并 (Coalescence & Generalization)
1. **暗坑聚类**：扫描本周期多条同源、同模块的微小笔记，主动将其归纳合并为一条通用的系统级防坑准则；
2. **技能兼并**：检查是否存在职责高度重叠的“薄技能”，提请整合精简，降低认知负载。

### 第三步：仓库物理保洁与清晰索引维护 (Physical Housekeeping & Epoch Indexing)
1. **沙盒清理**：扫描 `scratch/` 目录，对于超过 7 天无修改且无外部引用的临时文件，提请清除；
2. **完结大资产云归档提请**：扫描代码库中已完结的大体积历史资产（如答辩 PPT、视频、大型静态结果集），提请打包迁移至 Google Drive 专属账号（`zhuangyan529898`），并在 `.agents/gdrive-cloud-archive.md` 中保留单行墓碑指针；
3. **长文档沉淀与清晰索引维护 (Epoch Indexing)**：当开发日志或计划文档超长需要沉淀归档时，**严禁粗暴截断**；必须在活跃文档头部固化维护【历代里程碑归档全景索引表】，登记纪元时间段、核心产物、检索词与云端指针，确保历史脉络一目了然。

### 第四步：清算台账与报告沉淀 (Ledger Roll & Report Generation)
1. **各项目台账清算**：将各项目已审计条目标记为 `[已归档]`，滚动重置活跃区；
2. **全局周报沉淀**：若执行全局巡检，在 `~/.agents/custodian/reports/YYYY-Wxx.md` 沉淀一份跨项目汇总报告，并更新 `projects.md` 中各项目的巡检时间与健康状态；
3. **零通胀汇报**：
   * **全库健康时（极简直报事实）**：
     > `[周检完成] 本周期所有装载项目台账已全部验真合规，已生成 ~/.agents/custodian/reports/2026-Wxx.md。`
   * **发现实质问题时（列出精准变更建议待确认）**：
     > `[周检建议]`  
     > `1. 跨项目聚类：提议将项目 A 与项目 B 的 2 条同类报错笔记归纳为全局通用规则；`  
     > `2. 移云提请：检测到项目 A 中 docs/data.csv (120MB)，提请移至 Google Drive 并留单行指针；`  
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
