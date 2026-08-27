#!/usr/bin/env node
/**
 * name: contrast_checker.js
 * description: CLI tool to check WCAG 2.1 color contrast ratios between two HEX colors.
 *              Reports pass/fail for AA and AAA standards (Normal Text, Large Text, UI Components).
 *              No npm dependencies required — runs with the built-in Node.js runtime.
 *
 * Usage:
 *   node contrast_checker.js <background-hex> <foreground-hex>
 *
 * Examples:
 *   node contrast_checker.js "#0f0f1a" "#e2e8f0"
 *   node contrast_checker.js 1a1a2e F1F5F9
 */

// ── ANSI Color Codes (terminal output styling) ─────────────────────────────
const COLOR = {
  reset:  '\x1b[0m',
  bold:   '\x1b[1m',
  green:  '\x1b[32m',
  red:    '\x1b[31m',
  yellow: '\x1b[33m',
  cyan:   '\x1b[36m',
  gray:   '\x1b[90m',
  white:  '\x1b[97m',
};

// ── Core Calculation Functions ─────────────────────────────────────────────

/**
 * Convert a HEX color string to an RGB tuple.
 *
 * @param {string} hex - e.g. "#4F46E5" or "4F46E5"
 * @returns {{ r: number, g: number, b: number }}
 * @throws {Error} If the hex string is not a valid 6-digit color code.
 */
function hexToRgb(hex) {
  const clean = hex.replace(/^#/, '').trim();
  if (!/^[0-9A-Fa-f]{6}$/.test(clean)) {
    throw new Error(`Invalid HEX color: "${hex}". Expected format: #RRGGBB or RRGGBB`);
  }
  return {
    r: parseInt(clean.substring(0, 2), 16),
    g: parseInt(clean.substring(2, 4), 16),
    b: parseInt(clean.substring(4, 6), 16),
  };
}

/**
 * Compute the relative luminance of an sRGB color per WCAG 2.1 spec.
 * Reference: https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
 *
 * @param {number} r - Red channel 0–255
 * @param {number} g - Green channel 0–255
 * @param {number} b - Blue channel 0–255
 * @returns {number} Luminance in range [0, 1]
 */
function relativeLuminance(r, g, b) {
  const linearize = (c) => {
    const s = c / 255;
    return s <= 0.04045 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b);
}

/**
 * Compute the contrast ratio between two relative luminance values.
 * Formula: (L_lighter + 0.05) / (L_darker + 0.05)
 *
 * @param {number} l1 - Luminance of color 1
 * @param {number} l2 - Luminance of color 2
 * @returns {number} Contrast ratio (always >= 1)
 */
function contrastRatio(l1, l2) {
  const lighter = Math.max(l1, l2);
  const darker  = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

// ── Report Formatting ──────────────────────────────────────────────────────

/**
 * Format a single WCAG criterion row as a terminal string.
 *
 * @param {string} label       - Criterion name (e.g. "Normal Text — AA")
 * @param {string} description - Context note (e.g. "Body text < 18px")
 * @param {number} ratio       - Computed contrast ratio
 * @param {number} threshold   - Minimum required ratio for this criterion
 * @returns {string} Formatted line with PASS/FAIL badge and color
 */
function formatRow(label, description, ratio, threshold) {
  const pass   = ratio >= threshold;
  const badge  = pass
    ? `${COLOR.green}${COLOR.bold}✓ PASS${COLOR.reset}`
    : `${COLOR.red}${COLOR.bold}✗ FAIL${COLOR.reset}`;
  const req    = `${COLOR.gray}(requires ≥ ${threshold}:1)${COLOR.reset}`;
  const desc   = `${COLOR.gray}${description}${COLOR.reset}`;

  return [
    `  ${badge}  ${COLOR.white}${label.padEnd(30)}${COLOR.reset} ${req}`,
    `         ${desc}`,
  ].join('\n');
}

// ── Main Execution ─────────────────────────────────────────────────────────

/**
 * Entry point: parses CLI args, runs the contrast check, and prints a report.
 *
 * @returns {void}
 */
function main() {
  const args = process.argv.slice(2);

  if (args.length < 2 || args.includes('--help') || args.includes('-h')) {
    console.log(`
${COLOR.bold}${COLOR.cyan}WCAG 2.1 Contrast Checker${COLOR.reset}
${COLOR.gray}UX/UI Skill Tool — no npm install required${COLOR.reset}

${COLOR.bold}Usage:${COLOR.reset}
  node contrast_checker.js <background> <foreground>

${COLOR.bold}Arguments:${COLOR.reset}
  background   Background HEX color  (e.g. "#0F0F1A" or "0F0F1A")
  foreground   Foreground HEX color  (e.g. "#E2E8F0" or "E2E8F0")

${COLOR.bold}Examples:${COLOR.reset}
  node contrast_checker.js "#0f0f1a" "#e2e8f0"
  node contrast_checker.js 1a1a2e F1F5F9

${COLOR.bold}WCAG 2.1 Thresholds:${COLOR.reset}
  Normal Text  AA  ≥ 4.5:1   Body text < 18px regular or < 14px bold
  Large Text   AA  ≥ 3.0:1   Headings ≥ 18px regular or ≥ 14px bold
  Normal Text  AAA ≥ 7.0:1   Enhanced — stricter accessibility
  UI Components AA ≥ 3.0:1   Buttons, icons, focus indicators
    `);
    process.exit(0);
  }

  // Parse inputs
  let bgRgb, fgRgb;
  try {
    bgRgb = hexToRgb(args[0]);
    fgRgb = hexToRgb(args[1]);
  } catch (err) {
    console.error(`${COLOR.red}${COLOR.bold}Error:${COLOR.reset} ${err.message}`);
    process.exit(1);
  }

  // Compute luminance & ratio
  const bgL   = relativeLuminance(bgRgb.r, bgRgb.g, bgRgb.b);
  const fgL   = relativeLuminance(fgRgb.r, fgRgb.g, fgRgb.b);
  const ratio = contrastRatio(bgL, fgL);

  // Determine overall grade
  const ratioDisplay = ratio.toFixed(2);
  const overallColor = ratio >= 7 ? COLOR.green : ratio >= 4.5 ? COLOR.yellow : COLOR.red;

  // Print report
  console.log(`
${COLOR.bold}${COLOR.cyan}━━━ WCAG 2.1 Contrast Report ━━━━━━━━━━━━━━━━━━━━━━━━${COLOR.reset}

  ${COLOR.gray}Background:${COLOR.reset}  ${COLOR.white}${args[0].toUpperCase()}${COLOR.reset}
  ${COLOR.gray}Foreground:${COLOR.reset}  ${COLOR.white}${args[1].toUpperCase()}${COLOR.reset}

  ${COLOR.bold}Contrast Ratio:  ${overallColor}${ratioDisplay}:1${COLOR.reset}

${COLOR.bold}${COLOR.cyan}━━━ Results ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR.reset}
`);

  console.log(formatRow(
    'Normal Text — AA',
    'Body text < 18px regular, or < 14px bold',
    ratio, 4.5
  ));
  console.log();
  console.log(formatRow(
    'Large Text — AA',
    'Headings ≥ 18px regular, or ≥ 14px bold',
    ratio, 3.0
  ));
  console.log();
  console.log(formatRow(
    'Normal Text — AAA',
    'Enhanced accessibility target for body text',
    ratio, 7.0
  ));
  console.log();
  console.log(formatRow(
    'UI Components — AA',
    'Buttons, icons, borders, focus indicators',
    ratio, 3.0
  ));

  console.log(`
${COLOR.bold}${COLOR.cyan}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR.reset}
${COLOR.gray}Reference: WCAG 2.1 SC 1.4.3 (AA) & SC 1.4.6 (AAA)${COLOR.reset}
`);

  // Exit with error code if fails the minimum AA for normal text
  process.exit(ratio >= 4.5 ? 0 : 1);
}

main();
