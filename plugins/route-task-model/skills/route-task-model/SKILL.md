---
name: route-task-model
description: Automatically classify each new Codex task by scope, ambiguity, modality, risk, and reasoning depth, then handle work with Spark, GPT-5.4, GPT-5.5, GPT-5.6-Luna, and carefully gated GPT-5.6-Terra. GPT-5.6-Sol remains manual-only. Use when automatic model routing is enabled for a session.
---

# Route Task Model

Use the current Spark session as a lightweight router. Do not claim that the
main thread changed models: delegation to a model-pinned custom agent is the
supported behavior of this skill.

The user-level routing Hook keeps a local JSONL snapshot under
`~/.codex/route-context/`. Normally prefer the visible conversation because it
is richer and typed. After resume or compaction, inspect the newest relevant
snapshot only when visible context is incomplete; treat transcript fields as
best-effort because Codex may change the transcript format.

## Route before executing

For every new user task, classify the task before using tools or editing files.
Use the whole visible conversation as context, but do not copy the entire raw
transcript to a child agent.

Evaluate:

- clarity of the requested outcome and acceptance criteria;
- number of files, modules, repositories, or external systems involved;
- amount of multi-step reasoning, investigation, and verification required;
- requested modality (text, image, video, or other non-text input);
- side effects such as deployment, database writes, money, permissions, or production changes;
- security, privacy, compliance, or irreversible-operation risk;
- whether the user explicitly selected a model or asked to stay in the current session.

Use the aggressive profile by default: keep Spark for trivial work, but make
GPT-5.5 the normal route for implementation and tool use. Prefer Spark, 5.4,
5.5, and 5.6-Luna. Terra is available on the automatic path only for unusually
broad, tool-heavy work; Sol is never automatic.

After choosing, emit exactly one concise Chinese status line before execution:

```text
[Route] 当前任务：常规开发｜模型：GPT-5.5｜推理：中等｜执行方式：委派 Agent
```

For direct work use `执行方式：当前会话`; for Terra or an approved Sol
escalation include `执行方式：自动委派` or `执行方式：用户批准后委派`. Do not
emit model slugs, English labels, internal scoring, or a long routing analysis.

Use these display names: `GPT-5.3 Spark`, `GPT-5.4`, `GPT-5.5`,
`GPT-5.6 Luna`, `GPT-5.6 Terra`, and `GPT-5.6 Sol`. Translate reasoning as
`低`, `中等`, `高`, `极高`, or `最高`.

| Route | Default model and effort | Use for | Action |
| --- | --- | --- | --- |
| L0 | Spark `low` or `medium` | 仅限简单解释、摘要、查找、小文本修改和只读回答 | 在当前 Spark 会话直接处理 |
| L1 | 5.4 `medium` | 明确、可重复、范围很小的提取、分类、转换或单文件任务 | 委派给 `route-gpt54-medium` |
| L1+ | 5.6-Luna `low` 或 `medium` | 需要更大上下文、结构化输出或常规多模态处理的明确任务 | 委派给 `route-luna` 或 `route-luna-medium` |
| L2 | 5.5 `medium` | 默认用于任何编码、调试、测试、工具调用和多文件修改 | 委派给 `route-gpt55-medium` |
| L2+ | 5.5 `high` | 有歧义、边界条件多、需要多步验证的实现或审查 | 委派给 `route-gpt55-high` |
| L3 | 5.6-Luna `high` | 大型结构化、多模态或上下文密集型任务 | 委派给 `route-luna-high` |
| L4 | 5.6-Terra `xhigh` | 仅在同时满足至少两个大范围执行信号时自动使用 | 委派给 `route-terra-xhigh` |
| L5 | 5.6-Sol `max` | 永不自动使用；仅在用户明确请求或批准具体 Sol 升级后使用 | 获得批准后才委派给 `route-sol-max` |

Reasoning effort is part of the route, not an afterthought. Use `low` for
deterministic work, `medium` for ordinary reasoning (with GPT-5.5 as the
aggressive default for development), `high` for difficult analysis, `xhigh`
only for unusually broad tool-heavy work, and `max` only for the L5 escalation
above. Do not raise effort just because the task is long.

Apply these overrides:

- Any image or other non-text input cannot use Spark; choose at least L1, and
  use Luna when the task requires multimodal comparison or structured output.
- Production, security, financial, permission, or irreversible changes do not automatically choose Terra or Sol; use GPT-5.5 high and surface the risk.
- An explicit user-selected model or reasoning effort always overrides this matrix.
- Choose L4 only when at least two of these are true: three or more independent
  modules/files, five or more expected tool actions, cross-service/runtime
  integration, or a context that cannot fit reliably in the 5.5/Luna handoff.
  A long conversation, urgency, or ambiguity alone is not evidence.
- Never infer permission to use Sol from a high-risk task. Ask for approval if
  Sol would materially help, and otherwise continue with GPT-5.5.
- If confidence is low, move up one route only within the automatic ladder; do
  not jump to Terra or Sol because of uncertainty. For ordinary development,
  prefer GPT-5.5 over GPT-5.4 unless the task is clearly small and deterministic.
- An explicit user model choice overrides automatic routing.
- Keep user-requested scope and permission policy unchanged when delegating.

Never delegate to `route-sol`, `route-sol-max`, or any Sol model based only on
your own assessment. The words "production", "security", "deploy", "urgent",
or "complex" do not constitute Sol approval.

## Delegate safely

For L1-L4, use the `spawn_agent` tool with the exact custom agent name. Pass a
compact handoff containing:

```text
Task:
Goal:
Relevant context:
Constraints and decisions:
Files or systems in scope:
Acceptance checks:
Route and reason:
```

Include the original request and only the context needed to execute it. Redact
API keys, cookies, passwords, access tokens, and unrelated private transcript
content. The child agent owns execution and verification; wait for its result,
then report the result to the user in the main session.

If `spawn_agent` is unavailable, continue in the current session at the chosen
reasoning level and state the fallback internally; do not fabricate a model
switch or silently broaden the task.

## Keep routing concise

Do not make the user read a routing JSON object or a long classification
monologue. The single `[Route]` status line is required so the user can verify
that this skill ran and which model/effort was selected.

## Verify the handoff

Before returning the result, confirm that the delegated agent reported:

- what changed or what it found;
- which checks actually ran and their outcomes;
- unresolved risks, blockers, or follow-up work;
- whether the requested acceptance criteria were met.

Do not mark the task complete based only on a child agent's intention to run a
check; require its reported evidence.
