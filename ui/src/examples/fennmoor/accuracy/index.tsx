import { useEffect, useState } from "react";
import Part from "../../Part";
import { LIVE } from "../live";
import { TOTALS } from "../data";
import Costs from "./Costs";
import { n, type Accuracy } from "./data";
import Gain from "./Gain";
import Scores from "./Scores";
import Wall from "./Wall";

/*
  The accuracy section: the comparison of four methods on 186 questions, as measured (eval/comparison/, results/comparison.md). Each part is a claim in
  a sentence and the evidence under it; the caveats come with them, at the end, in the comparison's own words.
*/
export default function AccuracyBody() {
  const [d, setD] = useState<Accuracy | null>(null);
  // The data is the page's largest file (every query written), so it loads when the section does.
  useEffect(() => {
    let live = true;
    void import("./accuracy.json").then((m) => live && setD(m.default as unknown as Accuracy));
    return () => {
      live = false;
    };
  }, []);

  if (!d) return <div className="mt-8 h-[40rem] text-sm text-fg-muted">Loading the measurements…</div>;
  const schema = d.methods[0];
  return (
    <div>
      <Part live={LIVE.accuracy.scores} title="How often the answer is right" lead="Each question was written from a query the business really ran, so the right answer is known. Four methods answered them all, on the same model (Claude Sonnet 5.5): the only difference is what each is given.">
        <Scores d={d} />
      </Part>
      <Part summary="All 186 questions, four methods each: click one for the question, each answer and the query behind it." title="Every question, every method" lead="Each square is one question and its four corners are the four methods. Click one to read the question, each answer and the query behind it.">
        <Wall d={d} />
      </Part>
      <Part summary="Tokens and time a request costs, by method." title="What a request costs" lead="The schema in the prompt costs the same on every question, and an estate's schema grows with it. The layer's prompt is small.">
        <Costs d={d} />
        <p className="mt-6 max-w-3xl text-sm text-fg-muted">
          With prompt caching, the schema in the prompt is the cheapest way to a right answer (see the table). What the layer buys is accuracy, and the tokens,
          latency and context room that come with small prompts. This estate's {TOTALS.tables} tables take about {n(schema.log.tokens_p50)} tokens a request; an estate
          with thousands takes many times that.
        </p>
      </Part>
      <Part summary="The agent's exchanges, and the first answer each one got." title="Where the agent's gain comes from" lead="The agent's exchanges, and the first answer each one got.">
        <Gain d={d} />
      </Part>
      <Part summary="Five things that belong with the numbers on this page: the questions favour precedent, the agent's state is the best case, scoring is mechanical, one synthetic estate, and timings are measured under load." title="Before you quote these" lead="Read the numbers with these, which belong to them.">
        <ul className="mt-5 grid max-w-4xl list-disc gap-3 pl-5 text-sm leading-relaxed marker:text-fg-muted">
          <li>
            <strong className="font-medium">The questions favour precedent.</strong> They are written from the business's own queries, so about half are re-asks by
            construction. The query a question was written from is never offered to answer it, but a re-ask finds the same query through another of its texts in the
            log. In production, the share depends on the estate.
          </li>
          <li>
            <strong className="font-medium">The agent's state is the best case.</strong> It is written from the reference query, in the business's words, with no table,
            column, source or join named. A real agent knows less.
          </li>
          <li>
            <strong className="font-medium">Scoring is mechanical.</strong> An answer is right when it has the reference's rows and its compared columns hold the same
            values, whatever the columns are called. An answer that reads the question differently, such as one extra row, counts as wrong.
          </li>
          <li>
            <strong className="font-medium">One estate, and a synthetic one.</strong> Scores of the same method move a few points between runs. The agent accepts a wrong
            answer for {d.outcomes["accepted wrong"]} of {d.questions.length} questions.
          </li>
          <li>
            <strong className="font-medium">Timings are measured under load,</strong> six questions at a time and four methods at once.
          </li>
        </ul>
        <p className="mt-6 text-xs text-fg-muted">
          Measured by eval/comparison/run.py, every model call live; the totals are in results/comparison.md. All four methods are Claude Sonnet 5.5, and the naive
          methods have nothing of the semantic layer: no log, variables, joins, example queries or filter values.
        </p>
      </Part>
    </div>
  );
}

