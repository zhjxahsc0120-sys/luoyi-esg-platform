/// <reference lib="webworker" />

export {};

type ParseRequest = {
  type: "parse";
  url: string;
};

type MutableBatch = {
  color: string;
  width: number;
  positions: number[];
  indices: number[];
  lineCount: number;
};

const workerScope = self as unknown as DedicatedWorkerGlobalScope;

function valueOf(source: string, tag: string, fallback = "") {
  const match = source.match(
    new RegExp(`<${tag}(?:\\s[^>]*)?>([\\s\\S]*?)<\\/${tag}>`, "i"),
  );
  return match?.[1]?.trim() || fallback;
}

function parseCoordinates(
  source: string,
  batch: MutableBatch,
) {
  const tuples = source
    .trim()
    .split(/\s+/)
    .map((tuple) => tuple.split(",").map(Number))
    .filter(
      (tuple) =>
        tuple.length >= 2 &&
        Number.isFinite(tuple[0]) &&
        Number.isFinite(tuple[1]),
    );
  if (tuples.length < 2) return;

  const start = batch.positions.length / 3;
  for (const tuple of tuples) {
    batch.positions.push(tuple[0], tuple[1], tuple[2] || 0);
  }
  for (let index = 0; index < tuples.length - 1; index += 1) {
    batch.indices.push(start + index, start + index + 1);
  }
  batch.lineCount += 1;
}

async function parse(url: string) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`SPX KML 加载失败（HTTP ${response.status}）`);
  }
  const source = await response.text();
  const batches = new Map<string, MutableBatch>();
  const placemarkPattern = /<Placemark\b[\s\S]*?<\/Placemark>/gi;
  const coordinatePattern =
    /<LineString\b[\s\S]*?<coordinates(?:\s[^>]*)?>([\s\S]*?)<\/coordinates>[\s\S]*?<\/LineString>/gi;

  for (const placemark of source.matchAll(placemarkPattern)) {
    const block = placemark[0];
    const color = valueOf(block, "color", "ffffffff").toLowerCase();
    const parsedWidth = Number(valueOf(block, "width", "1"));
    const width = Number.isFinite(parsedWidth) ? parsedWidth : 1;
    const key = `${color}|${width}`;
    let batch = batches.get(key);
    if (!batch) {
      batch = { color, width, positions: [], indices: [], lineCount: 0 };
      batches.set(key, batch);
    }
    for (const coordinates of block.matchAll(coordinatePattern)) {
      parseCoordinates(coordinates[1], batch);
    }
  }

  const result = [...batches.values()].map((batch) => ({
    color: batch.color,
    width: batch.width,
    positions: new Float64Array(batch.positions),
    indices: new Uint32Array(batch.indices),
    lineCount: batch.lineCount,
  }));
  const transfers = result.flatMap((batch) => [
    batch.positions.buffer,
    batch.indices.buffer,
  ]);
  workerScope.postMessage(
    {
      type: "success",
      batches: result,
      placemarkCount: (source.match(/<Placemark(?:\s|>)/gi) || []).length,
    },
    transfers,
  );
}

workerScope.onmessage = (event: MessageEvent<ParseRequest>) => {
  if (event.data.type !== "parse") return;
  void parse(event.data.url).catch((error) => {
    workerScope.postMessage({
      type: "error",
      message: error instanceof Error ? error.message : "SPX KML 解析失败",
    });
  });
};
