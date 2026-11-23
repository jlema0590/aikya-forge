# Forge console settings and flow sidebar

Open `/aikya-settings` or press F2 in the interactive terminal. This is a local
administrative panel; opening it does not prompt a model. Its sections are
Providers, Appearance, Sidebar and Flow. Headless/RPC sessions report that an
interactive terminal is required and do not write preferences.

## Providers

Choose a provider from the pinned local catalog. Anthropic and OpenAI Codex appear
first. Connect using the API-key/OAuth methods supported by that provider, choose
a catalog model for the next launch, remove stored credentials, or clear the saved
selection. Provider metadata marked configured is not a successful remote inference.
Dynamic catalog downloads and arbitrary endpoint registration are outside this panel.

API keys use masked input and stay out of command arguments, custom messages and
model context. The existing project-local ModelRuntime credential store owns
`.aikya/pi/agent/auth.json`; this is filesystem storage, not an encrypted keychain.
OAuth opens its provider-owned sign-in flow only after the operator chooses Connect.
Disconnect removes the local stored credential; environment credentials remain
outside that operation. Authentication does not select or invoke a model by itself.

The next-launch provider/model selection is stored without credentials. Explicit
`--provider`/`--model` arguments take precedence. A saved selection only enables the
controlled runtime when the existing budget reports available. Unknown/exhausted or
unconfigured budgets retain the local preview and existing counters. Session model
bindings remain fixed; switching provider does not rewrite a live task/checkpoint.

## Appearance and layout

The `aikya` theme is the original Aikya identity for new projects. Explicit
existing dark/light/inherit preferences and legacy theme.json are retained. The
startup header draws the fixed Aikya wordmark with pyfiglet 1.0.4 slant/small
ASCII fonts, selecting an entire variant that fits. The original PNG remains the
color reference. The verified Python helper runs once per interpreter per process
with a 3-second deadline, 8-KiB response bound and no shell/provider call. Repaints
reuse the result. Missing dependencies or narrow widths use plain text. Native
payloads include fonts/license; source installs use `.[terminal]`. Use
`/aikya-theme aikya` to preview/select the palette.

Choose dark/light, accent/text/muted/background HEX colors, and normal/bold/italic
ANSI text style. Settings are applied locally and retained in
`.aikya/pi/console.json`. Theme choices and the compatible `/aikya-theme` command
share that authoritative preference. The previous theme.json is read as a legacy
fallback; new settings do not require a second theme file.

Reset colors restores the installed palette. The light appearance paints its own
readable background even on a dark terminal. Font family and point size belong to
the terminal emulator: Forge explains this boundary rather than claiming to change
Terminal, iTerm, Windows Terminal or another application's font configuration.

At 110 columns or wider, a real right column reserves space beside the transcript,
editor and dialogs. It does not overlay conversation text. Narrow terminals retain
the full-width editor and a compact flow summary; `/aikya-tokens` remains available.
The sidebar can be hidden. F2 and the command remain available independently.

## Flow and consumption

The sidebar shows the current English phase, running/idle state, selected model,
local project tokens/calls, budget percentage, estimated context percentage and
recorded token attribution for Claude/Codex and author/reviewer roles.

These percentages have different denominators: budget percentage uses the approved
project token cap; agent shares use all known recorded project tokens; context is
the SDK's estimate. Missing/truncated/uncertain attribution is marked partial and
does not produce a complete share percentage. The project ledger is cumulative,
not a new session or daily subscription limit.

Claude and Codex account quota windows are shown only when the actual provider
response supplies the recognized headers. The UI labels the source, age and stale
observations. Missing quota stays unavailable. There is no account scraping,
personal-client credential import, fabricated weekly percentage or token-to-quota
conversion. Current response observations are not persisted as a fresh quota after
restart. Periodic repaint uses cached local data and performs no inference.

Settings/Flow/Stop controls are shown in the right column; click handling is available
when the terminal delivers mouse events. Keyboard access remains through F2 and
`/aikya-settings`. Flow provides status, stop, current-response cancellation and
local usage refresh. Stop reuses the existing host task lifecycle. No unverified
pause/resume capability or automatic task start is introduced.

The right sidebar’s Project & Git block identifies the project directory, observed
Git branch and
`git config user.name`. Email and remotes are not displayed. Branch changes reuse
the SDK cache/watch; repainting runs no Git commands. User identity is read once
at session start; missing Git/configuration is shown explicitly as unavailable.
Narrow terminals retain project/Git fields in the compact summary below the transcript.

## Claude and Codex metrics

Each provider block shows Context, Tokens, Usage 5h and Usage 7d. Context belongs
only to the active SDK provider session and is labeled estimated. A reviewer has
an independent session; its context is not inferred or copied from the author.
Tokens use the existing project ledger, including its input/output/cache count
policy and role/provider grouping. Incomplete/truncated attribution stays partial.
Project-share percentages have a project-total denominator, not an account quota.

Quota slots select durations of exactly 18000 and 604800 seconds from recognized
response headers. They do not assume primary means 5h or secondary means 7d.
Missing, ambiguous or invalid slots remain unavailable; known zero is preserved.
Observations carry source/age/stale labels, including a reset that has already
passed. No account polling, credential import or inference fills missing fields.

Aikya local budget is the project execution guard for configured token/call maxima.
It is not an account balance, monetary budget or provider subscription meter.

GENERATED BY AIKYA HARNESS
