// Product brand for user-facing text — the TypeScript mirror of `hermes_brand.py`
// (keep the two in step). `AGENT_NAME` is what a person reads; internal
// identifiers (`hermes` command, `HERMES_*` variables, `hermes://` links, HTTP
// headers) keep their upstream names so merges from upstream stay cheap.
//
// The bundled catalogs are branded as they load (`brandCatalog`); the backend
// brands the YAML packs it serves; `scripts/rebrand.py` brands literals at rest.

export const AGENT_NAME = 'NousAI'
export const VENDOR = 'Nous Research'
/** Glyph that marks the agent in response labels and short notices. */
export const SYMBOL = '✦'

// Same rule as `hermes_brand._LEGACY_BRAND`: word-bounded on both sides so
// identifiers (`X-Hermes-Token`, `Hermes-Setup.exe`, `NousResearch.Hermes`,
// `OpenHermes`) and the Hermes model family (`Hermes 4`) are left alone, while
// `Hermes.app` / `Hermes.exe` follow the product name.
// In source literals the name may follow an escape sequence (`"...\nHermes"`):
// the `\n` is whitespace once the string is read, so it counts as a boundary.
const LEGACY_BRAND = /(?:(?<![A-Za-z0-9_.-])|(?<=\\[ntr]))Hermes(?: Agent)?(?![A-Za-z0-9_-])(?! \d)/g
// `Hermes' tool store` -> `NousAI's tool store`; the closing quote of `'Hermes'`
// (opened by the quote before the name) never qualifies.
const LEGACY_POSSESSIVE = /(?<!['’])(?:(?<![A-Za-z0-9_.-])|(?<=\\[ntr]))Hermes(?: Agent)?(['’])(?= [A-Za-z])/g
const LEGACY_SYMBOL = /☤/g

/** `NousAI's` for a possessive; untouched when the apostrophe closes a quote
 *  opened earlier on the line (`'Run Hermes' now`), which the brand rule then
 *  handles as a plain name. */
function possessive(match: string, apostrophe: string, offset: number, whole: string): string {
  const lineStart = whole.lastIndexOf('\n', offset) + 1
  const quotesBefore = whole.slice(lineStart, offset).split(apostrophe).length - 1

  return quotesBefore % 2 === 1 ? match : `${AGENT_NAME}${apostrophe}s`
}

/** `text` with every upstream product name and glyph replaced by the brand. Idempotent. */
export function brandText(text: string): string {
  return text.replace(LEGACY_POSSESSIVE, possessive).replace(LEGACY_BRAND, AGENT_NAME).replace(LEGACY_SYMBOL, SYMBOL)
}

type Leaf = (...args: unknown[]) => unknown

/**
 * Deep copy of a translation tree with every string leaf branded. Function
 * leaves are wrapped so their string results are branded too; arrays and
 * nested records recurse; anything else passes through untouched.
 */
export function brandCatalog<T>(tree: T): T {
  if (typeof tree === 'string') {
    return brandText(tree) as T
  }

  if (typeof tree === 'function') {
    const leaf = tree as unknown as Leaf

    return ((...args: unknown[]) => {
      const out = leaf(...args)

      return typeof out === 'string' ? brandText(out) : out
    }) as T
  }

  if (Array.isArray(tree)) {
    return tree.map(item => brandCatalog(item)) as T
  }

  if (tree !== null && typeof tree === 'object') {
    const out: Record<string, unknown> = {}

    for (const [key, value] of Object.entries(tree as Record<string, unknown>)) {
      out[key] = brandCatalog(value)
    }

    return out as T
  }

  return tree
}
