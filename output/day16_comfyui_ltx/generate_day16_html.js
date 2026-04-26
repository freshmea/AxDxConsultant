const fs = require("fs");
const path = require("path");
const slides = require("./slide_data_day16");

const outDir = __dirname;
const htmlPath = path.join(outDir, "day16_comfyui_ltx.html");
const theme = {
  bg: "#0B1020",
  panel: "#121A30",
  panelAlt: "#162441",
  panelAlt2: "#1D2E54",
  primary: "#41D9E6",
  secondary: "#7C72FF",
  accent: "#FF6B57",
  text: "#F5F7FB",
  subtext: "#AAB7D4",
  border: "#2A3657",
  success: "#35D49A",
  warning: "#FFC857"
};

function esc(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function pointsOnCircle(count, cx, cy, radius) {
  return Array.from({ length: count }, (_, i) => {
    const angle = (-Math.PI / 2) + (Math.PI * 2 * i) / count;
    return { x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius };
  });
}

function svgShell(inner, extraClass = "") {
  return `
    <svg class="viz-svg ${extraClass}" viewBox="0 0 620 360" role="img" aria-label="diagram">
      <defs>
        <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#182544"/>
          <stop offset="100%" stop-color="#0F1730"/>
        </linearGradient>
        <linearGradient id="cyanViolet" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="${theme.primary}"/>
          <stop offset="100%" stop-color="${theme.secondary}"/>
        </linearGradient>
        <filter id="softGlow">
          <feGaussianBlur stdDeviation="8" result="blur"/>
          <feMerge>
            <feMergeNode in="blur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
      <rect x="8" y="8" width="604" height="344" rx="24" fill="url(#bgGrad)" stroke="${theme.border}" />
      <circle cx="520" cy="56" r="40" fill="rgba(65,217,230,.08)" />
      <circle cx="96" cy="298" r="52" fill="rgba(124,114,255,.08)" />
      ${inner}
    </svg>`;
}

function svgHero(items) {
  const pts = pointsOnCircle(items.length, 310, 172, 116);
  return svgShell(`
    <rect x="212" y="116" width="196" height="112" rx="20" fill="#121A30" stroke="${theme.primary}" />
    <rect x="230" y="136" width="160" height="72" rx="14" fill="#1E305A" />
    <polygon points="295,150 295,194 336,172" fill="${theme.primary}" filter="url(#softGlow)"/>
    ${pts.map((pt, idx) => `
      <line x1="310" y1="172" x2="${pt.x}" y2="${pt.y}" stroke="rgba(255,255,255,.10)" />
      <rect x="${pt.x - 54}" y="${pt.y - 20}" width="108" height="40" rx="16" fill="#1A2950" stroke="${idx % 2 ? theme.secondary : theme.primary}" />
      <text x="${pt.x}" y="${pt.y + 7}" fill="${theme.text}" text-anchor="middle" font-size="18" font-weight="700">${esc(items[idx])}</text>
    `).join("")}
  `);
}

function svgNodeFlow(items) {
  const startX = 36;
  const width = 88;
  const gap = 18;
  return svgShell(`
    <text x="44" y="54" fill="${theme.subtext}" font-size="18">workflow / pipeline diagram</text>
    ${items.map((item, idx) => {
      const x = startX + idx * (width + gap);
      const y = idx % 2 === 0 ? 126 : 202;
      const nextX = x + width + gap;
      const nextY = idx % 2 === 0 ? 202 : 126;
      return `
        <rect x="${x}" y="${y}" width="${width}" height="56" rx="16" fill="#1A2950" stroke="${idx % 2 ? theme.secondary : theme.primary}" />
        <circle cx="${x + 18}" cy="${y + 18}" r="10" fill="${idx % 2 ? theme.secondary : theme.primary}" />
        <text x="${x + width / 2}" y="${y + 36}" fill="${theme.text}" text-anchor="middle" font-size="16" font-weight="700">${esc(item)}</text>
        ${idx < items.length - 1 ? `
          <path d="M ${x + width} ${y + 28} C ${x + width + 20} ${y + 28}, ${nextX - 20} ${nextY + 28}, ${nextX} ${nextY + 28}" fill="none" stroke="url(#cyanViolet)" stroke-width="4" />
          <polygon points="${nextX - 8},${nextY + 22} ${nextX + 6},${nextY + 28} ${nextX - 8},${nextY + 34}" fill="${theme.primary}" />
        ` : ""}
      `;
    }).join("")}
  `);
}

function svgStack(items, folderMode = false) {
  return svgShell(`
    ${items.map((item, idx) => `
      <g transform="translate(${74 + idx * 14}, ${70 + idx * 42})">
        <rect width="410" height="46" rx="14" fill="#1A2950" stroke="${idx % 2 ? theme.secondary : theme.primary}" />
        <rect x="18" y="13" width="${folderMode ? 34 : 22}" height="${folderMode ? 18 : 22}" rx="5" fill="${idx % 2 ? theme.secondary : theme.primary}" />
        ${folderMode ? `<rect x="18" y="8" width="20" height="10" rx="4" fill="${theme.warning}" />` : ""}
        <text x="68" y="29" fill="${theme.text}" font-size="18" font-weight="700">${esc(item)}</text>
      </g>
    `).join("")}
  `);
}

function svgCompare(leftTitle, leftItems, rightTitle, rightItems) {
  const renderCol = (title, items, x, accent) => `
    <rect x="${x}" y="70" width="228" height="218" rx="18" fill="#162441" stroke="${accent}" />
    <text x="${x + 24}" y="102" fill="${accent}" font-size="22" font-weight="800">${esc(title)}</text>
    ${items.map((item, idx) => `
      <circle cx="${x + 28}" cy="${136 + idx * 34}" r="6" fill="${accent}" />
      <rect x="${x + 44}" y="${124 + idx * 34}" width="${130 + idx * 10}" height="22" rx="11" fill="rgba(255,255,255,.05)" />
      <text x="${x + 56}" y="${140 + idx * 34}" fill="${theme.text}" font-size="16">${esc(item)}</text>
    `).join("")}
  `;
  return svgShell(`${renderCol(leftTitle, leftItems, 60, theme.primary)}${renderCol(rightTitle, rightItems, 332, theme.secondary)}`);
}

function svgDashboard(items) {
  const labels = items.slice(0, 4);
  return svgShell(`
    <rect x="46" y="58" width="528" height="248" rx="20" fill="#10182D" stroke="${theme.border}" />
    <rect x="46" y="58" width="112" height="248" rx="20" fill="#121A30" stroke="${theme.border}" />
    <rect x="176" y="78" width="240" height="150" rx="18" fill="#162441" stroke="${theme.primary}" />
    <path d="M 202 176 C 236 104, 274 148, 308 112 S 378 148, 390 102" fill="none" stroke="${theme.primary}" stroke-width="4" />
    <circle cx="308" cy="112" r="12" fill="${theme.secondary}" />
    ${labels.map((label, idx) => `
      <rect x="${192 + (idx % 2) * 116}" y="${244 + Math.floor(idx / 2) * 34}" width="100" height="24" rx="10" fill="#1E305A" />
      <text x="${242 + (idx % 2) * 116}" y="${260 + Math.floor(idx / 2) * 34}" text-anchor="middle" fill="${theme.text}" font-size="14">${esc(label)}</text>
    `).join("")}
    ${["Input", "Sampler", "Preview", "Queue"].map((tag, idx) => `
      <rect x="68" y="${82 + idx * 48}" width="68" height="28" rx="10" fill="${idx % 2 ? "#1A2950" : "#20315B"}" />
      <text x="102" y="${101 + idx * 48}" text-anchor="middle" fill="${theme.subtext}" font-size="14">${tag}</text>
    `).join("")}
    <rect x="438" y="78" width="112" height="64" rx="16" fill="#162441" stroke="${theme.secondary}" />
    <rect x="438" y="154" width="112" height="64" rx="16" fill="#162441" stroke="${theme.primary}" />
    <rect x="438" y="230" width="112" height="54" rx="16" fill="#162441" stroke="${theme.accent}" />
  `);
}

function svgTable(rows) {
  return svgShell(`
    <rect x="58" y="78" width="504" height="208" rx="18" fill="#162441" stroke="${theme.border}" />
    ${rows.map((row, idx) => `
      <line x1="58" y1="${124 + idx * 42}" x2="562" y2="${124 + idx * 42}" stroke="rgba(255,255,255,.08)" />
      <rect x="76" y="${92 + idx * 42}" width="154" height="24" rx="10" fill="rgba(65,217,230,.12)" />
      <text x="90" y="${109 + idx * 42}" fill="${theme.primary}" font-size="16" font-weight="700">${esc(row[0])}</text>
      <rect x="258" y="${92 + idx * 42}" width="${180 + idx * 12}" height="24" rx="10" fill="${idx % 2 ? "rgba(124,114,255,.18)" : "rgba(255,255,255,.06)"}" />
      <text x="272" y="${109 + idx * 42}" fill="${theme.text}" font-size="15">${esc(row[1])}</text>
    `).join("")}
    <text x="74" y="66" fill="${theme.subtext}" font-size="17">review / troubleshooting matrix</text>
  `);
}

function svgStoryboard(items) {
  return svgShell(`
    ${items.map((item, idx) => `
      <g transform="translate(${58 + idx * 132}, 94)">
        <rect width="112" height="158" rx="18" fill="#162441" stroke="${idx % 2 ? theme.secondary : theme.primary}" />
        <rect x="12" y="14" width="88" height="64" rx="12" fill="#20315B" />
        <path d="M 24 64 Q 54 26 88 52" fill="none" stroke="${idx % 2 ? theme.secondary : theme.primary}" stroke-width="4" />
        <circle cx="36" cy="42" r="9" fill="${theme.warning}" />
        <text x="56" y="108" text-anchor="middle" fill="${theme.primary}" font-size="22" font-weight="800">${idx + 1}</text>
        <text x="56" y="132" text-anchor="middle" fill="${theme.text}" font-size="16" font-weight="700">${esc(item)}</text>
      </g>
      ${idx < items.length - 1 ? `<path d="M ${170 + idx * 132} 172 C ${186 + idx * 132} 172, ${186 + idx * 132} 172, ${190 + idx * 132} 172" stroke="url(#cyanViolet)" stroke-width="5" />` : ""}
    `).join("")}
  `);
}

function svgIconGrid(items, type = "cards") {
  const cols = 2;
  return svgShell(`
    ${items.map((item, idx) => {
      const col = idx % cols;
      const row = Math.floor(idx / cols);
      const x = 62 + col * 252;
      const y = 76 + row * 92;
      const accent = idx % 3 === 0 ? theme.primary : idx % 3 === 1 ? theme.secondary : theme.warning;
      return `
        <rect x="${x}" y="${y}" width="214" height="70" rx="18" fill="#162441" stroke="${accent}" />
        <circle cx="${x + 28}" cy="${y + 35}" r="14" fill="${accent}" />
        <path d="M ${x + 22} ${y + 36} l5 6 9 -14" fill="none" stroke="#071018" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" opacity="${type === "checklist" ? 1 : 0}" />
        <rect x="${x + 18}" y="${y + 20}" width="20" height="20" rx="6" fill="${type === "checklist" ? accent : "#20315B"}" opacity="${type === "checklist" ? 0 : 1}" />
        <text x="${x + 54}" y="${y + 42}" fill="${theme.text}" font-size="18" font-weight="700">${esc(item)}</text>
      `;
    }).join("")}
  `);
}

function renderIllustration(slide) {
  const v = slide.visual;
  if (v.type === "hero") return svgHero(v.items);
  if (v.type === "compare") return svgCompare(v.leftTitle, v.leftItems, v.rightTitle, v.rightItems);
  if (["flow", "steps", "formula"].includes(v.type)) return svgNodeFlow(v.items);
  if (v.type === "timeline") return svgStoryboard(v.items);
  if (v.type === "stack") return svgStack(v.items, false);
  if (v.type === "folders") return svgStack(v.items, true);
  if (v.type === "quadrants") return svgDashboard(v.items);
  if (v.type === "table") return svgTable(v.rows);
  if (v.type === "checklist") return svgIconGrid(v.items, "checklist");
  return svgIconGrid(v.items || [], "cards");
}

function renderLegend(slide) {
  const v = slide.visual;
  if (v.type === "compare") {
    return `
      <div class="legend-grid compare-legend">
        <div><strong>${esc(v.leftTitle)}</strong><span>${v.leftItems.map(esc).join(" / ")}</span></div>
        <div><strong>${esc(v.rightTitle)}</strong><span>${v.rightItems.map(esc).join(" / ")}</span></div>
      </div>`;
  }
  if (v.type === "table") {
    return `<div class="legend-grid compact">${v.rows.map((row) => `<div><strong>${esc(row[0])}</strong><span>${esc(row[1])}</span></div>`).join("")}</div>`;
  }
  return `<div class="legend-chips">${(v.items || []).map((item, idx) => `<span class="legend-chip ${idx % 3 === 0 ? "is-cyan" : idx % 3 === 1 ? "is-violet" : "is-gold"}">${esc(item)}</span>`).join("")}</div>`;
}

function buildHtml() {
  const slidesHtml = slides.map((slide, idx) => `
    <section class="slide ${idx % 2 ? "reverse" : ""}" id="slide-${slide.id}">
      <div class="topline">
        <span class="session">${esc(slide.session)}</span>
        <span class="num">${String(slide.id).padStart(2, "0")} / 40</span>
      </div>
      <div class="kicker">${esc(slide.kicker)}</div>
      <h1>${esc(slide.title)}</h1>
      ${slide.subtitle ? `<p class="subtitle">${esc(slide.subtitle)}</p>` : ""}
      <div class="body">
        <article class="panel content">
          <ul class="bullet-list">
            ${slide.bullets.map((bullet) => `<li>${esc(bullet)}</li>`).join("")}
          </ul>
        </article>
        <aside class="panel visual">
          <div class="visual-head">
            <span class="visual-label">${esc(slide.visual.label || "도식")}</span>
            <span class="visual-kind">${esc(slide.visual.type)}</span>
          </div>
          <div class="visual-stage">
            ${renderIllustration(slide)}
          </div>
          ${renderLegend(slide)}
        </aside>
      </div>
      <div class="panel note">
        <strong>강사 포인트</strong>
        <p>${esc(slide.note)}</p>
      </div>
    </section>`).join("");

  const html = `<!doctype html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>16일차 ComfyUI + LTX-Video 교안</title>
  <style>
    :root {
      --bg: ${theme.bg};
      --panel: ${theme.panel};
      --panel-alt: ${theme.panelAlt};
      --panel-alt2: ${theme.panelAlt2};
      --primary: ${theme.primary};
      --secondary: ${theme.secondary};
      --accent: ${theme.accent};
      --text: ${theme.text};
      --subtext: ${theme.subtext};
      --border: ${theme.border};
      --success: ${theme.success};
      --warning: ${theme.warning};
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 24px;
      background:
        radial-gradient(circle at top left, rgba(65, 217, 230, .13), transparent 26%),
        radial-gradient(circle at 80% 0%, rgba(124, 114, 255, .12), transparent 22%),
        linear-gradient(180deg, #060A16 0%, var(--bg) 100%);
      color: var(--text);
      font-family: "Aptos", "Malgun Gothic", sans-serif;
    }
    main {
      max-width: 1440px;
      margin: 0 auto;
      display: grid;
      gap: 24px;
    }
    .slide {
      min-height: 860px;
      padding: 32px;
      border: 1px solid var(--border);
      border-radius: 24px;
      background:
        linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,0)),
        linear-gradient(135deg, rgba(65,217,230,.04), rgba(124,114,255,.05));
      box-shadow: 0 20px 60px rgba(0,0,0,.25);
      position: relative;
      overflow: hidden;
    }
    .slide::after {
      content: "";
      position: absolute;
      right: -80px;
      bottom: -80px;
      width: 220px;
      height: 220px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(65,217,230,.12), transparent 70%);
      pointer-events: none;
    }
    .topline {
      display: flex;
      justify-content: space-between;
      color: var(--subtext);
      font-size: 14px;
    }
    .session,
    .num {
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(255,255,255,.05);
    }
    .session {
      background: rgba(65,217,230,.12);
      color: var(--primary);
      font-weight: 800;
    }
    .kicker {
      margin-top: 16px;
      color: var(--primary);
      font-size: 13px;
      font-weight: 800;
      letter-spacing: .03em;
      text-transform: uppercase;
    }
    h1 {
      margin: 10px 0 0;
      max-width: 1000px;
      font-size: 52px;
      line-height: 1.08;
      font-family: "Aptos Display", "Malgun Gothic", sans-serif;
    }
    .subtitle {
      margin: 14px 0 0;
      max-width: 980px;
      color: var(--subtext);
      font-size: 26px;
    }
    .body {
      margin-top: 24px;
      display: grid;
      grid-template-columns: 1.02fr .98fr;
      gap: 20px;
      align-items: stretch;
    }
    .reverse .body {
      grid-template-columns: .98fr 1.02fr;
    }
    .panel {
      border: 1px solid var(--border);
      border-radius: 22px;
      background: rgba(18,26,48,.84);
    }
    .content {
      padding: 24px;
    }
    .bullet-list {
      margin: 0;
      padding-left: 24px;
      display: grid;
      gap: 18px;
      font-size: 24px;
      line-height: 1.45;
    }
    .bullet-list li::marker {
      color: var(--primary);
    }
    .visual {
      padding: 18px;
      display: grid;
      gap: 14px;
      align-content: start;
    }
    .visual-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
    }
    .visual-label {
      color: var(--subtext);
      font-size: 14px;
      font-weight: 800;
      letter-spacing: .02em;
    }
    .visual-kind {
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,.05);
      color: var(--subtext);
      font-size: 12px;
      text-transform: uppercase;
    }
    .visual-stage {
      min-height: 420px;
      display: grid;
      place-items: center;
    }
    .viz-svg {
      width: 100%;
      height: auto;
      display: block;
    }
    .legend-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .legend-chip {
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(255,255,255,.05);
      font-size: 14px;
      font-weight: 700;
      border: 1px solid rgba(255,255,255,.06);
    }
    .legend-chip.is-cyan { color: var(--primary); }
    .legend-chip.is-violet { color: var(--secondary); }
    .legend-chip.is-gold { color: var(--warning); }
    .legend-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }
    .legend-grid.compact {
      grid-template-columns: 1fr;
    }
    .legend-grid div {
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(255,255,255,.04);
      border: 1px solid rgba(255,255,255,.06);
      display: grid;
      gap: 6px;
    }
    .legend-grid strong {
      color: var(--text);
      font-size: 15px;
    }
    .legend-grid span {
      color: var(--subtext);
      font-size: 14px;
      line-height: 1.45;
    }
    .note {
      margin-top: 18px;
      padding: 14px 18px;
    }
    .note strong {
      color: var(--accent);
      font-size: 13px;
      letter-spacing: .03em;
    }
    .note p {
      margin: 8px 0 0;
      color: var(--subtext);
      font-size: 16px;
      line-height: 1.55;
    }
    @media (max-width: 1180px) {
      .slide { min-height: auto; }
      h1 { font-size: 42px; }
      .subtitle { font-size: 22px; }
      .body,
      .reverse .body {
        grid-template-columns: 1fr;
      }
      .bullet-list { font-size: 20px; }
    }
  </style>
</head>
<body>
  <main>
    ${slidesHtml}
  </main>
</body>
</html>`;

  fs.writeFileSync(htmlPath, html, "utf8");
}

buildHtml();
console.log(`Wrote ${htmlPath}`);
