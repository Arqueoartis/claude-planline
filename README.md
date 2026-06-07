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

## Quick Install

### English

```bash
git clone https://github.com/Arqueoartis/claude-planline
cd claude-planline
chmod +x bin/claude-planline
./bin/claude-planline preview --lang en --style cute
./bin/claude-planline install --lang en --style cute --layout two-line
```

Restart Claude Code. If you already had a custom statusLine, `claude-planline` keeps it and adds the plan meter underneath.

### Español

```bash
git clone https://github.com/Arqueoartis/claude-planline
cd claude-planline
chmod +x bin/claude-planline
./bin/claude-planline preview --lang es --style cute
./bin/claude-planline install --lang es --style cute --layout two-line
```

Reinicia Claude Code. Si ya tenias una statusLine propia, `claude-planline` la conserva y añade el medidor del plan debajo.

Example two-line result:

```text
Opus 4.8 │ ~/project │ █████████░ 97% left (26.8k/1.0M)
(•‿•) 5h [█░░░░░░░░░] 9% used · left 91% · reset 02:10
```

Ejemplo en dos lineas:

```text
Opus 4.8 │ ~/proyecto │ █████████░ 97% queda (26.8k/1.0M)
(•‿•) 5h [█░░░░░░░░░] 9% usado · queda 91% · reset 02:10
```

## Install Modes

### Preserve an existing statusLine

This is the default and safest mode:

```bash
./bin/claude-planline install --lang en --style cute --layout two-line
```

It creates:

```text
~/.claude/claude-planline-wrapper.sh
```

and updates:

```text
~/.claude/settings.json
```

with a timestamped backup first.

Inline instead of two lines:

```bash
./bin/claude-planline install --lang en --style cute --layout inline
```

### Replace the existing statusLine

```bash
./bin/claude-planline install --lang en --style cute --no-preserve-existing
```

### Dry run

Show what would be written without changing files:

```bash
./bin/claude-planline install --lang en --style cute --layout two-line --dry-run
```

### Uninstall

```bash
./bin/claude-planline uninstall
```

`uninstall` removes the `statusLine` block from settings and writes a backup. If you had an old statusLine, restore it from the backup printed by the installer.

## Manual Claude Code Config

You can also edit `~/.claude/settings.json` manually:

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

## Optional Python Package Install

From a cloned repo:

```bash
python3 -m pip install .
```

Then:

```bash
claude-planline install --lang en --style cute --layout two-line
```

Or directly from GitHub:

```bash
python3 -m pip install "git+https://github.com/Arqueoartis/claude-planline.git"
claude-planline install --lang en --style cute --layout two-line
```

If `pip` is not available or has build issues, use the cloned repo method above. It needs only Python 3 and no third-party dependencies.

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

English preview:

```bash
./bin/claude-planline preview --lang en --style cute
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
