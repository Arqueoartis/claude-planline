# claude-planline

Tiny cute statusLine helper for Claude Code.

It shows a compact 5-hour plan meter and, when Claude Code exposes it, monthly usage credits:

```text
(•‿•) 5h [██░░░░░░░░] 18% used · left 82% · reset 03:42
($‿$) extra [████████░░] €25.14/€30 month · reset Jul 1
```

No cookies. No login. No private endpoints. No telemetry.

`claude-planline` only reads the JSON that Claude Code passes to its official `statusLine` command.

## Español

Utilidad minima y cute para la `statusLine` de Claude Code.

Muestra el uso de la ventana de 5 horas y, si Claude Code lo expone en el JSON de `statusLine`, los creditos mensuales de uso extra:

```text
(•‿•) 5h [██░░░░░░░░] 18% usado · queda 82% · reset 03:42
($‿$) extra [████████░░] €25.14/€30 mes · reset Jul 1
```

Sin cookies. Sin login. Sin endpoints privados. Sin telemetria.

`claude-planline` solo lee el JSON que Claude Code entrega al comando oficial `statusLine`.

## Install

### Option A: run from a cloned repo, no package install

```bash
git clone https://github.com/Arqueoartis/claude-planline
cd claude-planline
chmod +x bin/claude-planline
./bin/claude-planline preview --lang es --style cute
```

Then use the absolute path in Claude Code:

```json
{
  "statusLine": {
    "type": "command",
    "command": "/absolute/path/to/claude-planline/bin/claude-planline --lang es --style cute",
    "refreshInterval": 60,
    "padding": 1
  }
}
```

### Option B: install as a Python package

From this folder:

```bash
python3 -m pip install .
```

Then install it into Claude Code settings:

```bash
claude-planline install --lang es --style cute
```

This writes a `statusLine` block to:

```text
~/.claude/settings.json
```

If that file already exists, `claude-planline` creates a timestamped backup first.

Dry run:

```bash
claude-planline install --lang es --style cute --dry-run
```

Uninstall:

```bash
claude-planline uninstall
```

## Manual Claude Code config

You can also edit `~/.claude/settings.json` manually:

```json
{
  "statusLine": {
    "type": "command",
    "command": "claude-planline --lang es --style cute",
    "refreshInterval": 60,
    "padding": 1
  }
}
```

## Preview

```bash
claude-planline preview --lang es --style cute
```

Or, from a cloned repo:

```bash
./bin/claude-planline preview --lang es --style cute
```

Example:

```text
(•‿•) 5h [██░░░░░░░░] 18% usado · queda 82% · reset 03:42
(•_•) 5h [██████░░░░] 61% usado · queda 39% · reset 01:55
(×_×) 5h [█████████░] 91% usado · queda 9% · reset 00:28
($‿$) extra [████████░░] €25.14/€30 mes · reset Jul 1
(-_-) sin datos
```

## Inspect the real statusLine JSON

If the monthly usage credits do not appear, first check whether Claude Code exposes them to `statusLine`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "claude-planline dump",
    "refreshInterval": 60,
    "padding": 1
  }
}
```

After one Claude Code response, inspect:

```text
~/.claude/last-statusline-input.json
```

Look for fields such as:

```text
rate_limits
five_hour
usage_credits
credits
extra_usage
```

If `usage_credits` is not present in the statusLine JSON, `claude-planline` will not invent it or call private APIs.

## Styles

Cute:

```bash
claude-planline --style cute
```

Plain:

```bash
claude-planline --style plain
```

Spanish:

```bash
claude-planline --lang es
```

English:

```bash
claude-planline --lang en
```

Disable colors:

```bash
claude-planline --no-color
```

## Data policy

`claude-planline` does not:

- ask for your Claude login
- read browser cookies
- call `claude.ai`
- call `api.anthropic.com`
- send telemetry
- store usage history

It reads stdin, prints one line, and exits.

The optional `dump` command writes the received statusLine JSON to:

```text
~/.claude/last-statusline-input.json
```

## Limitations

The display is only as fresh as the data Claude Code gives to `statusLine`.

If you use Claude web or Claude Desktop while Claude Code is idle, the shown values may be stale until Claude Code receives updated usage data.

Monthly usage credits are displayed only if they are present in the official statusLine JSON.

## Marca / Brand

This project is not affiliated with Anthropic.

The cute faces are original text UI. The project does not use Anthropic logos, mascots, trademarks, or brand assets.

## Development

Run locally:

```bash
python3 -m claude_planline.cli preview --lang es --style cute
```

Test with sample JSON:

```bash
printf '%s\n' '{"rate_limits":{"five_hour":{"used_percentage":42,"resets_at":"2026-06-07T02:10:00Z"}},"usage_credits":{"spent":25.14,"limit":30,"currency":"EUR","resets_at":"Jul 1"}}' | claude-planline --lang es --style cute
```

## License

MIT
