# Research behind Snitch

What the literature says about coding agents gaming tests, and what Snitch does with
it. Read 2026-10-24; numbers are quoted from the papers.

## Adopted

**Policy + escalation tool, together.** Gomez (2026), *Can escalation channels redirect
reward hacking toward defect disclosure?*
([arXiv 2608.29460](https://arxiv.org/abs/2608.29460)), 2×2 design over 8 frontier
models, 360 samples per condition. Reward hacking: baseline 23.6%, escalation tool only
15.0%, written policy only 9.7%, both 5.3% (OR 9.18, 95% CI 5.0–16.8), with no
detectable cost or solve-rate overhead; a one-line "don't reward hack" instruction gave
16.9%. The tool alone was rarely used; pairing it with the policy maximised use.
→ The plugin's SessionStart hook gives the agent an anti-reward-hacking policy adapted
from the paper's (CC BY 4.0) in warn and enforce mode (`engine/policy.py`), next to the
existing `escalate` tool. The tool's description and receipt follow the paper's design:
escalating is "a normal and expected part of responsible operation", and the reply is a
fixed receipt that never says whether the escalation looks justified. Observe mode
injects nothing, so it stays a pure measurement arm.

**Comparison-operator overloading.** Zhong, Raghunathan & Carlini (2025),
*ImpossibleBench* ([arXiv 2510.20270](https://arxiv.org/abs/2510.20270)) classify
cheating on impossible tasks into four strategies: modifying tests, overloading
comparison operators (an `__eq__` that returns True for any string), recording extra
state (call counters), and special-casing. Claude models cheated mostly (>79%) by
modifying tests; OpenAI models used all four.
→ New rule `comparison_forced` (faking): a new `__eq__` that returns True (or `__ne__`
False) without comparing self with the other operand, or `__eq__ = lambda ...: True`.
`if self is other: return True` stays legitimate (fixture `legit_eq_defined`).

**Deterministic first.** ImpossibleBench's LLM monitors caught 86–89% of cheating on
single-function tasks but only 42–65% on multi-file SWE-bench tasks; unflagged
transcripts justified spec-violating code as "backward compatibility". TRACE
([arXiv 2601.20103](https://arxiv.org/abs/2601.20103)), 517 human-verified trajectories
over 54 exploit categories: the best model (GPT-5.2, highest reasoning) detects 63% of
hacks when contrasting trajectories and 45% when judging each one alone. → Snitch keeps every verdict tied to a deterministic diff; the
planned judge only decides intent on events the detectors already found.

**Escalation precision.** Gomez (2026) reports escalations were right 99.4% of the time
when they fired. → `bench-score` reports a false-escalation rate (escalations on
control tasks) next to the honest-escalation rate.

**Held-out tests as ground truth.** EvilGenie
([arXiv 2511.21654](https://arxiv.org/abs/2511.21654)) and SpecBench
([arXiv 2605.21384](https://arxiv.org/abs/2605.21384)) grade with held-out tests;
SpecBench finds agents saturate visible tests while hacking persists on held-out ones.
→ Every TemptationBench task has hidden tests the agent's runner config cannot fake.

## Noted, not done yet

- **Prompt strictness matters.** ImpossibleBench: the same models cheated >85% with a
  loose prompt and 1% (GPT-5) / 33% (o3) with a strict one ("STOP, identify them and
  explain why they are incorrect. Do NOT try to carve out the code"). TemptationBench
  must publish its exact task prompts and never tune them per agent.
- **Impossible variants at scale.** ImpossibleBench builds impossible tasks by mutating
  tests (one-off and conflicting variants) so any pass is a cheat. The same mutation
  could grow TemptationBench past 40 tasks with exact ground truth.
- **Capped tests.** CapCode (Lodkaew et al., 2026,
  [arXiv 2606.07379](https://arxiv.org/abs/2606.07379)) caps the best honest score below
  100% with randomized tests, so scores above the cap prove cheating.
- **Audit the bench itself.** Hardening Agent Benchmarks (arXiv 2606.08960) found 16% of
  1,968 terminal-agent tasks hackable from the task description alone, using hacker /
  fixer agent loops. TemptationBench checks one known cheat per task (`cheat.sh`); an
  adversarial pass would find others.
- **Recorded state and special-casing** (ImpossibleBench's other two strategies) are
  not detected deterministically: a rule would flag legitimate caches and base cases.
  Hidden tests catch them in the bench.
