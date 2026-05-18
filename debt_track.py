#!/usr/bin/env python3
"""
DebtTrack - Technical Debt Quantification Tool

Track technical debt in hours, not code smells.
Output to Telegram, Discord, or file.
"""

import argparse
import os
import sys
import json
import subprocess
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Try to import yaml, fall back to json config
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

# === CONFIGURATION ===

DEFAULT_HOURLY_RATE = 50  # USD
DEFAULT_REFACTOR_MULTIPLIER = 4  # hours per hotspot point
COMPLEXITY_WEIGHTS = {
    'nested_depth': 1.5,
    'file_age_days': 0.01,
    'loc_penalty': 0.001,
    'cyclomatic': 0.5
}

EXCLUDE_PATTERNS = [
    'node_modules', '.git', '__pycache__', 'dist', 'build',
    '*.min.js', '*.bundle.js', '.venv', 'venv', 'target',
    'coverage', '.next', '.nuxt'
]

# === ANALYSIS ===

def get_git_files(root_path: str, extensions: List[str] = None) -> List[str]:
    """Get all tracked files in git repo."""
    try:
        result = subprocess.run(
            ['git', '-C', root_path, 'ls-files', '--others', '--exclude-standard'],
            capture_output=True, text=True, timeout=30
        )
        tracked = result.stdout.strip().split('\n') if result.stdout.strip() else []

        result = subprocess.run(
            ['git', '-C', root_path, 'ls-files'],
            capture_output=True, text=True, timeout=30
        )
        all_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        all_files.extend(tracked)
        return list(set(all_files))
    except Exception:
        return []

def should_exclude(path: str) -> bool:
    """Check if path matches exclusion patterns."""
    path_lower = path.lower()
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith('*'):
            if path_lower.endswith(pattern[1:]):
                return True
        elif pattern in path_lower:
            return True
    return False

def count_loc_file(file_path: str) -> Tuple[int, int]:
    """Count lines and estimate complexity for a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        total_lines = len(lines)
        code_lines = 0
        nested_depth = 0
        max_nested = 0
        cyclomatic = 1  # base complexity

        in_comment = False
        for line in lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Handle comments
            if stripped.startswith('/*'):
                in_comment = True
            if in_comment:
                if '*/' in stripped:
                    in_comment = False
                continue

            if stripped.startswith('//') or stripped.startswith('#'):
                continue

            code_lines += 1

            # Count nesting
            indent = len(line) - len(line.lstrip())
            depth = indent // 4 + 1
            max_nested = max(max_nested, depth)

            # Cyclomatic complexity rough estimate
            if any(kw in stripped for kw in ['if ', 'elif ', 'else', 'for ', 'while ', 'except', 'case ', '&&', '||']):
                cyclomatic += 0.5

        return code_lines, int(max_nested * COMPLEXITY_WEIGHTS['nested_depth'] + cyclomatic)
    except Exception:
        return 0, 0

def get_file_age_days(file_path: str) -> int:
    """Get file age in days since last modification."""
    try:
        mtime = os.path.getmtime(file_path)
        age = datetime.now() - datetime.fromtimestamp(mtime)
        return age.days
    except Exception:
        return 0

def analyze_project(root_path: str, exclude_patterns: List[str] = None) -> Dict:
    """Analyze project and calculate technical debt."""
    global EXCLUDE_PATTERNS
    if exclude_patterns:
        EXCLUDE_PATTERNS = exclude_patterns

    modules = {}
    total_debt_hours = 0
    total_loc = 0

    root_path = os.path.expanduser(root_path)
    if not os.path.exists(root_path):
        return {'error': f'Path not found: {root_path}'}

    # Get all source files
    all_files = []
    for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.rb', '.php', '.c', '.cpp', '.h']:
        all_files.extend(Path(root_path).rglob(f'*{ext}'))

    files_analyzed = 0
    for file_path in all_files:
        str_path = str(file_path)
        if should_exclude(str_path):
            continue

        rel_path = os.path.relpath(str_path, root_path)
        code_lines, complexity = count_loc_file(str_path)
        if code_lines < 5:  # Skip very small files
            continue

        age_days = get_file_age_days(str_path)
        age_factor = min(age_days * COMPLEXITY_WEIGHTS['file_age_days'], 10)

        # Hotspot score calculation
        hotspot_score = (
            complexity * code_lines * 0.001 +
            complexity * age_factor +
            code_lines * COMPLEXITY_WEIGHTS['loc_penalty']
        )

        debt_hours = hotspot_score * DEFAULT_REFACTOR_MULTIPLIER

        # Group by module (parent directory)
        module = str(Path(rel_path).parent)
        if module == '.':
            module = 'root'

        if module not in modules:
            modules[module] = {
                'files': [],
                'total_loc': 0,
                'total_complexity': 0,
                'debt_hours': 0,
                'age_sum': 0
            }

        modules[module]['files'].append({
            'path': rel_path,
            'loc': code_lines,
            'complexity': complexity,
            'age_days': age_days,
            'hotspot_score': hotspot_score,
            'debt_hours': debt_hours
        })
        modules[module]['total_loc'] += code_lines
        modules[module]['total_complexity'] += complexity
        modules[module]['debt_hours'] += debt_hours
        modules[module]['age_sum'] += age_days

        total_debt_hours += debt_hours
        total_loc += code_lines
        files_analyzed += 1

    return {
        'project': os.path.basename(root_path),
        'path': root_path,
        'files_analyzed': files_analyzed,
        'total_loc': total_loc,
        'total_debt_hours': round(total_debt_hours, 1),
        'modules': modules,
        'analyzed_at': datetime.now().isoformat()
    }

def calculate_cost(debt_hours: float, hourly_rate: float = DEFAULT_HOURLY_RATE) -> Dict:
    """Calculate monetary cost of debt."""
    monthly_cost = (debt_hours / 12) * hourly_rate
    yearly_cost = monthly_cost * 12
    return {
        'hourly_rate': hourly_rate,
        'total_hours': round(debt_hours, 1),
        'monthly_cost': round(monthly_cost, 2),
        'yearly_cost': round(yearly_cost, 2)
    }

def prioritize_modules(modules: Dict, threshold_critical: float = 50,
                       threshold_high: float = 20, threshold_medium: float = 5) -> Dict:
    """Categorize modules by debt priority."""
    categorized = {
        'critical': [],  # >50h
        'high': [],      # 20-50h
        'medium': [],    # 5-20h
        'low': []        # <5h
    }

    for module_name, data in modules.items():
        debt = data['debt_hours']
        if debt >= threshold_critical:
            categorized['critical'].append({
                'module': module_name,
                'debt_hours': round(debt, 1),
                'loc': data['total_loc'],
                'files': len(data['files'])
            })
        elif debt >= threshold_high:
            categorized['high'].append({
                'module': module_name,
                'debt_hours': round(debt, 1),
                'loc': data['total_loc'],
                'files': len(data['files'])
            })
        elif debt >= threshold_medium:
            categorized['medium'].append({
                'module': module_name,
                'debt_hours': round(debt, 1),
                'loc': data['total_loc'],
                'files': len(data['files'])
            })
        else:
            categorized['low'].append({
                'module': module_name,
                'debt_hours': round(debt, 1),
                'loc': data['total_loc'],
                'files': len(data['files'])
            })

    # Sort each category by debt hours descending
    for cat in categorized:
        categorized[cat].sort(key=lambda x: x['debt_hours'], reverse=True)

    return categorized

# === REPORTING ===

def format_report_telegram(data: Dict, cost_data: Dict, prioritized: Dict) -> str:
    """Format report for Telegram."""
    project = data['project']
    total_debt = data['total_debt_hours']
    total_loc = data['total_loc']
    files = data['files_analyzed']

    # Emoji for Telegram
    critical_emoji = "🔴"
    high_emoji = "🟡"
    medium_emoji = "🟢"

    lines = [
        f"📊 *DebtTrack Report* — `{project}`",
        "",
        f"*Total Debt:* {total_debt:.1f} hours",
        f"*Codebase:* {total_loc:,} LOC in {files} files",
        f"*Monthly Cost:* ${cost_data['monthly_cost']:,.2f}",
        "",
        "*Priority Breakdown:*",
    ]

    # Critical
    critical_total = sum(m['debt_hours'] for m in prioritized['critical'])
    critical_count = len(prioritized['critical'])
    if critical_count > 0:
        lines.append(f"{critical_emoji} Critical: {critical_total:.1f}h — {critical_count} modules")
    else:
        lines.append(f"{critical_emoji} Critical: 0h")

    # High
    high_total = sum(m['debt_hours'] for m in prioritized['high'])
    high_count = len(prioritized['high'])
    if high_count > 0:
        lines.append(f"{high_emoji} High: {high_total:.1f}h — {high_count} modules")

    # Medium
    medium_total = sum(m['debt_hours'] for m in prioritized['medium'])
    medium_count = len(prioritized['medium'])
    if medium_count > 0:
        lines.append(f"{medium_emoji} Medium: {medium_total:.1f}h — {medium_count} modules")

    # Top hotspots
    all_hotspots = []
    for cat in ['critical', 'high', 'medium']:
        all_hotspots.extend(prioritized[cat])

    if all_hotspots:
        lines.append("")
        lines.append("*Top Hotspots:*")
        for i, hotspot in enumerate(all_hotspots[:5], 1):
            lines.append(f"{i}. `{hotspot['module']}` — {hotspot['debt_hours']:.1f}h ({hotspot['loc']:,} LOC)")

    lines.append("")
    lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_")

    return "\n".join(lines)

def format_report_markdown(data: Dict, cost_data: Dict, prioritized: Dict) -> str:
    """Format report as Markdown."""
    project = data['project']
    total_debt = data['total_debt_hours']
    total_loc = data['total_loc']
    files = data['files_analyzed']

    lines = [
        f"# DebtTrack Report — {project}",
        "",
        f"**Total Debt:** {total_debt:.1f} hours",
        f"**Codebase:** {total_loc:,} LOC in {files} files",
        f"**Monthly Cost:** ${cost_data['monthly_cost']:,.2f}",
        f"**Yearly Cost:** ${cost_data['yearly_cost']:,.2f}",
        "",
        "## Priority Breakdown",
        "",
        "| Priority | Hours | Modules |",
        "|----------|-------|---------|",
        f"| 🔴 Critical | {sum(m['debt_hours'] for m in prioritized['critical']):.1f} | {len(prioritized['critical'])} |",
        f"| 🟡 High | {sum(m['debt_hours'] for m in prioritized['high']):.1f} | {len(prioritized['high'])} |",
        f"| 🟢 Medium | {sum(m['debt_hours'] for m in prioritized['medium']):.1f} | {len(prioritized['medium'])} |",
        "",
        "## Top Hotspots",
        "",
        "| Module | Debt Hours | LOC |",
        "|--------|------------|-----|",
    ]

    all_hotspots = []
    for cat in ['critical', 'high', 'medium']:
        all_hotspots.extend(prioritized[cat])

    for hotspot in all_hotspots[:10]:
        lines.append(f"| `{hotspot['module']}` | {hotspot['debt_hours']:.1f}h | {hotspot['loc']:,} |")

    lines.append("")
    lines.append(f"_Generated: {datetime.now().isoformat()}_")

    return "\n".join(lines)

def format_report_json(data: Dict, cost_data: Dict, prioritized: Dict) -> str:
    """Format report as JSON."""
    return json.dumps({
        'project': data['project'],
        'path': data['path'],
        'debt': cost_data,
        'summary': {
            'total_loc': data['total_loc'],
            'files_analyzed': data['files_analyzed'],
            'total_debt_hours': data['total_debt_hours']
        },
        'priority': {
            'critical': prioritized['critical'],
            'high': prioritized['high'],
            'medium': prioritized['medium'],
            'low': prioritized['low']
        },
        'analyzed_at': data['analyzed_at']
    }, indent=2)

# === OUTPUT ===

def send_telegram(message: str) -> bool:
    """Send message to Telegram."""
    try:
        import requests
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')

        if not bot_token or not chat_id:
            print("ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID not set")
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(url, json={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }, timeout=30)

        return response.status_code == 200
    except Exception as e:
        print(f"Telegram send error: {e}")
        return False

def send_discord(message: str) -> bool:
    """Send message to Discord."""
    try:
        import requests
        webhook_url = os.environ.get('DISCORD_WEBHOOK_URL', '')

        if not webhook_url:
            print("ERROR: DISCORD_WEBHOOK_URL not set")
            return False

        response = requests.post(webhook_url, json={
            'content': message
        }, timeout=30)

        return response.status_code in [200, 204]
    except Exception as e:
        print(f"Discord send error: {e}")
        return False

def save_file(content: str, file_path: str) -> bool:
    """Save content to file."""
    try:
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Report saved to: {file_path}")
        return True
    except Exception as e:
        print(f"File save error: {e}")
        return False

# === CLI ===

def load_config(config_path: str = '~/.debt-track/config.yaml') -> Dict:
    """Load configuration file."""
    config_path = os.path.expanduser(config_path)
    if os.path.exists(config_path):
        if HAS_YAML:
            with open(config_path) as f:
                return yaml.safe_load(f) or {}
        else:
            with open(config_path) as f:
                return json.load(f)
    return {}

def main():
    parser = argparse.ArgumentParser(description='DebtTrack - Quantify technical debt in hours')
    parser.add_argument('--path', '-p', required=True, help='Project path to analyze')
    parser.add_argument('--output', '-o', default='stdout',
                       choices=['telegram', 'discord', 'file', 'stdout', 'json'],
                       help='Output format')
    parser.add_argument('--file-path', '-f', help='Output file path (for file output)')
    parser.add_argument('--hourly-rate', type=float, default=DEFAULT_HOURLY_RATE,
                       help=f'Hourly rate for cost calculation (default: {DEFAULT_HOURLY_RATE})')
    parser.add_argument('--config', '-c', help='Config file path')
    parser.add_argument('--modules', '-m', help='Comma-separated modules to analyze')
    parser.add_argument('--no-cost', action='store_true', help='Skip cost calculation')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    # Load config
    config = {}
    if args.config:
        config = load_config(args.config)
    else:
        config = load_config()

    # Analyze project
    print(f"Analyzing: {args.path}")
    data = analyze_project(args.path)

    if 'error' in data:
        print(f"ERROR: {data['error']}")
        sys.exit(1)

    # Calculate cost
    cost_data = calculate_cost(data['total_debt_hours'], args.hourly_rate)

    # Prioritize modules
    prioritized = prioritize_modules(data['modules'])

    # Format output
    if args.json:
        output = format_report_json(data, cost_data, prioritized)
    elif args.output == 'json':
        output = format_report_json(data, cost_data, prioritized)
    elif args.output == 'telegram':
        output = format_report_telegram(data, cost_data, prioritized)
    elif args.output == 'discord':
        # Discord doesn't support Markdown nicely, simplify
        output = format_report_markdown(data, cost_data, prioritized)
    elif args.output == 'file':
        output = format_report_markdown(data, cost_data, prioritized)
    else:
        output = format_report_markdown(data, cost_data, prioritized)

    # Send output
    if args.output == 'telegram':
        success = send_telegram(output)
        if success:
            print("Report sent to Telegram")
        else:
            print("Failed to send to Telegram, showing output:")
            print(output)
    elif args.output == 'discord':
        success = send_discord(output)
        if success:
            print("Report sent to Discord")
        else:
            print("Failed to send to Discord, showing output:")
            print(output)
    elif args.output == 'file':
        file_path = args.file_path or f"./debt-track-{data['project']}-{datetime.now().strftime('%Y%m%d')}.md"
        save_file(output, file_path)
    else:
        print(output)

if __name__ == '__main__':
    main()