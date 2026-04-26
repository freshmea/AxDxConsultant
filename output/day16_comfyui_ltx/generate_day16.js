const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");
const slides = require("./slide_data_day16");

const outDir = __dirname;
const htmlPath = path.join(outDir, "day16_comfyui_ltx.html");
const pptxPath = path.join(outDir, "day16_comfyui_ltx.pptx");
const theme = { bg: "0B1020", panel: "121A30", panelAlt: "162441", primary: "41D9E6", secondary: "7C72FF", accent: "FF6B57", text: "F5F7FB", subtext: "AAB7D4", border: "2A3657", success: "35D49A" };

function esc(text) { return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
function chunk(items, size) { const out = []; for (let i = 0; i < items.length; i += size) out.push(items.slice(i, i + size)); return out; }

function renderVisualHtml(v) {
  const label = `<div class="visual-label">${esc(v.label || "")}</div>`;
  if (v.type === "compare") {
    return `${label}<div class="compare"><div class="compare-col"><h3>${esc(v.leftTitle)}</h3><ul>${v.leftItems.map((i) => `<li>${esc(i)}</li>`).join("")}</ul></div><div class="compare-col"><h3>${esc(v.rightTitle)}</h3><ul>${v.rightItems.map((i) => `<li>${esc(i)}</li>`).join("")}</ul></div></div>`;
  }
  if (v.type === "table") {
    return `${label}<table class="mini-table"><tbody>${v.rows.map((r) => `<tr><th>${esc(r[0])}</th><td>${esc(r[1])}</td></tr>`).join("")}</tbody></table>`;
  }
  if (["flow", "timeline", "steps", "formula"].includes(v.type)) {
    return `${label}<div class="flow-row">${v.items.map((i, n) => `<div class="flow-item"><span class="flow-index">${n + 1}</span><span>${esc(i)}</span></div>`).join("")}</div>`;
  }
  if (["stack", "folders"].includes(v.type)) {
    return `${label}<div class="stack-col">${v.items.map((i) => `<div class="stack-item">${esc(i)}</div>`).join("")}</div>`;
  }
  if (v.type === "hero" || v.type === "summary") {
    return `${label}<div class="hero-cloud">${v.items.map((i) => `<span>${esc(i)}</span>`).join("")}</div>`;
  }
  return `${label}<div class="card-grid">${v.items.map((i) => `<div class="card-item">${esc(i)}</div>`).join("")}</div>`;
}

function buildHtml() {
  const body = slides.map((s, idx) => `
    <section class="slide ${idx % 2 ? "reverse" : ""}">
      <div class="top"><span class="session">${esc(s.session)}</span><span class="num">${String(s.id).padStart(2, "0")} / 40</span></div>
      <div class="kicker">${esc(s.kicker)}</div>
      <h1>${esc(s.title)}</h1>
      ${s.subtitle ? `<p class="subtitle">${esc(s.subtitle)}</p>` : ""}
      <div class="body">
        <div class="panel content"><ul>${s.bullets.map((b) => `<li>${esc(b)}</li>`).join("")}</ul></div>
        <div class="panel visual">${renderVisualHtml(s.visual)}</div>
      </div>
      <div class="panel note"><strong>강사 포인트</strong><p>${esc(s.note)}</p></div>
    </section>`).join("");

  const html = `<!doctype html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>16일차 ComfyUI + LTX-Video 교안</title><style>
  :root{--bg:#${theme.bg};--panel:#${theme.panel};--panel-alt:#${theme.panelAlt};--primary:#${theme.primary};--secondary:#${theme.secondary};--accent:#${theme.accent};--text:#${theme.text};--subtext:#${theme.subtext};--border:#${theme.border};}
  *{box-sizing:border-box} body{margin:0;padding:24px;background:radial-gradient(circle at top left,rgba(65,217,230,.12),transparent 24%),radial-gradient(circle at top right,rgba(124,114,255,.12),transparent 20%),linear-gradient(180deg,#050814,var(--bg));color:var(--text);font-family:"Aptos","Malgun Gothic",sans-serif}
  main{max-width:1440px;margin:0 auto;display:grid;gap:24px}.slide{min-height:810px;padding:32px;border:1px solid var(--border);border-radius:24px;background:linear-gradient(180deg,rgba(255,255,255,.02),rgba(255,255,255,0));box-shadow:0 20px 60px rgba(0,0,0,.24)}.top{display:flex;justify-content:space-between;color:var(--subtext);font-size:14px}.session,.num{padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.05)}.session{color:var(--primary);font-weight:700;background:rgba(65,217,230,.12)}.kicker{margin-top:16px;color:var(--primary);font-size:13px;font-weight:800}.subtitle{color:var(--subtext);font-size:24px;max-width:960px}.slide h1{margin:10px 0 0;font-size:52px;line-height:1.08;max-width:960px;font-family:"Aptos Display","Malgun Gothic",sans-serif}.body{margin-top:24px;display:grid;grid-template-columns:1.05fr .95fr;gap:20px}.reverse .body{grid-template-columns:.95fr 1.05fr}.panel{background:rgba(18,26,48,.84);border:1px solid var(--border);border-radius:20px}.content{padding:24px}.content ul{margin:0;padding-left:24px;display:grid;gap:16px;font-size:24px;line-height:1.45}.content li::marker{color:var(--primary)}.visual{padding:22px;min-height:430px}.visual-label{color:var(--subtext);font-size:14px;font-weight:700;margin-bottom:12px}.card-grid,.compare,.flow-row{display:grid;gap:12px}.card-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.card-item,.compare-col,.flow-item,.stack-item,.hero-cloud span{border:1px solid rgba(255,255,255,.08);background:rgba(22,36,65,.9);border-radius:18px}.card-item{min-height:100px;display:flex;align-items:center;justify-content:center;padding:18px;text-align:center;font-size:22px;font-weight:700}.compare{grid-template-columns:repeat(2,minmax(0,1fr))}.compare-col{padding:18px}.compare-col h3{margin:0 0 10px;color:var(--primary)}.compare-col ul{margin:0;padding-left:20px;color:var(--subtext);font-size:18px;line-height:1.45}.flow-row{grid-template-columns:repeat(auto-fit,minmax(130px,1fr))}.flow-item{padding:16px;display:grid;gap:8px;min-height:96px;font-size:18px;font-weight:700}.flow-index{width:34px;height:34px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;background:var(--primary);color:#031019;font-weight:900}.stack-col{display:grid;gap:12px}.stack-item{padding:18px 18px 18px 52px;position:relative;font-size:22px;font-weight:700}.stack-item::before{content:"";position:absolute;left:18px;top:50%;transform:translateY(-50%);width:18px;height:18px;border-radius:6px;background:linear-gradient(135deg,var(--primary),var(--secondary))}.hero-cloud{display:flex;flex-wrap:wrap;gap:12px;justify-content:center}.hero-cloud span{padding:16px 20px;font-size:20px;font-weight:800}.mini-table{width:100%;border-collapse:collapse;font-size:17px}.mini-table th,.mini-table td{border:1px solid rgba(255,255,255,.08);padding:14px;text-align:left}.mini-table th{width:38%;color:var(--primary)}.note{margin-top:18px;padding:14px 18px}.note strong{color:var(--accent);font-size:13px}.note p{margin:8px 0 0;color:var(--subtext);font-size:16px;line-height:1.55}@media(max-width:1180px){.slide h1{font-size:42px}.body{grid-template-columns:1fr}.content ul{font-size:20px}}
  </style></head><body><main>${body}</main></body></html>`;
  fs.writeFileSync(htmlPath, html, "utf8");
}

function addVisual(slide, shapes, v, x, y, w, h) {
  slide.addText(v.label || "", { x, y, w, h: 0.24, fontFace: "Aptos", fontSize: 9.5, color: theme.subtext, bold: true, margin: 0 });
  const y0 = y + 0.28, h0 = h - 0.28;
  if (v.type === "compare") {
    const colW = (w - 0.14) / 2;
    [["left", x], ["right", x + colW + 0.14]].forEach(([side, xx]) => {
      slide.addShape(shapes.RECTANGLE, { x: xx, y: y0, w: colW, h: h0, fill: { color: theme.panelAlt }, line: { color: theme.border, width: 1 } });
      slide.addText(v[`${side}Title`], { x: xx + 0.12, y: y0 + 0.1, w: colW - 0.24, h: 0.22, fontFace: "Aptos", fontSize: 14, color: theme.primary, bold: true, margin: 0 });
      slide.addText(v[`${side}Items`].map((t, i, arr) => ({ text: t, options: { bullet: true, breakLine: i !== arr.length - 1 } })), { x: xx + 0.14, y: y0 + 0.38, w: colW - 0.24, h: h0 - 0.46, fontFace: "Aptos", fontSize: 11.2, color: theme.subtext, margin: 0.03 });
    });
    return;
  }
  if (v.type === "table") {
    slide.addTable(v.rows, { x, y: y0, w, h: h0, border: { pt: 1, color: theme.border }, fill: theme.panelAlt, color: theme.text, fontFace: "Aptos", fontSize: 11, margin: 0.05, colW: [w * 0.38, w * 0.62] });
    return;
  }
  if (["hero", "summary"].includes(v.type)) {
    chunk(v.items, 3).forEach((row, ry) => row.forEach((t, cx) => {
      const boxW = (w - 0.12 * (row.length - 1)) / row.length;
      const xx = x + cx * (boxW + 0.12), yy = y0 + ry * 0.7;
      slide.addShape(shapes.ROUNDED_RECTANGLE, { x: xx, y: yy, w: boxW, h: 0.5, rectRadius: 0.08, fill: { color: theme.panelAlt }, line: { color: theme.border, width: 1 } });
      slide.addText(t, { x: xx + 0.06, y: yy + 0.1, w: boxW - 0.12, h: 0.22, fontFace: "Aptos", fontSize: 11.5, color: cx % 2 === 0 ? theme.primary : theme.secondary, bold: true, align: "center", margin: 0 });
    }));
    return;
  }
  const items = v.items || [];
  const cols = ["grid", "cards", "checklist", "quadrants"].includes(v.type) ? 2 : Math.min(items.length, 5);
  const rows = Math.ceil(items.length / cols), gapX = 0.12, gapY = 0.12, boxW = (w - gapX * (cols - 1)) / cols, boxH = Math.min(0.9, (h0 - gapY * (rows - 1)) / rows);
  items.forEach((t, i) => {
    const row = Math.floor(i / cols), col = i % cols, xx = x + col * (boxW + gapX), yy = y0 + row * (boxH + gapY);
    slide.addShape(shapes.RECTANGLE, { x: xx, y: yy, w: boxW, h: boxH, fill: { color: theme.panelAlt }, line: { color: theme.border, width: 1 } });
    if (v.type === "checklist") slide.addShape(shapes.OVAL, { x: xx + 0.12, y: yy + 0.15, w: 0.16, h: 0.16, fill: { color: theme.success }, line: { color: theme.success, width: 0.5 } });
    slide.addText(t, { x: xx + 0.16, y: yy + 0.14, w: boxW - 0.24, h: boxH - 0.18, fontFace: "Aptos", fontSize: 11.2, color: theme.text, bold: true, align: "center", valign: "mid", margin: 0.04 });
  });
}

async function buildPptx() {
  const pptx = new PptxGenJS();
  const shapes = pptx.shapes;
  pptx.layout = "LAYOUT_16x9";
  pptx.author = "OpenAI Codex";
  pptx.title = "16일차 고성능 AI 영상 제작 실무";
  pptx.subject = "ComfyUI + LTX-Video 교안";
  slides.forEach((s, idx) => {
    const slide = pptx.addSlide();
    slide.background = { color: theme.bg };
    slide.addShape(shapes.RECTANGLE, { x: 0.28, y: 0.22, w: 9.44, h: 5.18, fill: { color: "10182D" }, line: { color: theme.border, width: 1 } });
    slide.addShape(shapes.RECTANGLE, { x: 8.72, y: 0.22, w: 1.0, h: 5.18, fill: { color: idx % 2 === 0 ? "0F1E38" : "132347" }, line: { color: theme.border, width: 0.5 } });
    slide.addText(s.session, { x: 0.48, y: 0.34, w: 0.84, h: 0.2, fontFace: "Aptos", fontSize: 9.5, color: theme.primary, bold: true, align: "center", fill: { color: "17304D" }, margin: 0.02 });
    slide.addText(`${String(s.id).padStart(2, "0")} / 40`, { x: 8.92, y: 0.34, w: 0.56, h: 0.18, fontFace: "Aptos", fontSize: 9, color: theme.subtext, bold: true, align: "center", margin: 0 });
    slide.addText(s.kicker, { x: 0.5, y: 0.66, w: 4, h: 0.18, fontFace: "Aptos", fontSize: 9, color: theme.primary, bold: true, charSpacing: 1, margin: 0 });
    slide.addText(s.title, { x: 0.5, y: 0.9, w: 7.7, h: 0.54, fontFace: "Aptos Display", fontSize: s.title.length > 26 ? 24 : 28, color: theme.text, bold: true, margin: 0 });
    let top = 1.56;
    if (s.subtitle) { slide.addText(s.subtitle, { x: 0.5, y: 1.32, w: 7.5, h: 0.2, fontFace: "Aptos", fontSize: 12, color: theme.subtext, margin: 0 }); top = 1.64; }
    const leftX = idx % 2 === 0 ? 0.52 : 4.92, rightX = idx % 2 === 0 ? 4.92 : 0.52;
    slide.addShape(shapes.RECTANGLE, { x: leftX, y: top, w: 4.15, h: 2.74, fill: { color: theme.panel }, line: { color: theme.border, width: 1 } });
    slide.addShape(shapes.RECTANGLE, { x: rightX, y: top, w: 3.58, h: 2.74, fill: { color: theme.panel }, line: { color: theme.border, width: 1 } });
    slide.addText(s.bullets.map((t, i, arr) => ({ text: t, options: { bullet: true, breakLine: i !== arr.length - 1 } })), { x: leftX + 0.18, y: top + 0.18, w: 3.78, h: 2.38, fontFace: "Aptos", fontSize: 13.1, color: theme.text, margin: 0.04, paraSpaceAfterPt: 6 });
    addVisual(slide, shapes, s.visual, rightX + 0.16, top + 0.16, 3.24, 2.36);
    slide.addShape(shapes.RECTANGLE, { x: 0.52, y: 4.48, w: 7.98, h: 0.56, fill: { color: "111B33" }, line: { color: theme.border, width: 1 } });
    slide.addText("강사 포인트", { x: 0.66, y: 4.6, w: 0.84, h: 0.16, fontFace: "Aptos", fontSize: 9.3, color: theme.accent, bold: true, margin: 0 });
    slide.addText(s.note, { x: 1.64, y: 4.56, w: 6.56, h: 0.3, fontFace: "Aptos", fontSize: 9.6, color: theme.subtext, margin: 0 });
    slide.addText(s.session === "오전" ? "Morning Lab" : "Afternoon Lab", { x: 8.88, y: 1.2, w: 0.6, h: 0.7, rotate: 90, fontFace: "Aptos Display", fontSize: 11.5, color: idx % 2 === 0 ? theme.primary : theme.secondary, bold: true, align: "center", margin: 0 });
  });
  await pptx.writeFile({ fileName: pptxPath });
}

async function main() {
  buildHtml();
  await buildPptx();
  console.log(`Wrote ${htmlPath}`);
  console.log(`Wrote ${pptxPath}`);
}

main().catch((err) => { console.error(err); process.exit(1); });
