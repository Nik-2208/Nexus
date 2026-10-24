# NEXUS: AI Failure Intelligence Engine

> *“Don't just detect AI failure. Trace how it happens.”*

NEXUS is an open-source, local-first experimental diagnostic engine designed to discover, trace, and evaluate structural failure modes in AI agent plans, architectures, and execution traces.

---

## 🔬 Four Integrated Diagnostic Modules

1. **BeliefBlast Radius:** Calculates the downstream dependency radius when claims are contradicted, revised, or disproven, identifying affected configuration files and code artifacts.
2. **ContextFlip:** Performs controlled context perturbations to detect whether subtle context shifts cause plans to invert or drop safety constraints.
3. **GoalRot:** Formulates deterministic invariant predicates to detect divergence between explicit user objectives (e.g. offline-only operation) and proposed actions.
4. **AssumptionDebt:** Audits unverified assumptions and subjects them to safe, allowlisted deterministic test checks.

---

## 🛡️ Non-Negotiable Security Invariants

- **Local-First & Offline by Default:** Demo Mode and baseline analysis run with zero network activity.
- **Strict Loopback Binding:** UI and local inference clients bind exclusively to `127.0.0.1` / `localhost`.
- **SSRF Prevention:** Enforced endpoint validation blocks non-loopback destinations, redirects, and obfuscations.
- **No Arbitrary Code Execution:** Zero use of `eval()`, `exec()`, or dynamic tool execution. Tests are strictly allowlisted.
- **Zero Silent Egress:** Remote transmission (e.g. Gemini API) is disabled by default and requires explicit per-run confirmation.
- **Secret Redaction:** API keys and credentials are systematically redacted from UI, logs, errors, and history.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- Windows, macOS, or Linux

### 2. Installation
Clone repository and install dependencies:
```bash
pip install -r requirements.txt
```

Launch NEXUS Modern Web Application (FastAPI + Scientific UI):
```bash
python -m uvicorn nexus.web.server:app --host 127.0.0.1 --port 8000
```
*(Or execute `start_web.bat`)*

Alternatively, launch via Streamlit on loopback:
```bash
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```
Or on Windows run:
```bat
start_app.bat
```

### 4. Running with Local Gemma Model (Optional)
If you have `llama-server` installed and the GGUF model in the project directory:
```bat
start_local_model.bat
```

### 5. Running the Test Suite
Execute the pytest suite:
```bash
python -m pytest tests/
```

---

## 📄 License
Released under the Apache 2.0 License. Model weights and runtimes are subject to their respective licenses.
