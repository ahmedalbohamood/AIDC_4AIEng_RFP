const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, PageOrientation,
} = require("docx");

const data = JSON.parse(fs.readFileSync("/tmp/docx_data.json", "utf8"));

const PAGE_W = 12240, PAGE_H = 15840; // US Letter, DXA

const VERDICT_COLOR = {
  correct: "C6EFCE", partial: "FFEB9C", wrong: "FFC7CE", missing: "D9D9D9",
};
const VERDICT_LABEL = {
  correct: "Correct", partial: "Partial", wrong: "Wrong", missing: "No answer",
};

function cell(children, { width, shade, bold, header } = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shade ? { type: ShadingType.CLEAR, fill: shade } : undefined,
    children: Array.isArray(children) ? children : [
      new Paragraph({
        children: [new TextRun({ text: String(children), bold: !!bold })],
      }),
    ],
  });
}

function heading(text, level) {
  return new Paragraph({ text, heading: level, spacing: { before: 280, after: 140 } });
}

function para(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, ...opts })],
    spacing: { after: 120 },
  });
}

function hr() {
  return new Paragraph({
    text: "",
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "999999" } },
    spacing: { after: 200 },
  });
}

// ---------- Section: the 17 questions -----------------------------------
const qHeaderRow = new TableRow({
  tableHeader: true,
  children: [
    cell("#", { width: 500, shade: "D9D9D9", bold: true }),
    cell("Field", { width: 2600, shade: "D9D9D9", bold: true }),
    cell("Type", { width: 1000, shade: "D9D9D9", bold: true }),
    cell("Difficulty", { width: 1100, shade: "D9D9D9", bold: true }),
    cell("What we asked for", { width: 4200, shade: "D9D9D9", bold: true }),
  ],
});
const diffShade = { easy: "E2EFDA", medium: "FFF2CC", hard: "FCE4D6" };
const qRows = data.rows.map(r => new TableRow({
  children: [
    cell(String(r.number), { width: 500 }),
    cell(r.label, { width: 2600 }),
    cell(r.type, { width: 1000 }),
    cell(r.difficulty, { width: 1100, shade: diffShade[r.difficulty] }),
    cell(r.guidance, { width: 4200 }),
  ],
}));
const questionsTable = new Table({
  width: { size: 9400, type: WidthType.DXA },
  columnWidths: [500, 2600, 1000, 1100, 4200],
  rows: [qHeaderRow, ...qRows],
});

// ---------- Section: grounding summary across all 6 docs ----------------
function groundingTable() {
  const g = data.summary.overall_grounding;
  const header = new TableRow({
    tableHeader: true,
    children: ["Model", "Docs", "Present", "Absent", "Groundedness", "Hallucination", "Cost (USD)", "Sec / doc"]
      .map((t, i) => cell(t, { width: [2400, 900, 1100, 1000, 1400, 1400, 1200, 1000][i], shade: "D9D9D9", bold: true })),
  });
  const rows = Object.entries(g).map(([name, v]) => new TableRow({
    children: [
      cell(name, { width: 2400, bold: true }),
      cell(String(v.docs), { width: 900 }),
      cell(String(v.present), { width: 1100 }),
      cell(String(v.absent), { width: 1000 }),
      cell(v.grounded.toFixed(3), { width: 1400, shade: "C6EFCE" }),
      cell(v.halluc.toFixed(3), { width: 1400, shade: "C6EFCE" }),
      cell(v.cost === 0 ? "$0.00 (local)" : `$${v.cost.toFixed(3)}`, { width: 1200 }),
      cell(v.sec_doc.toFixed(1), { width: 1000 }),
    ],
  }));
  return new Table({
    width: { size: 10400, type: WidthType.DXA },
    columnWidths: [2400, 900, 1100, 1000, 1400, 1400, 1200, 1000],
    rows: [header, ...rows],
  });
}

// ---------- Section: accuracy summary ------------------------------------
function accuracyTable() {
  const a = data.summary.accuracy;
  const header = new TableRow({
    tableHeader: true,
    children: ["Model", "Accuracy vs. ground truth"].map((t, i) =>
      cell(t, { width: [3000, 3000][i], shade: "D9D9D9", bold: true })),
  });
  const rows = Object.entries(a).map(([name, pct]) => new TableRow({
    children: [
      cell(name, { width: 3000, bold: true }),
      cell(`${pct.toFixed(1)}%`, { width: 3000, shade: pct >= 65 ? "C6EFCE" : pct >= 55 ? "FFEB9C" : "FFC7CE" }),
    ],
  }));
  return new Table({
    width: { size: 6000, type: WidthType.DXA },
    columnWidths: [3000, 3000],
    rows: [header, ...rows],
  });
}

// ---------- Section: per-field detail -------------------------------------
const MODEL_LABEL = {
  "gpt-4o-text": "GPT-4o (text)",
  "llama-70b-text": "Llama-3.3-70B AWQ (text, local)",
  "qwen3-vl-32b-vision": "Qwen3-VL-32B AWQ (vision, local)",
};

function fieldSection(r) {
  const els = [];
  els.push(new Paragraph({
    children: [
      new TextRun({ text: `${r.number}. ${r.label}`, bold: true, size: 26 }),
      new TextRun({ text: `   [${r.difficulty}]`, italics: true, size: 20, color: "666666" }),
    ],
    spacing: { before: 260, after: 80 },
  }));
  els.push(new Paragraph({
    children: [
      new TextRun({ text: "Ground truth: ", bold: true }),
      new TextRun({ text: r.truth_present ? r.truth_value : "(absent — not specified in the document)" }),
    ],
    spacing: { after: 60 },
  }));
  if (r.note) {
    els.push(new Paragraph({
      children: [new TextRun({ text: "Note: " + r.note, italics: true, size: 19, color: "555555" })],
      spacing: { after: 100 },
    }));
  }

  const header = new TableRow({
    tableHeader: true,
    children: ["Model", "Answer", "Verdict"].map((t, i) =>
      cell(t, { width: [2400, 5800, 1400][i], shade: "D9D9D9", bold: true })),
  });
  const rows = Object.entries(r.models).map(([backend, m]) => new TableRow({
    children: [
      cell(MODEL_LABEL[backend], { width: 2400 }),
      cell(m.present === false ? "(said absent)" : m.value, { width: 5800 }),
      cell(VERDICT_LABEL[m.verdict], { width: 1400, shade: VERDICT_COLOR[m.verdict] }),
    ],
  }));
  els.push(new Table({
    width: { size: 9600, type: WidthType.DXA },
    columnWidths: [2400, 5800, 1400],
    rows: [header, ...rows],
  }));
  return els;
}

// ---------- Assemble ------------------------------------------------------
const children = [];

children.push(new Paragraph({
  children: [new TextRun({ text: "RFP Field-Extraction Benchmark", bold: true, size: 44 })],
  spacing: { after: 80 },
}));
children.push(new Paragraph({
  children: [new TextRun({
    text: "Questions asked, and how GPT-4o, Llama-3.3-70B and Qwen3-VL-32B answered them",
    size: 24, color: "555555",
  })],
  spacing: { after: 300 },
}));

children.push(heading("1. What was asked — the 17 fields", HeadingLevel.HEADING_1));
children.push(para(
  "Every model was given the same RFP document and asked to extract the same 17 fields, " +
  "each as a structured answer: present/absent, the extracted value, a page number, and a " +
  "verbatim quote from the source. Difficulty was assigned after reading the source RFP in " +
  "full and is a property of the document, not of any model's answer.", { size: 20 }));
children.push(questionsTable);

children.push(heading("2. Groundedness — is every answer backed by a real quote?", HeadingLevel.HEADING_1));
children.push(para(
  "Before any answer is checked against ground truth, every field a model marks “present” " +
  "is verified mechanically: does its quote actually appear in the source PDF? This catches " +
  "fabrication independent of whether the value itself is correct, and it required no hand " +
  "labeling to compute — it ran across all 6 documents in the corpus for all three models.", { size: 20 }));
children.push(groundingTable());
children.push(para(
  "All three models reached perfect groundedness (1.000) with zero hallucinated quotes across " +
  "306 field-extractions (3 models × 6 documents × 17 fields). Every apparent hallucination " +
  "encountered during development turned out to be a bug in the verification checker, never the " +
  "model — documented in the project's rescore.py history.", { size: 20, italics: true }));

children.push(heading("3. Accuracy against hand-written ground truth", HeadingLevel.HEADING_1));
children.push(para(
  "Groundedness says a value is backed by real text; it says nothing about whether the value is " +
  "correct. Ground truth was produced by reading the source RFP directly (“RFP CP-730126, " +
  "Generative AI Software”, University of Saskatchewan, 33 pages) and hand-writing the correct " +
  "answer for all 17 fields, with two deliberate absence traps and one deliberate hallucination " +
  "trap built in. This is the only document graded against ground truth so far.", { size: 20 }));
children.push(accuracyTable());
children.push(para(
  "Caveat: GPT-4o's OpenAI project hit a configured spend limit mid-benchmark, so 2 of its 17 " +
  "fields (mandatory_submission_requirements, mandatory_technical_requirements) reflect an earlier, " +
  "retrieval-bugged run rather than the corrected pipeline the other two models were graded against. " +
  "Its 70.6% is not on fully equal footing with the other two scores until it is re-run.",
  { size: 19, italics: true, color: "884400" }));

children.push(new Paragraph({ children: [new TextRun({ text: "", break: 1 })], pageBreakBefore: true }));
children.push(heading("4. Per-field detail", HeadingLevel.HEADING_1));
children.push(para(
  "For every field: the ground truth answer, then what each model actually returned, and the " +
  "grading verdict. Verdicts account for field type — exact match after date/number normalisation " +
  "for atomic fields, recall/precision overlap for lists and tables, similarity scoring for free text.",
  { size: 20 }));

for (const r of data.rows) {
  for (const el of fieldSection(r)) children.push(el);
}

const doc = new Document({
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: PAGE_H }, margin: { top: 1000, bottom: 1000, left: 1000, right: 1000 } } },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/home/ubuntu/aidc/project-qwen-rfp/RFP-Benchmark-Questions-and-Results.docx", buf);
  console.log("wrote RFP-Benchmark-Questions-and-Results.docx");
});
