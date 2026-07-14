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

Choose the lowest suitable route. Prefer Spark, 5.4, 5.5, and 5.6-Luna. Terra
is available on the automatic path only for unusually broad, tool-heavy work;
Sol is never automatic.

After choosing, emit exactly one concise Chinese status line before execution:

```text
[Route] 当前任务：常规开发｜模型：GPT-5.4｜推理：中等｜执行方式：委派 Agent
```

For direct work use `执行方式：当前会话`; for Terra or an approved Sol
escalation include `执行方式：自动委派` or `执行方式：用户批准后委派`. Do not
emit model slugs, English labels, internal scoring, or a long routing analysis.

Use these display names: `GPT-5.3 Spark`, `GPT-5.4`, `GPT-5.5`,
`GPT-5.6 Luna`, `GPT-5.6 Terra`, and `GPT-5.6 Sol`. Translate reasoning as
`低`, `中等`, `高`, `极高`, or `最高`.

| Route | Default model and effort | Use for | Action |
| --- | --- | --- | --- |
| L0 | Spark `low` or `medium` | Simple explanation, summary, lookup, small text edit, or read-only answer | Handle directly in the current Spark session |
| L1 | 5.4 `medium` | Clear, repeatable extraction, classification, transformation, or bounded text/image task | Delegate to `route-gpt54-medium` |
| L1+ | 5.6-Luna `low` or `medium` | Clear, repeatable work needing larger context, stronger structured output, or routine multimodal handling | Delegate to `route-luna` or `route-luna-medium` |
| L2 | 5.4 `medium` | Normal coding, debugging, tests, and bounded multi-file changes | Delegate to `route-gpt54-medium` |
| L2+ | 5.4 `high` or 5.5 `medium` | Difficult but well-scoped implementation or review | Delegate to `route-gpt54-high` or `route-gpt55-medium` |
| L3 | 5.5 `high` or `xhigh` | Ambiguous, broad, or high-value reasoning that is not yet a large tool-heavy execution | Delegate to `route-gpt55-high` |
| L4 | 5.6-Terra `xhigh` | Automatic only when at least two broad-execution signals are present | Delegate to `route-terra-xhigh` |
| L5 | 5.6-Sol `max` | Never automatic; only when the user explicitly requests Sol or approves a specific Sol escalation | Delegate to `route-sol-max` only after approval |

Reasoning effort is part of the route, not an afterthought. Use `low` for
deterministic work, `medium` for ordinary reasoning, `high` for difficult
analysis, `xhigh` only for unusually broad tool-heavy work, and `max` only for
the L5 escalation above. Do not raise effort just because the task is long.

Apply these overrides:

- Any image or other non-text input cannot use Spark; choose at least L1.
- Production, security, financial, permission, or irreversible changes do not automatically choose Terra or Sol; use GPT-5.5 high and surface the risk.
- An explicit user-selected model or reasoning effort always overrides this matrix.
- Choose L4 only when at least two of these are true: three or more independent
  modules/files, five or more expected tool actions, cross-service/runtime
  integration, or a context that cannot fit reliably in the 5.5/Luna handoff.
  A long conversation, urgency, or ambiguity alone is not evidence.
- Never infer permission to use Sol from a high-risk task. Ask for approval if
  Sol would materially help, and otherwise continue with GPT-5.5.
- If confidence is low, move up one route only within the automatic ladder; do
  not jump to Terra or Sol because of uncertainty.
- An explicit user model choice overrides automatic routing.
- Keep user-requested scope and permission policy unchanged when delegating.

Never delegate to `route-sol`, `route-sol-max`, or any Sol model based only on
your own assessment. The words "production", "security", "deploy", "urgent",
or "complex" do not constitute Sol approval.

## Delegate safely

For L1-L3, use the `spawn_agent` tool with the exact custom agent name. Pass a
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
