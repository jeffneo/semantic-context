/** The project's repository: the header links to it, and each section to the code that does its work. */
export const REPO = "https://github.com/jeffneo/semantic-context";

/** One reference to the code: a file, or a line in it. */
export interface CodeLink {
  label: string;
  path: string;
  line?: number;
}

/** A link to a file at a commit (not to a branch, whose lines move). tests/test_code_links.py checks each against that commit. */
export const codeUrl = (commit: string, l: CodeLink) => `${REPO}/blob/${commit}/${l.path}${l.line ? `#L${l.line}` : ""}`;
