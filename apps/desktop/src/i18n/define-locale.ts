import { brandCatalog } from '@hermes/shared/brand'
import { mergeTranslations, type TranslationOverride } from '@hermes/shared/i18n'

import { en } from './en'
import type { Translations } from './types'

export type TranslationOverrides = TranslationOverride<Translations>

// Branded as it loads, like `en`: direct importers of a locale see the same text as TRANSLATIONS.
export const defineLocale = (overrides: TranslationOverrides): Translations =>
  brandCatalog(mergeTranslations<Translations>(en, overrides))
