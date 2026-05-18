# DebtTrack

**Track technical debt in hours, not code smells.**

DebtTrack quantifies your codebase's technical debt into developer hours and monetary cost. Run as a Hermes skill, delivering weekly reports to Telegram/Discord — no server, no budget needed.

## Features

- **Quantified in hours** — not scores, not "A/B/C ratings"
- **Monetary translation** — see debt cost in your team's monthly salary spend
- **Weekly trend tracking** — debt going up or down per module
- **Priority breakdown** — Critical/High/Medium with actionable modules
- **Multi-format output** — Telegram, Discord, local file
- **Self-hosted** — runs on your Mac/server, no external service

## Quick Start

```bash
# Install skill
hermes skills install https://raw.githubusercontent.com/powds/debt-track/main/SKILL.md

# Run analysis
hermes debt-track --path /path/to/project

# Weekly cron (every Monday 9am)
hermes cron create "0 9 * * 1" --prompt "Run DebtTrack on your projects and send report" --skills debt-track
```

## Output Example

```
📊 DebtTrack Report - captionhook

Total Debt: 347 hours
Trend: +12h this week ↑

Priority Breakdown:
  🔴 Critical: 89h - 3 modules
  🟡 High: 156h - 5 modules
  🟢 Medium: 102h - 8 modules

Cost Impact: ~$4,200/month maintenance overhead

Top 3 Hotspots:
  1. src/services/payment.js: 47h
  2. legacy/auth/: 38h
  3. reports/generator.ts: 29h
```

## Requirements

- Hermes Agent (running 24/7)
- `cloc` or `wc` for LOC counting (cloc recommended)
- Python 3.8+

## Documentation

See [docs/](docs/) for full documentation.