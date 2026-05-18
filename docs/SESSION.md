# DebtTrack Session Log

## Session: 2026-05-18

### What was built
- **DebtTrack** — technical debt quantification tool
- Quantifies code in developer hours, not scores
- Translates to monetary cost ($/month)
- Output: Telegram, Discord, file, JSON
- Runs locally (no server needed)

### Project location
`~/projects/debt-track/`

### GitHub
https://github.com/powds/debt-track

### Test results
- captionhook: 1,158 hours debt, $4,825/month maintenance
- 4 critical modules, 3 high, 6 medium

### Files created
```
debt-track/
├── SKILL.md              # Hermes skill integration
├── debt_track.py         # Main analysis script
├── requirements.txt      # Python dependencies
├── README.md             # Project overview
├── config.yaml           # Default config (to be created)
└── docs/
    └── ALGORITHM.md      # How debt is calculated
```

### Next steps
1. Create config.yaml with project paths
2. Setup weekly cron job
3. Test with other projects (facelessflow, hookconversion)
4. Add true cyclomatic complexity via radon/pylint
5. Track trend over time (save history to JSON)

### Key decisions
- Keep it simple: LOC + nesting depth + age
- Not using full static analysis (too complex for v1)
- Focus on relative comparison (which modules are worse)
- Refactor multiplier = 4 hours per hotspot point (tunable)

### Dependencies
- Python 3.8+
- requests (for Telegram/Discord)
- pyyaml (optional, falls back to JSON)