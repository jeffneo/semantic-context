# The comparison: qlsc against naive approaches

Does the semantic layer earn its keep? Four methods answer the same 186 questions, scored on the answer's
rows against a reference, with the tokens and seconds each request costs.

| method | what it has |
|---|---|
| `naive-schema` | the warehouse's schema in the prompt (323 tables, columns, types): one query, one fix after a failed dry run |
| `naive-agent` | a generic tool-using agent over the same schema: `list_tables`, `describe_table`, `run_sql`, `submit` |
| `layer` | qlsc's compiled request, one shot, as the log evaluations score it |
| `agent` | qlsc as an AI agent uses it: the agent holds its business process's state, writes its request, checks each answer, corrects it; qlsc answers by its router, precedent first |

All four are Sonnet 5.5. The naive methods have nothing of the semantic layer: no log, Variables, joins,
Computations, example queries or filter values.

## Results

186 questions: the 10 scored gold questions (hand-written references) and the 176 log questions, each
written from a query the business ran, its result the reference. The log questions' own query is never
offered to answer them. Every LLM call live and measured (commit in `results/comparison.json`).

**176 log questions**

| method | right | delivered | tokens p50 / p90 | seconds p50 / p90 | $ per request | $ per right answer |
|---|---|---|---|---|---|---|
| naive-schema | 116 (66%) | 0 | 43,872 / 44,032 | 4.4 / 5.5 | 0.012 | 0.018 |
| naive-agent | 108 (61%) | 17 | 50,304 / 127,053 | 22.4 / 42.8 | 0.060 | 0.098 |
| layer | 132 (75%) | 132 | 6,667 / 9,804 | 4.4 / 8.2 | 0.017 | 0.023 |
| **agent** | **158 (90%)** | **153 (87%)** | 10,667 / 47,220 | 9.0 / 40.8 | 0.042 | 0.047 |

**10 gold questions:** naive-schema 3, naive-agent 6, layer 6, agent 9.

*Delivered* is right within the service's targets (`service.targets`: 20,000 tokens and 30 seconds per
request). *Tokens* count every input token, cache reads included, so a cached schema still counts in
full; dollars price the cache reads at a tenth.

### What it says

- **Accuracy is the gain.** On the business's own questions the layer answers 75% in one shot, against
  61% to 66% for the same model with only the schema. An agent that brings its process's context, and
  lets qlsc answer by precedent, reaches 90%.
- **Tokens and latency, against naive.** The schema in the prompt costs about 44,000 tokens a request;
  the generic agent about 50,000, and 127,000 at the 90th percentile, for 22 seconds and worse answers.
  The layer needs 6,700 tokens. Neither naive method delivers more than a handful of answers within the
  targets.
- **Dollars are a different story.** With prompt caching the naive schema is the cheapest per right
  answer (1.8 cents against 2.3 for the layer and 4.7 for the agent). What the layer buys is accuracy,
  and the tokens, latency and context window that come with small prompts: at 44,000 tokens a question
  the schema doesn't fit an estate with thousands of tables (this one has 323).
- **Precedent is most of the gain.** 89 of the agent's 186 first answers were a precedent: the
  business's own query for a request like this one, its values set from the question. 86 were right, at
  a median of 864 tokens and 3.5 seconds. The other 97 were compiled requests: 75 right, 10,307 tokens,
  8.6 seconds.
- **Novel questions.** For a question the business hasn't asked before, the agent's context lifts the
  compiled request. But the exchange costs more: tokens and seconds above are the whole exchange,
  corrections included, and the gold questions (novel, and harder) took a median 43,513 tokens and 47
  seconds.
- **Wrong answers accepted.** The agent accepts a wrong answer for 10 of 186 questions. An agent that
  checks an answer against its state catches most but not all errors.
- **The agent's failures aren't ours.** 65 right answers were rejected by the agent (over rounding,
  ordering and the like). qlsc delivered them; the agent ran the exchange on to its four-answer cap. They
  are most of the 90th-percentile tokens and seconds.

The agent's 186 exchanges: right at once 96; right after corrections 1; right, rejected by the agent 65;
right, past the targets 5; accepted wrong 10; never right 9.

### Caveats

- **The questions favour precedent.** They are written from the log's own queries, so about half are
  re-asks by construction. A question the business has asked before gets the precedent route; in
  production the share depends on the estate. The query a question was written from is excluded; a
  re-ask finds the same query through another of its texts in the log, run with other values.
- **The agent's state is written from the reference query,** in the business's words, with no table,
  column, source or join named. It is the best a process-aware agent could know; a real one knows less.
  On the probe set, a state that also said where the data comes from and how it is joined was worth
  about two fifths of the agent's gain (the plan, "Probe: states without source or join hints").
- **One estate, and a synthetic one.** Numbers move a few points between runs of the same method: the layer
  scored 132 of 176 and 6 of 10 gold in both of its full runs, but 7 of 10 gold on the probe set.
- **Latency is measured under parallel load,** six questions at a time, four methods at once.

## Reproducing it

```bash
uv run examples/fennmoor-bank/eval/comparison/run.py prep          # the references, the agent's states
uv run examples/fennmoor-bank/eval/comparison/run.py layer         # naive-schema | naive-agent | layer | agent
uv run examples/fennmoor-bank/eval/comparison/run.py report        # -> results/comparison.md, comparison.json
```

Needs the estate built (`qlsc build`, which includes `qlsc requests`), the answer keys (`eval/log_questions.py
write|run`) and a warehouse login. Each method takes `--workers=N`, `--only=Q01,L...` and `--fresh=TAG`. About
$25 and 15 minutes in all: the agent $8 (the agent's own calls $2), the generic agent $11, the layer $3, the
schema $2. Each method's LLM calls are cached in their own directory
(`<work>/llm_cache_comparison/<method>`): a run again replays them for free, and the report says so; add
`--fresh=TAG` to measure anew.

| file | what |
|---|---|
| `run.py` | the questions, the runner (parallel, measured with `qlsc/meter.py`), the report |
| `naive.py` | the two naive methods |
| `consumer.py` | the agent: its state, its request, its check of each answer, its corrections |
| `prompts/` | the comparison's prompts: the naive methods' and the agent's |

The earlier exploration that led here (each idea tested alone, on a probe set: model and reasoning swaps,
iterated graph context, confirmation loops, precedent variants) is in
[plans/2026-09-30-accuracy-orthogonal.md](../../../../plans/2026-09-30-accuracy-orthogonal.md); its code
is at commit `1578fa6`.
