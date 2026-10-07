/*
  Where the squares go: blocks (a dataset, a group of the semantic layer) packed in rows, each block a label and its tiles in a rough square. A pure
  function of the blocks and the width, so the same tile can be given its place in one layout and then another, and glide between them.
*/
export const TILE = 14;
export const GAP = 3;
const STEP = TILE + GAP;
const LABEL = 30; // a block's label: its name and its count
const BETWEEN_X = 22; // after a labelled block
const BETWEEN_SMALL = 10; // after one with no label: the many small groups sit close
const HEADING = 28; // a section heading: a row of its own
const BETWEEN_Y = 18;
export const LABEL_MAX = 200; // px: a longer name is cut short (the line above the map reads it in full)
const CHAR = 6.3; // px a character of the label takes

export interface Block {
  key: string;
  name: string;
  /** the tiles in it */
  count: number;
  /** a block with no label (the many small groups) is just its tiles */
  labelled: boolean;
  /** a heading is not a block: it starts a new row, names the section that follows, and holds no tiles */
  heading?: boolean;
  /** the colour of the area it names */
  color?: string;
}
export interface Placed {
  block: Block;
  x: number;
  y: number;
  /** the width of the block's tiles, and how many fit across */
  cols: number;
  top: number;
}

/** Tiles across: roughly square, whatever the count, and never wider than the space. */
const across = (n: number, width: number) => Math.min(Math.max(2, Math.ceil(Math.sqrt(n * 1.8))), Math.max(1, Math.floor((width + GAP) / STEP)));

export function pack(blocks: Block[], width: number): { placed: Placed[]; height: number } {
  const placed: Placed[] = [];
  let x = 0;
  let y = 0;
  let rowHeight = 0;
  for (const block of blocks) {
    if (block.heading) {
      if (x > 0) y += rowHeight + BETWEEN_Y;
      else if (placed.length > 0) y += rowHeight;
      placed.push({ block, x: 0, y, cols: 0, top: 0 });
      y += HEADING;
      x = 0;
      rowHeight = 0;
      continue;
    }
    const cols = across(block.count, width);
    const rows = Math.ceil(block.count / cols);
    const tiles = cols * STEP - GAP;
    const label = block.labelled ? Math.min(LABEL_MAX, Math.ceil(block.name.length * CHAR)) : 0;
    const w = Math.min(width, Math.max(tiles, label));
    const top = block.labelled ? LABEL : 0;
    const h = top + rows * STEP - GAP;
    if (x > 0 && x + w > width) {
      x = 0;
      y += rowHeight + BETWEEN_Y;
      rowHeight = 0;
    }
    placed.push({ block, x, y, cols, top });
    x += w + (block.labelled ? BETWEEN_X : BETWEEN_SMALL);
    rowHeight = Math.max(rowHeight, h);
  }
  return { placed, height: y + rowHeight };
}

/** A tile's place: the block's corner, then its column and row in the block. */
export function tileAt(p: Placed, i: number): [number, number] {
  return [p.x + (i % p.cols) * STEP, p.y + p.top + Math.floor(i / p.cols) * STEP];
}
