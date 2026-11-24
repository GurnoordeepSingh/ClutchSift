# Shorts research: what should we optimize?

Do not assert a universal perfect clip length, hook formula, or guaranteed viral algorithm. Gaming audience preferences vary by game, channel, language and personality. Use platform-available real metrics and controlled creator testing.

## What official YouTube metrics actually expose

YouTube Studio Shorts analytics reports **how many chose to view** versus swiped away, and related retention/engagement measures. A published clip can still do poorly even if an LLM declares it high potential. Source: https://support.google.com/youtube/answer/12942217?co=YOUTUBE._YTVideoType%3Dshorts&hl=en

## Proposed editorial features to test

1. **Immediate context:** does a new viewer understand what's happening without watching three minutes of build-up?
2. **Setup + payoff:** don't start right at the loud explosion; include enough lead-in and reaction so the moment makes sense.
3. **Remove dead time carefully:** silence isn't always dead time—quiet tension can be the most important part of a funny/horror reveal.
4. **Readability:** dynamic, editable captions should not obscure gameplay HUD or platform UI. Test on actual phone screens.
5. **Preserve the frame:** default full-gameplay on blurred vertical canvas; use cropping only when the subject remains visible.
6. **No redundant clips:** make several genuinely different suggestions, not five overlapping slices of the same event.
7. **Grounded packaging:** titles and descriptions must match footage. Do not hallucinate kills, celebrities, challenge results, or game names.
8. **Review + feedback:** allow creators to accept/reject a candidate and note why; use their own accepted edits to adjust heuristic weights later.

## Controlled experiment

For each game, compare: audio-only vs hybrid vs hybrid+future semantic VLM. Blind-review 5 candidates per one-hour recording. Record `usable`, `reason_rejected`, `start_adjustment_seconds`, `end_adjustment_seconds`, `time_saved_minutes`. If the creator publishes, optional manually provided `chose_to_view`, `average_percentage_viewed`, and `retention` at a fixed time after publishing. **Do not scrape private analytics or upload without explicit authorization.**

Expected outcome is knowledge about editing utility, **not** a promise to go viral. The north-star early metric is **creator-approved clips per recording hour**, not views before the product has users.
