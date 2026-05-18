---
name: debt-track
description: "Quantify technical debt in developer hours. Track debt trends, identify hotspots, calculate maintenance cost. Output to Telegram/Discord/local file."
version: 1.0.0
author: powds
license: MIT
metadata:
  debt-track:
    tags: [technical-debt, code-analysis, metrics, developer-tools]
    homepage: https://github.com/powds/debt-track
---

# DebtTrack Skill

Track technical debt in hours, not code smells. Quantifies your codebase into developer time and monetary cost.

## Usage

### Command Line

```bash
# Analyze a project
python debt_track.py --path /path/to/project --output telegram

# Specific modules only
python debt_track.py --path /path/to/project --modules src/api,lib/utils

# Output to file only
python debt_track.py --path /path/to/project --output file --file-path ./debt-report.md

# Skip cost calculation
python debt_track.py --path /path/to/project --no-cost
```

### Hermes Integration

```bash
# Via cron job (weekly)
hermes cron create "0 9 * * 1" --prompt "Run debt-track on ~/projects and send report to telegram" --skills debt-track

# Direct command
hermes skills exec debt-track --path ~/projects/captionhook --output telegram
```

## Output Formats

| Format | Flag | Description |
|--------|------|-------------|
| Telegram | `--output telegram` | Send to home channel |
| Discord | `--output discord` | Send to Discord home |
| File | `--output file --file-path ./report.md` | Save as markdown |
| Stdout | `--output stdout` | Print to terminal (default) |

## Metrics Collected

- **Lines of Code (LOC)** per module
- **Cyclomatic Complexity** estimation via nested depth analysis
- **File age** (last modified)
- **Hotspot score** = (complexity × LOC × age_factor)
- **Debt hours** = hotspot_score × refactor_multiplier

## Cost Calculation

```
monthly_cost = (total_debt_hours / 12) × avg_hourly_rate
avg_hourly_rate = configurable, default $50/hr
```

## Configuration

Create `~/.debt-track/config.yaml`:

```yaml
projects:
  captionhook:
    path: ~/projects/captionhook
    hourly_rate: 50
    priority_threshold: 0.7
  facelessflow:
    path: ~/projects/facelessflow
    hourly_rate: 50

output:
  default_format: telegram
  include_modules: true
  trend_days: 7

analysis:
  exclude_patterns:
    - "node_modules/*"
    - "*.min.js"
    - "dist/*"
    - ".git/*"
  complexity_weights:
    nested_depth: 1.5
    file_age_days: 0.01
    loc_penalty: 0.001
```

## Files

```
debt-track/
├── SKILL.md              # This file
├── debt_track.py         # Main analysis script
├── config.yaml           # Default config
├── requirements.txt      # Python dependencies
├── docs/
│   ├── README.md         # Full documentation
│   ├── ALGORITHM.md      # How debt is calculated
│   └── API.md            # API reference
└── README.md             # Project README
```