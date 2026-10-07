/*
  Row-level security, passed through, as the page draws it (written by examples/fennmoor-bank/generate/ui_security.py from the entitlement evaluation's own
  results and the allowlists the warehouse produced). The warehouse is the rulebook: the gateway asks it what each principal may read and never
  re-implements a rule, and the pass-through makes Cypher over the Virtual Graph run as that principal too.
*/
export interface Principal {
  name: string;
  /** what the test principal stands for, as the example sets it up in the warehouse */
  rule: string;
  readable: string[];
  /** columns of readable tables hidden by a policy tag */
  hidden: [table: string, column: string][];
  tagged: number;
  /** tables a row access policy filters */
  rowFiltered: string[];
  /** strings the check looked for in everything the gateway told them, which must not name what they cannot read */
  canaries: number;
}
export interface Side {
  query?: string;
  total?: number;
  columns?: string[];
  rows?: [string | null, number][];
  declined?: string;
  why?: string;
}
export interface Case {
  id: string;
  text: string;
  as: Record<string, { cypher: Side; sql: Side }>;
}
export interface Security {
  principals: Principal[];
  cases: Case[];
  driver: { name: string; refused: boolean; why: string }[];
  evaluation: {
    principal: string;
    questions: number;
    schemaLeaks: number;
    rowIncidents: number;
    sqlAnswered: number;
    cypherAnswered: number;
    routedToCypher: number;
    oracleAgrees: boolean;
  }[];
  controls: { name: string; principals: string[]; caught: boolean; by: string }[];
}

export const n = (x: number) => x.toLocaleString("en-US");
