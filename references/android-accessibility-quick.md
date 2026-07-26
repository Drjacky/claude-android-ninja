# Android accessibility (quick)

Full guide: [android-accessibility.md](android-accessibility.md) (~1570 lines). Section anchors: [INDEX-sections.md](INDEX-sections.md#android-accessibilitymd-1571-lines).

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
| Hide a field from a11y services | [Hiding sensitive fields](android-accessibility.md#hiding-sensitive-fields-from-accessibility-services) |
| Contrast, color-only cues | [Color & Visual Accessibility](android-accessibility.md#color--visual-accessibility) |
| Focus order, keyboard | [Focus Management](android-accessibility.md#focus-management) |
| Tabs, lists, forms, dialogs | [Common Patterns](android-accessibility.md#common-patterns) |
| TalkBack, Espresso, checks | [Testing Accessibility](android-accessibility.md#testing-accessibility) |

## Hard rules (summary)

**Required:**

- Concise labels (purpose, not "button" / "tap here").
- `mergeDescendants` to group related content; `stateDescription` for state changes.
- `traversalIndex` requires an ancestor with `isTraversalGroup = true`, otherwise it is a silent no-op.
- `semantics { sensitiveData = true }` on sensitive fields (card number, OTP, balance) - `FLAG_SECURE` does not hide node text.
- Support dark mode and high contrast.

**Forbidden:**

- Touch targets smaller than 48dp.
- `contentDescription` on purely decorative images.
- Ignoring form validation error announcements.
- Hardcoded user-visible strings in semantics.
- `traversalIndex` used to compensate for a layout whose visual order differs from composition order - fix the layout.
- Marking a whole screen `sensitiveData` - it breaks screen readers for the entire flow.

Open the full file for WCAG tables, code samples, and Espresso patterns.
