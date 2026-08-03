import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

import { describe, expect, it } from 'vitest'

// Contract: the document title carries BOTH brand tokens, and each is load-bearing
// for a different reason:
//
//   'NousAI' — this fork's product name. Nothing else asserts it. The desktop E2E
//     suite that exercises the real window title only checks for 'Hermes', so a
//     sync that reverted the title to plain `<title>Hermes</title>` would pass
//     every other check in the repo. This test is the guard against that.
//   'Hermes' — upstream's e2e/boot.spec.ts asserts `title.toContain('Hermes')`.
//     Dropping the word to make the title purely NousAI would break that spec the
//     next time the Desktop E2E job runs (it is disabled upstream as of Aug 2026,
//     so the breakage would surface late, on whichever sync re-enables it).
//
// Both tokens live in an upstream-owned file we deliberately diverge on, which is
// exactly the kind of line an upstream merge can quietly rewrite — hence a unit
// test in an always-on lane rather than relying on the E2E suite.
const INDEX_HTML = join(dirname(fileURLToPath(import.meta.url)), '..', 'index.html')

describe('desktop brand identity', () => {
  const title = readFileSync(INDEX_HTML, 'utf8').match(/<title>([^<]*)<\/title>/)?.[1]

  it('index.html declares a document title', () => {
    expect(title).toBeDefined()
  })

  it('names the fork so the product brand cannot be silently reverted', () => {
    expect(title).toContain('NousAI')
  })

  it("keeps 'Hermes', which upstream's boot e2e spec asserts on the window title", () => {
    expect(title).toContain('Hermes')
  })
})
