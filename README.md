# Gabriel Medeiros

**Computer Engineering @ IME (2nd in class) · Founding engineer ×2 (Baze, Camada AI) · ML research @ Purdue**

## Shipped

- **Built a bank-reconciliation engine that runs in 40 s; the market incumbent takes 2 min 50 s (≈4×).** Camada AI, 2025. Deterministic, on Google OR-Tools constraint programming, chosen over an LLM after measuring correctness, latency and cost. M:N transaction matching; OFX, PDF, XLS and CSV parsers.
- **Shipped Camada AI's full MVP in 72 hours** (React/TypeScript, FastAPI, Postgres). Also built a multi-agent WhatsApp invoice-automation flow (LangGraph, Whisper).
- **Led avionics for IME's rocketry team at IREC 2025** (Intercollegiate Rocket Engineering Competition). C++ firmware on ESP32 with a Kalman filter.
- **Wrote GPT-2 from scratch in PyTorch** and trained it on Wikipedia on IMPA's GPU cluster (IMPA ML Summer School 2024).

## Code you can check

| Repo | What it shows | Stack |
|---|---|---|
| [eeg-mental-state-classifier](https://github.com/GabeMed/eeg-mental-state-classifier)<br>[![CI](https://github.com/GabeMed/eeg-mental-state-classifier/actions/workflows/ci.yml/badge.svg)](https://github.com/GabeMed/eeg-mental-state-classifier/actions/workflows/ci.yml) | 3-class EEG classifier with leakage-aware cross-validation. Test macro-F1 **0.970** (XGBoost) vs **0.953** (logistic regression); 33 tests. | Python, scikit-learn, XGBoost |
| [micrograd](https://github.com/GabeMed/micrograd)<br>[![CI](https://github.com/GabeMed/micrograd/actions/workflows/ci.yml/badge.svg)](https://github.com/GabeMed/micrograd/actions/workflows/ci.yml) | Scalar autograd engine (after Karpathy's micrograd) plus a NumPy statevector simulator; gradients match PyTorch and PennyLane to **1e-10**. On make_moons a 26-parameter circuit reaches **97.5%**, a 25-parameter MLP **99.4%**: no quantum advantage. | Python, NumPy |
| [Sanctum](https://github.com/GabeMed/Sanctum)<br>[![CI](https://github.com/GabeMed/Sanctum/actions/workflows/ci.yml/badge.svg)](https://github.com/GabeMed/Sanctum/actions/workflows/ci.yml) | Append-only journal API with **AES-256-GCM** envelope encryption. `go test -race` against a real Postgres in CI; passes gosec and govulncheck. | Go, PostgreSQL |
| [personal-financial-manager](https://github.com/GabeMed/personal-financial-manager)<br>[![CI](https://github.com/GabeMed/personal-financial-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/GabeMed/personal-financial-manager/actions/workflows/ci.yml) | Finance tracker; one `docker compose up` runs the full stack. **38** API tests, CI on SQLite and Postgres. | FastAPI, PostgreSQL, React, TypeScript |
| [SmartInvestor](https://github.com/GabeMed/SmartInvestor)<br>[![CI](https://github.com/GabeMed/SmartInvestor/actions/workflows/ci.yml/badge.svg)](https://github.com/GabeMed/SmartInvestor/actions/workflows/ci.yml) | Pulls BRAPI quotes for **~2,000** Brazilian tickers every hour and e-mails a buy or sell alert when a watched price reaches either end of its range. **33** tests, BRAPI mocked. | Django, Celery, Redis |
| [panorama-stitching](https://github.com/GabeMed/panorama-stitching)<br>[![CI](https://github.com/GabeMed/panorama-stitching/actions/workflows/ci.yml/badge.svg)](https://github.com/GabeMed/panorama-stitching/actions/workflows/ci.yml) | DLT + RANSAC homography from scratch. Stays sub-pixel with **60%** injected outliers; **1.93 px** mean corner error on a synthetic pair with known ground truth (OpenCV: 1.20 px). | Python, NumPy, OpenCV |
| [CEOs-Project-IMU](https://github.com/GabeMed/CEOs-Project-IMU)<br>[![CI](https://github.com/GabeMed/CEOs-Project-IMU/actions/workflows/ci.yml/badge.svg)](https://github.com/GabeMed/CEOs-Project-IMU/actions/workflows/ci.yml) | ESP32 firmware: fuses an ICM-20948 9-axis IMU with a Mahony filter and outputs orientation at **50 Hz**. | C++, PlatformIO |

## Timeline

- `2025–now` **Baze.** Founding engineer at Baze, a Brazilian fintech: first hire after the two founders; builds the company's AI and backend systems in production.
- `2025–now` **Purdue, Prof. Can Li's group.** Visiting scholar, on site Aug–Dec 2025, remote since. Research on explainability for neural networks; paper under review at ICLR 2027.
- `2025` **Camada AI.** Founding engineer, Jun–Aug: the OR-Tools reconciliation engine and the 72-hour MVP.
- `2024–25` **CNPq (PIBIC).** Undergraduate research: ML for Python performance.
- `2024` **IMPA ML Summer School.** GPT-2 from scratch in PyTorch.
- `2023–25` **IME rocketry team.** Avionics firmware; avionics lead at IREC 2025.
- `2023` **Abstra (YC S21).** Software engineering intern, Sep–Dec: Python automations for enterprise clients.
- `2023` **Vinci Partners.** Summer intern, Jan–Mar: IGP-M and IPC inflation forecasting in R with time-aware cross-validation.

**Education.** IME (Instituto Militar de Engenharia), Computer Engineering, civilian track (about 15 civilian seats a year nationwide). 2nd in class; graduating Dec 2026.

**Stack.** Python, TypeScript, Julia, C/C++, Go, SQL · PyTorch, scikit-learn, XGBoost · LangGraph, FastAPI, Django, React · OR-Tools, Gurobi, JuMP · Postgres, AWS, Docker

**Contact.** [LinkedIn](https://linkedin.com/in/gabriel-medeiros-374a3b233) · [gabrielmedeirossoftware@gmail.com](mailto:gabrielmedeirossoftware@gmail.com) · [LeetCode](https://www.leetcode.com/medeiross)
