# Android accessibility (quick)

Full guide: [android-accessibility.md](android-accessibility.md) (~1530 lines). Section anchors: [INDEX-sections.md](INDEX-sections.md#android-accessibilitymd-1534-lines).

Required before shipping interactive Compose UI:

- `contentDescription` on every icon and meaningful image; `null` only when an adjacent label already conveys the action.
- 48dp x 48dp minimum touch targets; do not rely on color alone.
- String resources for all user-visible accessibility text - [android-i18n.md](android-i18n.md).
- Test with TalkBack (and Espresso a11y checks for critical flows).

## Section routing

| Task | Open |
|------|------|
| WCAG 2.2 on Compose | [WCAG 2.2 Criteria That Apply Here](android-accessibility.md#wcag-22-criteria-that-apply-here) |
| `contentDescription`, roles, custom actions | [Semantic Properties](android-accessibility.md#semantic-properties) |
| 48dp targets, spacing | [Touch Target Sizes](android-accessibility.md#touch-target-sizes) |
| Traversal order, headings, live regions | [Screen Reader Navigation](android-accessibility.md#screen-reader-navigation) |
| Contrast, color-only cues | [Color & Visual Accessibility](android-accessibility.md#color-visual-accessibility) |
| Focus order, keyboard | [Focus Management](android-accessibility.md#focus-management) |
| Tabs, lists, forms, dialogs | [Common Patterns](android-accessibility.md#common-patterns) |
| TalkBack, Espresso, checks | [Testing Accessibility](android-accessibility.md#testing-accessibility) |

## Hard rules (summary)

**Required:**

- Concise labels (purpose, not "button" / "tap here").
- `mergeDescendants` to group related content; `stateDescription` for state changes.
- Support dark mode and high contrast.

**Forbidden:**

- Touch targets smaller than 48dp.
- `contentDescription` on purely decorative images.
- Ignoring form validation error announcements.
- Hardcoded user-visible strings in semantics.

Open the full file for WCAG tables, code samples, and Espresso patterns.
