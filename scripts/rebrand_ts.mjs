#!/usr/bin/env node
// Brand string literals in TypeScript / JavaScript sources — the TS half of
// scripts/rebrand.py, which drives it. Reads {files, pattern, agentName,
// legacySymbol, symbol, keepMarker, write} as JSON on stdin and prints the
// paths it changed (or would change), one per line.
//
// Only literal text is touched: string literals, template literal chunks and
// JSX text. Identifiers, comments and import paths are never rewritten, so a
// `hermes` module stays `hermes` while the `'Hermes'` a person reads changes.
import { readFileSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
let ts
try {
  ts = require('typescript')
} catch {
  process.stderr.write('typescript is not installed (npm ci at the repo root)\n')
  process.exit(3)
}

const input = JSON.parse(readFileSync(0, 'utf8'))
const brand = new RegExp(input.pattern, 'g')
const symbol = new RegExp(input.legacySymbol, 'g')
const rebrandText = text => text.replace(brand, input.agentName).replace(symbol, input.symbol)

const KINDS = {
  cjs: ts.ScriptKind.JS,
  cts: ts.ScriptKind.TS,
  js: ts.ScriptKind.JS,
  jsx: ts.ScriptKind.JSX,
  mjs: ts.ScriptKind.JS,
  mts: ts.ScriptKind.TS,
  ts: ts.ScriptKind.TS,
  tsx: ts.ScriptKind.TSX
}

function isTextNode(node) {
  return (
    ts.isStringLiteral(node) ||
    ts.isNoSubstitutionTemplateLiteral(node) ||
    ts.isTemplateHead(node) ||
    ts.isTemplateMiddle(node) ||
    ts.isTemplateTail(node) ||
    ts.isJsxText(node)
  )
}

/** Lines inside `keep-start` / `keep-end` blocks plus lines carrying the marker. */
function keptLines(lines, marker) {
  const kept = new Set()
  let inBlock = false
  lines.forEach((line, index) => {
    if (line.includes(`${marker}-start`)) inBlock = true
    if (inBlock || line.includes(marker)) kept.add(index)
    if (line.includes(`${marker}-end`)) inBlock = false
  })
  return kept
}

const parseErrors = (file, text, kind) =>
  ts.createSourceFile(file, text, ts.ScriptTarget.Latest, false, kind).parseDiagnostics?.length ?? 0

function rebrandSource(file, text) {
  const ext = file.slice(file.lastIndexOf('.') + 1)
  const kind = KINDS[ext] ?? ts.ScriptKind.TS
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, kind)
  const kept = keptLines(text.split('\n'), input.keepMarker)
  const spans = []
  const visit = node => {
    if (isTextNode(node)) {
      const start = node.getStart(sf)
      const { line } = sf.getLineAndCharacterOfPosition(start)
      if (!kept.has(line) && !kept.has(line - 1)) spans.push([start, node.getEnd()])
    }
    ts.forEachChild(node, visit)
  }
  visit(sf)
  let out = text
  for (const [start, end] of spans.sort((a, b) => b[0] - a[0])) {
    out = out.slice(0, start) + rebrandText(out.slice(start, end)) + out.slice(end)
  }
  if (out !== text && parseErrors(file, out, kind) > parseErrors(file, text, kind)) {
    process.stderr.write(`skipped ${file}: the rewrite would not parse\n`)
    return text
  }
  return out
}

for (const file of input.files) {
  const text = readFileSync(file, 'utf8')
  const out = rebrandSource(file, text)
  if (out !== text) {
    if (input.write) writeFileSync(file, out)
    process.stdout.write(`${file}\n`)
  }
}
