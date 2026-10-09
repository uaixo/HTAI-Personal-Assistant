import { describe, expect, it } from 'vitest'

import { AGENT_NAME, brandCatalog, brandText, SYMBOL } from './brand'

describe('brandText', () => {
  it('replaces the upstream product name and glyph in prose', () => {
    expect(brandText('Welcome to Hermes Agent!')).toBe(`Welcome to ${AGENT_NAME}!`)
    expect(brandText('Hermes is working on 2 chats.')).toBe(`${AGENT_NAME} is working on 2 chats.`)
    expect(brandText("Hermes' home, (Hermes)")).toBe(`${AGENT_NAME}'s home, (${AGENT_NAME})`)
    expect(brandText("Hermes’ own bot; the 'Hermes' skill; 'Run Hermes' now")).toBe(
      `${AGENT_NAME}’s own bot; the '${AGENT_NAME}' skill; 'Run ${AGENT_NAME}' now`
    )
    expect(brandText('/Applications/Hermes.app and Hermes.exe')).toBe(
      `/Applications/${AGENT_NAME}.app and ${AGENT_NAME}.exe`
    )
    expect(brandText('☤ Starting Hermes update…')).toBe(`${SYMBOL} Starting ${AGENT_NAME} update…`)
    expect(brandText('Hermes Agent v0.18.2')).toBe(`${AGENT_NAME} v0.18.2`)
  })

  it('leaves identifiers, URLs and the Hermes model family alone', () => {
    for (const text of [
      'hermes doctor',
      '~/.hermes/config.yaml',
      'HERMES_HOME',
      'hermes://open',
      'X-Hermes-Session-Token',
      'Hermes-Setup.exe',
      'NousResearch.Hermes',
      'OpenHermes-2.5',
      'HermesE2E-1',
      'hermes-agent.nousresearch.com',
      'Hermes 4',
      'Hermes 3 & 4 models',
      'Hermes-3-Llama-3.1-70B'
    ]) {
      expect(brandText(text)).toBe(text)
    }
  })

  it('is idempotent', () => {
    const once = brandText('☤ Hermes Agent: Hermes, HermesCLI, hermes update, Hermes 4')

    expect(brandText(once)).toBe(once)
    expect(once).not.toContain('Hermes Agent')
    expect(once).toContain('HermesCLI')
  })
})

describe('brandCatalog', () => {
  it('brands string leaves, function results, arrays and nested records', () => {
    const catalog = {
      title: 'Hermes Agent',
      nested: { body: (name: string) => `Hermes can use ${name}`, count: (n: number) => n },
      list: ['Ask Hermes', 'Hermes 4'],
      flag: true
    }

    const branded = brandCatalog(catalog)

    expect(branded.title).toBe(AGENT_NAME)
    expect(branded.nested.body('Slack')).toBe(`${AGENT_NAME} can use Slack`)
    expect(branded.nested.count(3)).toBe(3)
    expect(branded.list).toEqual([`Ask ${AGENT_NAME}`, 'Hermes 4'])
    expect(branded.flag).toBe(true)
    expect(catalog.title).toBe('Hermes Agent')
  })
})
