import type { Preset } from "./types";

/** A query file as a panel opens with it: its comment header stays (it says what the query is for), but not the line naming the database, which the panel's header says. */
export const preset = (label: string, raw: string): Preset => ({ label, query: raw.replace(/^\/\/ Database:.*\n/, "").trimEnd() + "\n" });
