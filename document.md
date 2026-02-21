AI Code Archaeology – Research SaaS Technical Plan
1. Project Overview
This project is a research-oriented SaaS platform designed to analyze open-source software repositories
and determine why projects stagnate or die. The system focuses on offline, deep analysis and produces
structured reports rather than continuous dashboards.
2. Development Phases
● Phase 0 – Definition & Research: Define 'dead project' criteria, metrics, scoring weights, and
exclusion rules.
● Phase 1 – Data Ingestion: Collect commit history, contributors, issues, PRs, releases via APIs.
● Phase 2 – Core Metrics Engine: Compute stagnation, bus factor, contributor churn, activity decay.
● Phase 3 – NLP Analysis: Semantic analysis of commit messages to detect technical debt and intent
collapse.
● Phase 4 – Failure Reasoning Engine: Combine metrics and NLP outputs to generate 'Why it died?'
explanations.
● Phase 5 – Report Generation: Produce PDF/Markdown reports with scores, graphs, and
comparisons.
● Phase 6 – SaaS Layer: Repo submission, async job handling, status tracking, and report delivery.
3. Core Analysis Algorithm
1 Input repository URL.
2 Fetch repository metadata and historical data snapshot.
3 Build time-series of commits, contributors, issues, and releases.
4 Construct contributor graph and calculate bus factor.
5 Detect activity decay and stagnation patterns.
6 Apply NLP to commit messages to extract semantic signals.
7 Aggregate metrics into weighted failure score.
8 Generate natural-language explanation of failure causes.
9 Compare against known dead-project clusters.
10 Output structured analytical report.
4. Technology Tree
■ Data Layer: Git APIs, data normalization, snapshot caching.
■ Processing Layer: Python analytics stack (time-series, graph analysis).
■ AI / NLP Layer: Embeddings, clustering, semantic pattern detection.
■ Scoring Layer: Weighted risk model and classification logic.
■ Reporting Layer: PDF & Markdown generation, visualization export.■ SaaS Orchestration: Async workers, job queues, API gateway.
■ Interface Layer: Minimal web UI for submission and download.
5. Expected Outcome
The final system is a research-grade SaaS platform capable of analyzing real-world software repositories
and producing explainable, data-driven failure reports. The architecture prioritizes analytical depth,
scientific validity, and CV-level technical credibility over traditional SaaS engagement metrics.