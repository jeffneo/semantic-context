/*
  The landing page's figures, as data, each with where it comes from in the repository. Everything here is measured on one synthetic
  bank estate (324 tables) by qlsc's own evaluations; none of it is a customer result. Change a figure here, never in a component.
*/

export interface Proof {
  /** the status quo problem this answers, in the customer's words */
  problem: string;
  /** the headline figure */
  figure: string;
  unit: string;
  /** what it is measured against */
  versus: string;
  /** the repository file the number comes from */
  source: string;
}

export const PROOF: Proof[] = [
  {
    problem: "Answers that look right",
    figure: "90%",
    unit: "right",
    versus:
      "of 176 of the business's own questions when an agent uses the layer, against 61 to 66% for the same model given only the schema.",
    source: "results/comparison.md",
  },
  {
    problem: "Context that doesn't scale",
    figure: "6.7k",
    unit: "tokens a question",
    versus: "against about 44k for the schema in the prompt (medians), a gap that grows with the estate.",
    source: "results/comparison.md",
  },
  {
    problem: "Re-reading the warehouse",
    figure: "0.05s",
    unit: "a repeat read",
    versus: "from memory, against 0.7 s for the query; a 50-question session bills 605 MiB, not 2,128.",
    source: "results/economics.md",
  },
  {
    problem: "Agents that see too much",
    figure: "0",
    unit: "row incidents",
    versus:
      "across 3 principals and 60 questions, with the warehouse as the oracle; forged, expired and missing tokens were refused.",
    source: "results/entitlements.md",
  },
];

export const CAVEAT =
  "One synthetic bank estate. Figures are from qlsc's own evaluations in this repository, not a customer's. Half the questions are re-asks by construction, and in dollars a cached schema prompt is the cheapest per right answer.";

export interface Step {
  n: string;
  title: string;
  text: string;
}

export const STEPS: Step[] = [
  {
    n: "1",
    title: "Find context",
    text: "Walk the semantic layer from the question to a handful of tables, their joins, and the business's own queries that look like it.",
  },
  {
    n: "2",
    title: "Route",
    text: "Memory first, then a precedent, a compiled request, Cypher, free SQL: the cheapest trustworthy route that fits.",
  },
  {
    n: "3",
    title: "Compile",
    text: "The model fills in a typed request. Code writes the joins, filters and aggregation, and never multiplies rows.",
  },
  {
    n: "4",
    title: "Run as the person",
    text: "The warehouse enforces tables, columns and rows. A request reaches the graph only with a token signed for that principal.",
  },
];
