from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

LOG_PATH = Path("data/logs.jsonl")


def _percentile(data: list[float | int], p: float) -> float:
    if not data:
        return 0.0
    sorted_d = sorted(data)
    k = (len(sorted_d) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_d) - 1)
    d = k - f
    return float(sorted_d[f] * (1 - d) + sorted_d[c] * d)


def render_dashboard_html() -> str:
    records: list[dict[str, Any]] = []
    if LOG_PATH.exists():
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=60)

    # Filter within last 60 minutes
    recent_records: list[dict[str, Any]] = []
    for r in records:
        ts_str = r.get("ts")
        if ts_str:
            try:
                # Handle iso format
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts >= cutoff:
                    recent_records.append(r)
            except Exception:
                recent_records.append(r)
        else:
            recent_records.append(r)

    # Panel 1: Latency & TTFT
    responses = [r for r in recent_records if r.get("event") == "response_sent"]
    latencies = [r["latency_ms"] for r in responses if "latency_ms" in r]
    ttfts = [r["ttft_ms"] for r in responses if "ttft_ms" in r]

    p50 = _percentile(latencies, 50)
    p95 = _percentile(latencies, 95)
    p99 = _percentile(latencies, 99)
    ttft_p95 = _percentile(ttfts, 95)

    # Panel 2: Traffic
    received = [r for r in recent_records if r.get("event") == "request_received"]
    req_count = len(received)
    rate_per_min = round(req_count / 60.0, 2)

    # Panel 3: Errors & Retrieval Success
    failed = [r for r in recent_records if r.get("event") == "request_failed"]
    total_reqs = req_count if req_count > 0 else 1
    error_rate_pct = round((len(failed) / total_reqs) * 100, 2)

    tool_calls = [r for r in responses if "tool_success" in r and r.get("tool_name") == "retrieval"]
    tool_success_count = sum(1 for r in tool_calls if r.get("tool_success") is True)
    tool_success_pct = round((tool_success_count / len(tool_calls) * 100), 1) if tool_calls else 100.0

    # Panel 4: Cost
    costs = [r.get("cost_usd", 0.0) for r in responses]
    total_cost = round(sum(costs), 6)
    avg_cost = (total_cost / len(responses)) if responses else 0.0

    # Panel 5: Tokens
    tokens_in = sum(r.get("tokens_in", 0) for r in responses)
    tokens_out = sum(r.get("tokens_out", 0) for r in responses)
    total_tokens = tokens_in + tokens_out

    # Panel 6: Quality
    quality_scores = [r["quality_score"] for r in responses if "quality_score" in r]
    mean_quality = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0.0

    # Threshold checks
    lat_status = "PASS" if p95 <= 3000 else "BREACH"
    err_status = "PASS" if error_rate_pct <= 2.0 and tool_success_pct >= 90.0 else "BREACH"
    cost_status = "PASS" if total_cost <= 2.5 else "BREACH"
    token_status = "PASS" if total_tokens <= 50000 else "BREACH"
    qual_status = "PASS" if mean_quality >= 0.75 else "BREACH"

    # HTML template
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="30">
    <title>K4-L3A Day 13 Monitoring & LLMOps Dashboard</title>
    <style>
        :root {{
            --bg: #0d1117;
            --card-bg: #161b22;
            --border: #30363d;
            --text: #c9d1d9;
            --text-heading: #58a6ff;
            --pass: #2ea043;
            --warn: #d29922;
            --danger: #f85149;
        }}
        body {{
            background-color: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 24px;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        h1 {{
            color: var(--text-heading);
            margin: 0;
            font-size: 22px;
        }}
        .meta-bar {{
            font-size: 13px;
            color: #8b949e;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-pass {{ background: rgba(46, 160, 67, 0.15); color: #3fb950; border: 1px solid #3fb950; }}
        .badge-breach {{ background: rgba(248, 81, 73, 0.15); color: #f85149; border: 1px solid #f85149; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .card-title {{
            font-size: 15px;
            font-weight: 600;
            color: #f0f6fc;
        }}
        .big-number {{
            font-size: 32px;
            font-weight: 700;
            color: #f0f6fc;
            margin: 8px 0;
        }}
        .unit {{
            font-size: 13px;
            color: #8b949e;
            font-weight: 400;
        }}
        .sub-metrics {{
            font-size: 13px;
            color: #8b949e;
            margin-top: 10px;
            line-height: 1.6;
        }}
        .threshold-line {{
            margin-top: 12px;
            padding-top: 8px;
            border-top: 1px dashed var(--border);
            font-size: 12px;
            color: #8b949e;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-top: 16px;
        }}
        th, td {{
            text-align: left;
            padding: 8px;
            border-bottom: 1px solid var(--border);
        }}
        th {{ color: #8b949e; }}
    </style>
</head>
<body>
    <header>
        <div>
            <h1>K4-L3A Day 13 Monitoring & LLMOps Dashboard</h1>
            <div class="meta-bar">Student: <b>Le Minh Hieu (2A202602848)</b> | Service: <code>api</code> | Environment: <code>dev</code></div>
        </div>
        <div class="meta-bar" style="text-align: right;">
            <div>Time Range: <b>Last 60 Minutes</b></div>
            <div>Refresh Rate: <b>30s</b> | Auto-refreshing</div>
        </div>
    </header>

    <div class="grid">
        <!-- Panel 1: Latency -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">1. Latency & TTFT</span>
                <span class="badge badge-{'pass' if lat_status == 'PASS' else 'breach'}">{lat_status}</span>
            </div>
            <div class="big-number">{p95:.1f} <span class="unit">ms (P95)</span></div>
            <div class="sub-metrics">
                <div>• P50: <b>{p50:.1f} ms</b> | P99: <b>{p99:.1f} ms</b></div>
                <div>• TTFT P95: <b>{ttft_p95:.1f} ms</b></div>
            </div>
            <div class="threshold-line">SLO Threshold: P95 &le; 3000 ms</div>
        </div>

        <!-- Panel 2: Traffic -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">2. Request Traffic</span>
                <span class="badge badge-pass">ACTIVE</span>
            </div>
            <div class="big-number">{req_count} <span class="unit">requests</span></div>
            <div class="sub-metrics">
                <div>• Rate: <b>{rate_per_min} req/min</b></div>
                <div>• Total Received: <b>{req_count}</b></div>
            </div>
            <div class="threshold-line">Threshold: rate &ge; 1 req/min</div>
        </div>

        <!-- Panel 3: Errors -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">3. Errors & Retrieval</span>
                <span class="badge badge-{'pass' if err_status == 'PASS' else 'breach'}">{err_status}</span>
            </div>
            <div class="big-number">{error_rate_pct:.1f}% <span class="unit">error rate</span></div>
            <div class="sub-metrics">
                <div>• Retrieval Success: <b>{tool_success_pct:.1f}%</b> ({tool_success_count}/{len(tool_calls)})</div>
                <div>• Failed Requests: <b>{len(failed)}</b></div>
            </div>
            <div class="threshold-line">SLO: Error Rate &le; 2% | Retrieval &ge; 90%</div>
        </div>

        <!-- Panel 4: Cost -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">4. Cost Over Time</span>
                <span class="badge badge-{'pass' if cost_status == 'PASS' else 'breach'}">{cost_status}</span>
            </div>
            <div class="big-number">${total_cost:.5f} <span class="unit">USD</span></div>
            <div class="sub-metrics">
                <div>• Requests Billed: <b>{len(responses)}</b></div>
                <div>• Avg / req: <b>${avg_cost:.6f}</b></div>
            </div>
            <div class="threshold-line">Budget Limit: &le; $2.50 USD / window</div>
        </div>

        <!-- Panel 5: Tokens -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">5. Tokens Volume</span>
                <span class="badge badge-{'pass' if token_status == 'PASS' else 'breach'}">{token_status}</span>
            </div>
            <div class="big-number">{total_tokens:,} <span class="unit">tokens</span></div>
            <div class="sub-metrics">
                <div>• Tokens In: <b>{tokens_in:,}</b></div>
                <div>• Tokens Out: <b>{tokens_out:,}</b></div>
            </div>
            <div class="threshold-line">Threshold: sum &le; 50,000 tokens</div>
        </div>

        <!-- Panel 6: Quality -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">6. Quality Proxy</span>
                <span class="badge badge-{'pass' if qual_status == 'PASS' else 'breach'}">{qual_status}</span>
            </div>
            <div class="big-number">{mean_quality:.2f} <span class="unit">/ 1.0</span></div>
            <div class="sub-metrics">
                <div>• Evaluated Responses: <b>{len(quality_scores)}</b></div>
                <div>• Quality Model: Heuristic Grounding</div>
            </div>
            <div class="threshold-line">Guardrail: mean &ge; 0.75</div>
        </div>
    </div>

    <div class="card" style="margin-top: 24px;">
        <div class="card-title" style="margin-bottom: 8px;">Recent Handled Requests (Correlation & Traces)</div>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Correlation ID</th>
                    <th>Feature</th>
                    <th>Latency</th>
                    <th>Tokens (In / Out)</th>
                    <th>Cost</th>
                    <th>Quality</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f'''<tr>
                    <td>{r.get('ts', '')[-12:-1]}</td>
                    <td><code>{r.get('correlation_id', '')}</code></td>
                    <td>{r.get('feature', '')}</td>
                    <td>{r.get('latency_ms', '')} ms</td>
                    <td>{r.get('tokens_in', '')} / {r.get('tokens_out', '')}</td>
                    <td>${r.get('cost_usd', 0):.5f}</td>
                    <td>{r.get('quality_score', '')}</td>
                </tr>''' for r in responses[-10:][::-1])}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    return html
