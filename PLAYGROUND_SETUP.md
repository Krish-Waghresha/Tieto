# Run the Invoice Review Playground

This guide is for the interactive **INV-BULK-26 bulk invoice import** playground on the `demo/attention-first` branch.

It is not the older order-pricing example or the earlier MessagePack/React demo.

## Open the Correct Playground Now

On the current development machine, the correct server is already running on **127.0.0.1:5174**. Another app is listening on port **5173**; that is not the invoice playground server.

Open the current PR-linked page:

<http://127.0.0.1:5174/pr-3/2580ea6aef6ec30eafd760d558192e9fb2489051d0206493ce43add9f1a8fcfe/index.html>

On macOS, the equivalent command is:

```sh
open "http://127.0.0.1:5174/pr-3/2580ea6aef6ec30eafd760d558192e9fb2489051d0206493ce43add9f1a8fcfe/index.html"
```

Use the complete URL, not just `http://127.0.0.1:5174/`. The root serves a directory listing containing different generated reviews.

### Confirm You Have the Right Version

- PR-linked title: **INV-BULK-26: bulk invoice import #3**.
- Change summary: **1,618 added lines / 15 files / 25 changed methods**.
- Ten module nodes, including `DuplicatePolicy`, `BatchReconciler`, and `RetryingInvoiceWriter`.
- Orange cards say **Hallucination risk**.
- The red retry card's **Understand** view has **Simulation**, **Listen to your code**, and **Take a quiz** tabs.
- The quiz has six questions; the audio is approximately 1 minute 42 seconds.
- **Overall sign-off** has one acknowledgment and **Continue to GitHub**, not a username or local approval form.

## Start the Server If It Is Not Running

From the active implementation worktree:

```sh
cd /Users/krish/Junction26/teito-attention-first/classifier
npm run playground:serve
```

Keep this terminal running. Open the full PR-linked URL above in the browser.

The serve command is equivalent to:

```sh
python3 -m http.server 5174 --bind 127.0.0.1 --directory out/playground
```

It serves files already built under `classifier/out/playground/`. It does not build, classify, or watch for changes.

## Refresh the Current PR-Linked UI

Use this after changes to the web UI, quiz, or narration. Run it in a second terminal while the server continues running:

```sh
cd /Users/krish/Junction26/teito-attention-first/classifier
node web/build.mjs out/invoice-import/playground.json out/playground/pr-3/2580ea6aef6ec30eafd760d558192e9fb2489051d0206493ce43add9f1a8fcfe/index.html
```

Then reload the browser. There is no automatic hot reload.

This command needs the existing generated `out/invoice-import/playground.json` and an authenticated GitHub CLI account with access to the private demo repository. It reads PR metadata to verify the source revision; it does not post comments or modify the PR.

Check authentication if needed:

```sh
gh auth status
```

If the build reports that the PR revision differs from the analysis, do not bypass the check or manually substitute commit hashes. Regenerate the PR-bound analysis through the intentional GitHub publication workflow, or use the standalone invoice setup below.

The long PR URL identifies the current analysis. If a later publication creates a new PR number or review key, use the new link produced by that workflow.

## Fresh Setup: Invoice Playground Without GitHub Authentication

Use this on another machine, or when the generated PR-bound files are missing. Generated output is not committed to Git.

### Requirements

- Node.js and npm; Node.js 22 or later is a practical choice.
- Python 3.
- .NET 8 SDK and runtime, or a compatible installation that can build and run the `net8.0` projects.
- Network access for the first npm and NuGet dependency restore.

Clone the implementation branch into a new directory:

```sh
git clone --branch demo/attention-first https://github.com/Krish-Waghresha/teito.git teito-demo
cd teito-demo/classifier
```

If already cloned, enter its `classifier` directory instead. Do not clone over an existing worktree.

Install dependencies, generate the invoice analysis, and build a stable local URL:

```sh
npm ci
npm run demo:invoice
node web/build.mjs out/invoice-import/analysis.json out/playground/invoice/index.html
npm run playground:serve
```

Open:

<http://127.0.0.1:5174/invoice/index.html>

This is the same invoice review experience without the GitHub PR header/binding. Its final handoff offers **Copy review** instead of **Continue to GitHub**. The header uses the invoice requirement title, not a PR number.

The invoice fixture should report **87 passing checks and one intentional retry-integrity failure**. That failure is the red-card counterexample, not a failed setup. Unexpected failures cause the runner to stop.

### .NET on This Development Machine

The runner automatically uses the isolated installation at:

```text
~/.local/share/teito-tooling/dotnet/dotnet
```

Otherwise, it uses `DOTNET_PATH` when set, or `dotnet` on `PATH`. To select a specific installation:

```sh
export DOTNET_PATH="$HOME/.local/share/teito-tooling/dotnet/dotnet"
npm run demo:invoice
```

Only use that path on a machine where the installation exists.

### Refresh the Standalone UI

After UI-only changes, reuse the existing invoice analysis:

```sh
node web/build.mjs out/invoice-import/analysis.json out/playground/invoice/index.html
```

Reload `/invoice/index.html`. If the fixture source or requirements changed, rerun `npm run demo:invoice` first. Its evidence bindings may require review; do not silently replace them to make a changed fixture pass.

## Commands That Select the Older Example

Do not use these to launch or verify the invoice demo:

| Command or location | What it selects |
| --- | --- |
| `npm run demo` | The older order-flow classification and graph. |
| `npm run build` with no input arguments | `out/analysis.json` -> `out/graph.html`, the older default graph. |
| `npm run test:browser` | The older order-flow browser test. |
| `npm run github:watch` | The older order PR watcher; it can publish to GitHub. |
| Port `5173` on this machine | The separate earlier app, not the invoice file server. |
| `out/graph.html` or `/pr-2/...` | The older order-flow review. |

Always give `web/build.mjs` the invoice input and explicit output path shown in this guide.

## Troubleshooting

### Address Already in Use

Inspect the listener:

```sh
lsof -nP -iTCP:5174 -sTCP:LISTEN
```

If it is the existing invoice server, reuse it. Do not start a second server or kill unrelated processes.

If another application owns the port, use a different port:

```sh
python3 -m http.server 5175 --bind 127.0.0.1 --directory out/playground
```

Replace `5174` with `5175` in the complete invoice URL. Previously published local links will still point to 5174.

### Directory Listing or 404

- Open the complete page URL, including `/index.html`.
- Start the server from `classifier`, so `out/playground` resolves to the right directory.
- Rebuild the matching output file. Building `out/invoice-import/preview.html` alone does not update the served PR-linked page.
- If the PR-bound input is absent, follow the standalone setup instead of guessing a hashed URL.

### UI Still Looks Old

- Check the port and the page title first.
- Rebuild the exact HTML file corresponding to the URL you opened.
- Reload the browser; the server does not rebuild automatically.
- Saved clarification answers and walkthrough progress can change the displayed state. They are not evidence of an old build. Do not clear all browser storage merely to refresh the UI.

### GitHub Link Shows 404

The demo repository is private. The browser must be signed into an account with repository access. CLI authentication and browser authentication are separate. A working local playground does not grant GitHub access.

### Audio or API Keys

The current playground does not need an ElevenLabs or Gemini API key to open or run. On macOS, the build generates and embeds narration using the local `say` command; other platforms retain the transcript if audio generation is unavailable.

ElevenLabs setup is for the separate video-production workflow. Keep its key in the ignored root environment file, never in browser assets or committed setup instructions.

## Verify the Invoice Playground

From `classifier`, install the test browser once:

```sh
npx playwright install chromium
```

For the current PR-linked page:

```sh
node web/check-invoice.mjs "http://127.0.0.1:5174/pr-3/2580ea6aef6ec30eafd760d558192e9fb2489051d0206493ce43add9f1a8fcfe/index.html"
```

For the standalone route after building it:

```sh
node web/check-invoice.mjs "http://127.0.0.1:5174/invoice/index.html"
```

## GitHub Publication Is a Separate Action

`python3 github_demo.py --invoice` creates or updates the private demo PR and its generated playground link. **It writes to GitHub.** Do not run it just to open the existing playground.

For publishing details, see [classifier/README.md](classifier/README.md). The local serve and explicit build commands above are sufficient for normal UI work.