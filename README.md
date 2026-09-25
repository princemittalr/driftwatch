# DriftWatch — Autonomous Infrastructure Intelligence Agent

Oct 3, 2026 · @Prince Mittal

## Overview

DriftWatch is an autonomous multi-agent system that continuously monitors your software infrastructure and tells you what is about to break — before it does.

Most engineering teams react to outages. DriftWatch acts before them. It pulls signals from your GitHub repository and dependency stack, correlates them across sources using three tiers of NVIDIA Nemotron models, and delivers a ranked strategic action plan — complete with auto-filed GitHub Issues and a plain-English weekly digest your whole team can read.

The core insight: no existing tool loads your entire codebase and all external signals simultaneously and reasons across them. Nemotron Super's 1M-token context window makes that possible for the first time.

## The Problem

Every engineering team running production software carries an invisible tax.

A dependency released a breaking change three weeks ago and nobody noticed until production went down. A CVE was published for a package in active use and sat unpatched for months. The main branch had no PR review gate, so vulnerable code merged silently. No single tool connected these dots and told the team what mattered most, right now.

Datadog alerts on individual metrics but has no code context. Dependabot raises one PR at a time but does not know if you actually call that code path. Nobody synthesizes the whole picture and tells you: in four days, these three things converging will cause an outage.

DriftWatch is that synthesis layer.

## How It Works

DriftWatch runs a three-phase agent pipeline every time a scan is triggered.

**Phase 1 — Scanner Agents using Nemotron Nano:** Two lightweight agents run in parallel. The GitHub scanner fetches recent commits, open pull requests, stale branches, and open issues. The dependency scanner reads your requirements.txt directly from the repository and checks every package against the OSV.dev CVE database. Nano handles these tasks because it is the most compute-efficient model in the family — ideal for high-frequency parallel calls where speed and cost matter more than deep reasoning.

**Phase 2 — Analyst Agent using Nemotron Super:** All scanner output is loaded into a single Super context window. Super identifies compound risks — situations where two independent findings together create a larger problem than either one alone — and scores each by blast radius and urgency. The 1M-token context window is what makes this possible: the entire codebase and all scan results fit simultaneously without chunking or approximation.

**Phase 3 — Strategist Agent using Nemotron Ultra:** Ultra takes the analyst's findings and produces a long-horizon strategic action plan with explicit effort versus impact tradeoffs. It then auto-creates GitHub Issues for critical findings — fully written with context, steps, and acceptance criteria — and generates a weekly digest in plain English that a non-technical stakeholder can read and act on.

## NVIDIA Nemotron Models

DriftWatch uses all three tiers of the Nemotron 3 family deliberately, with each model matched to the layer that fits its strengths.

| Model | Parameters | Role | Why This Model |
| --- | --- | --- | --- |
| Nemotron 3 Nano | 30B MoE, 3B active | Scanner agents — parallel GitHub and CVE analysis | Highest compute efficiency per token; built for high-frequency agentic calls |
| Nemotron 3 Super | 120B MoE, 12B active | Analyst agent — cross-signal compound risk synthesis | 1M token context window; SWE-Bench leading accuracy; 50% faster generation than comparable open models |
| Nemotron 3 Ultra | 550B MoE, 55B active | Strategist agent — planning, issue creation, weekly digest | Frontier reasoning for effort and impact tradeoffs and multi-step strategic output |

## Nebius Token Factory

All three Nemotron models are served through Nebius Token Factory using the OpenAI-compatible API at `https://api.tokenfactory.nebius.com/v1/`. The client is the standard OpenAI Python SDK with the base URL overridden — no custom SDK or wrapper required.

Token Factory enables the tiered model strategy at scale. Nano handles every scanner call because it is fast and cheap enough to run on a continuous schedule. Super is invoked once per scan cycle for the analyst pass. Ultra is reserved for the strategist layer where its reasoning depth justifies the cost. This architecture keeps DriftWatch economical enough to run continuously rather than only on demand.

## Setup Instructions

**Prerequisites:** Python 3.11 or higher, a Nebius Token Factory account with an API key, and a GitHub Personal Access Token with repo scope.

**Install**

```
git clone https://github.com/princemittalr/driftwatch
cd driftwatch
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Configure**

```
cp .env.example .env
```

Set three values in `.env`: your `NEBIUS_API_KEY` from Token Factory, your `GITHUB_TOKEN` with repo scope, and `GITHUB_REPO` as `owner/repo-name` pointing at the repository you want to monitor.

**Run a scan**

```
python main.py
```

**Launch the dashboard**

```
python dashboard/app.py
```

Open `http://localhost:5000` to see the live dashboard with health score, compound risks, strategic action plan, weekly digest, and auto-created GitHub Issues.

## Project Structure

```
driftwatch/
├── agents/
│   ├── scanner.py        GitHub repo scanner — Nemotron Nano
│   ├── dep_scanner.py    CVE and dependency scanner — Nemotron Nano
│   ├── analyst.py        Compound risk analyst — Nemotron Super
│   └── strategist.py     Strategic planner and issue creator — Nemotron Ultra
├── core/
│   └── llm.py            Nebius Token Factory client and model registry
├── dashboard/
│   └── app.py            Flask dashboard server
├── reports/              JSON scan reports auto-generated per run
├── main.py               Master orchestrator — runs the full pipeline
├── .env.example          Environment variable template
└── requirements.txt      Python dependencies
```

## Hackathon Track and License

DriftWatch is submitted to the **Best Apps and Agents** track of the Nebius × NVIDIA Global AI Hackathon. It uses all three Nemotron model tiers with deliberate purpose, demonstrates compound risk intelligence no existing tool provides, and ships as a working product with a live dashboard, automated GitHub Issue creation, and a scan pipeline ready for Nebius Serverless Jobs.

Licensed under the MIT License. See the LICENSE file in the repository root.
