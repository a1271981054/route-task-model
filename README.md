# Route Task Model

一个可分发的 Codex 插件，用 Spark 判断任务难度，再把任务路由到合适的模型。

自动路径：

```text
GPT-5.3 Spark → GPT-5.4 → GPT-5.5 → GPT-5.6 Luna → GPT-5.6 Terra
```

Terra 只用于同时满足多个“大范围、工具密集型”信号的任务；GPT-5.6 Sol 永远不会自动选择，必须由用户明确请求或批准。

## 安装

从 GitHub 克隆后，在仓库根目录执行：

```bash
python3 plugins/route-task-model/scripts/install_agents.py
```

然后重启 Codex，并在 `/hooks` 中审核并信任插件 Hook。新任务开始时会显示中文路由状态，例如：

```text
[Route] 当前任务：常规开发｜模型：GPT-5.4｜推理：中等｜执行方式：委派 Agent
```

路由快照保存在 `~/.codex/route-context/`，最近一次记录是 `latest.json`。

## 目录

- `plugins/route-task-model/skills/route-task-model/SKILL.md`：路由规则
- `plugins/route-task-model/agents/`：模型和推理等级绑定的 Agent
- `plugins/route-task-model/hooks/`：会话快照和每轮路由提示
- `.agents/plugins/marketplace.json`：仓库级插件市场清单
