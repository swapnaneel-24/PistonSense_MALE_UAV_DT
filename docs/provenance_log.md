# Project Provenance Log: Architectural Evolution & Decision History

**1. The Signal Processing Pivot: From Standard FFT to Crank-Angle Normalization**
* What was done: We discarded standard Fast Fourier Transform (FFT) vibration analysis in favor of Crank-Angle Domain Normalization and computed order tracking[cite: 1].
* Why it was done: Standard vibration analysis fails during the dynamic flight envelope (e.g., Takeoff to Cruise to Loiter) because the engine RPM changes constantly[cite: 1].
* What led to this: Rapid RPM changes cause mechanical frequencies to "smear" across the spectrum, masking early warnings of engine failure[cite: 1]. We realized anomaly detection must be "RPM-Invariant" to differentiate genuine structural faults from normal aeroelastic loads (like gyroscopic precession during steep banking)[cite: 1].

**2. The Thermodynamic Pivot: From Black-Box ML to Physics-Informed AI**
* What was done: We shifted from threshold-based anomaly detection to a Physics-Informed Baseline Twin (XGBoost Regressor) that dynamically calculates Thermal Residuals using Density Altitude (DA) and True Airspeed (TAS)[cite: 1].
* Why it was done: Traditional black-box Machine Learning ignores the non-linear thermal inertia of reciprocating machinery[cite: 1].
* What led to this: Standard systems trigger false alarms because they fail to account for the thermal phase-lag (CHT lagging behind EGT) and the severe drop in convective cooling at high loiter altitudes[cite: 1].

**3. The Telemetry Pivot: From Monolithic Architecture to Edge-to-Cloud Distributed Nodes**
* What was done: We split the monolithic Python application into two distinct nodes: a lightweight Edge Node (onboard the UAV) and a GCS Server Node (Ground Control Station) connected via encrypted MQTT[cite: 1].
* Why it was done: High-fidelity vibration sensors generate megabytes of raw data per second, creating a severe bandwidth bottleneck over constrained Line-of-Sight (LOS) RF or SATCOM links[cite: 1].
* What led to this: To make the system deployable, the Edge node must process the heavy Crank-Angle Normalization onboard and only transmit a highly compressed, kilobyte-sized "Health State Vector" to the ground[cite: 1].

**4. The Ingestion Pivot: From CSV Data to SocketCAN/Virtual CAN Integration**
* What was done: We architected the system to pipe X-Plane 12 simulation data into a Linux Virtual CAN interface (vcan0), reading it with the python-can library[cite: 1].
* Why it was done: SIH Problem Statement 26054 explicitly requires "CAN bus/Socket CAN-based engine data acquisition" interfacing with an ECU or FADEC[cite: 1].
* What led to this: We needed to prove our software is hardware-agnostic and "plug-and-play"; using vcan0 ensures the code requires zero changes for deployment on a physical MALE Drone's CAN bus[cite: 1].

**5. The Diagnostic Pivot: From Static Manuals to Temporal RAG & Explainable AI**
* What was done: We integrated Temporal (Time-Series) SHAP and a Flight-State-Aware Hybrid RAG system (BM25 + Dense Vector) constrained by strict "Physics Rule Adherence"[cite: 1].
* Why it was done: Static lookup tables and error codes are blind to the current flight state and thermal lags[cite: 1].
* What led to this: The RAG system must know if the drone is at 25,000 feet to warn of a shock-cooling hazard during descent, avoiding hallucinated recommendations and explaining time-lagged triggers (e.g., attributing a minute-45 overheat to a minute-43 throttle advance)[cite: 1].

**6. The SIH Rubric Pivot: Integrating Prognostics (RUL) and Dashboard Emulation**
* What was done: We expanded the scope to include Remaining Useful Life (RUL) estimation (using statistical models like Survival Analysis or Particle Filters) and a Visualization Dashboard with Mission Replay capabilities[cite: 1].
* Why it was done: The SIH Problem Statement mandated RUL tracking, mission replay, and a user interface to transition from reactive alarms to predictive diagnostics[cite: 1].
* What led to this: We broadened the systems-engineering scope to ensure every single rubric requirement of PS ID 26054 was met[cite: 1].

**7. The Hardware Emulation Pivot: Overcoming the Physical Hardware Requirement**
* What was done: We utilized Docker containerization, Linux cgroups (artificial resource constraining), and ONNX Runtime profiling[cite: 1].
* Why it was done: To mathematically prove that the Edge inference algorithms can run on a lightweight processor (like an NVIDIA Jetson Orin Nano or Raspberry Pi CM4) without actually possessing or purchasing the physical hardware[cite: 1].
* What led to this: The need to deliver a defense-grade "Functional prototype/software demonstrator" on a standard laptop while proving its edge-viability to the SIH judges during a live pitch[cite: 1].

## [2026-09-10] Phase 0 Completion, Proposal Finalization, & Defense Strategy Locked

**Objective:** Finalize the project scope, confirm GitHub rendering compatibility, and document the architectural defense strategy for SIH PS 26054.

**Key Decisions & Actions:**
* **Phase 0 (Scope Locking) Completed:** Officially bounded the project around the physical constraints of MALE UAVs, mandating Edge AI to bypass Line-of-Sight (LOS) RF bandwidth bottlenecks and using Physics-Informed AI to handle thermal inertia[cite: 2].
* **Dataset Strategy Solidified:** Confirmed a three-stream approach using X-Plane 12 SITL simulation (Stream A), synthetic multi-order fault injection (Stream B), and empirical domain logs for zero-shot validation (Stream C)[cite: 2].
* **Resource Base Locked:** Integrated definitive engineering textbooks (Heywood for thermodynamics, Busch for aviation mechanics, Randall for vibration monitoring, Rao for mechanical vibrations, and Si et al. for RUL) alongside key multimedia resources (Savvy Aviation, Steve Brunton, FlyRotax)[cite: 2].
* **Academic Defense Strategy Established:** Formulated a strict defense against "keyword salad" critiques by anchoring every algorithm to a physical necessity[cite: 2]. Specifically justified the Hybrid RAG system's necessity by its "Flight-State Awareness" and strict "Physics Rule Adherence" constraint to prevent hallucinated, physically destructive actions (e.g., ignoring shock-cooling hazards)[cite: 2].
* **Documentation Formatting:** Standardized the Project Pipeline and Proposal into a single defense-grade document. Resolved GitHub MathJax rendering quirks by converting list-bound block equations to inline LaTeX formulas.

---

## [2026-11-25] Approved master architecture and research provenance

**Status:** Project owner approved the consolidated architecture after ten design-review rounds. The earlier entries are preserved as historical planning records, not evidence of implementation or validation. The approved master framework supersedes conflicting assumptions.

### Research inspiration

Raghu (4 February 2024), [Tapas Drone Project Scrapped](https://peoplesdemocracy.in/2024/0204_pd/tapas-drone-project-scrapped), *People's Democracy*. Identified by the project owner as an early research influence; initial consultation date unknown. The article discusses funding, development difficulties and propulsion challenges. It is contextual commentary, not a technical specification or proof of current programme status; it distinguishes withdrawal of mission-mode funding from possible continued development. The approved demonstrator uses a generic civilian-representative observational simulation, not a specific operational military platform.

### Design review milestones

| Round | Decision and rationale |
|---|---|
| 1 | Five logical domains; separate experimentation, offline development and runtime; three execution modes. |
| 2 | Distinguish native, emulated, derived and reference data; immutable source recordings and separate experimental labels. Simulator capabilities and synthetic validity remain unverified. |
| 3 | Separate mechanical, thermal and prognostic research; grouped independent partitions, shared causal features, baseline comparisons; optimization conditional on evidence. |
| 4 | Multi-rate Edge, timestamp validation distinct from filtering, unwrapped angle distinct from cycle phase, configuration-aware analysis, independent thermal/mechanical evidence. EKF, Goertzel, CNN and quantization remain candidates. |
| 5 | Versioned contracts, canonical units, incident identities and revisions, explicit quality, MQTT and bounded idempotent recovery. Transport acknowledgement is not durable processing. |
| 6 | Four GCS layers; separate diagnostic evidence, health estimation, conditional RUL, model attribution and grounded advisories. SHAP is not causation and automated advisory checks are not certification. |
| 7 | Optional historical read-only ADQ with approved probes and resource admission; compare against routine and event-triggered alternatives. Computation success does not establish diagnostic usefulness. |
| 8 | Engineering investigation dashboard, synchronized replay, explicit stale/missing data. Distinguish dashboard playback and pipeline re-execution; 3D deferred. |
| 9 | Thin integration slice, staged development, feasibility gates, independent evaluation, risks and bounded LLM implementation tasks. |
| 10 | Approved master framework distinguishes architecture requirements, preferred candidates, conditional capabilities and deferred extensions. |

### Corrections to historical assumptions

Order tracking reduces speed-related smearing; phase wrapping does not correct drift and FFT remains a valid method. Thermal residuals are evidence, not unique diagnoses. Virtual CAN and laptop resource constraints do not establish physical hardware equivalence. Local information reduction must be measured; MQTT/TLS cannot guarantee zero loss. RUL requires independent degradation evidence and explicit endpoint assumptions. Earlier SIH compliance claims require an authoritative problem-statement audit. No implementation or benchmark is claimed complete.

### Reference audit

- Fyfe, K. R., and Munck, E. D. S. (1997), *Analysis of computed order tracking*, MSSP 11(2), 187–205. https://doi.org/10.1006/mssp.1996.0056
- Lundberg, S. M., and Lee, S.-I. (2017), *A Unified Approach to Interpreting Model Predictions*. https://proceedings.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html
- Es, S., James, J., Espinosa-Anke, L., and Schockaert, S. (2024), *RAGAs: Automated Evaluation of Retrieval Augmented Generation*. https://aclanthology.org/2024.eacl-demo.16/ (2023 preprint: https://arxiv.org/abs/2309.15217).
- Si, X.-S., Wang, W., Hu, C.-H., and Zhou, D.-H. (2011), *Remaining useful life estimation – A review on the statistical data driven approaches*, EJOR 213(1), 1–14. https://doi.org/10.1016/j.ejor.2010.11.018. Verified replacement reading lead for the unresolved Si et al. book citation.
- FAA-H-8083-32B: https://www.faa.gov/regulationspolicies/handbooksmanuals/aviation/faa-h-8083-32b-aviation-maintenance-technician
- Rotax official technical library: https://www.flyrotax.com/p/service/technical-documentation
- Savvy Aviation educational resources: https://www.savvyaviation.com/resources/
- Retain Heywood, Randall, Rao, Mike Busch, Steve Brunton and Rotax-Owner as learning leads; verify editions and specific lectures. ISO 11898 parts 1 and 2 are standards, not research papers; verify editions and applicability.
- No concrete empirical dataset is identified in v4.0. Verify availability, licensing, signal compatibility and independent evaluation before claiming external validation.

Bibliographic identities and selected landing pages were checked, not full-text scientific applicability. The original [cite: 1] and [cite: 2] markers remain historical placeholders with unresolved source mapping. Exact manual revisions and official SIH requirements remain pending.

The approved master framework was generated in the project conversation; this entry does not imply that it has been committed to the repository. Next steps remain requirements audit, configuration and measurement verification, and the approved integration milestone. No models, datasets, benchmarks or end-to-end tests are claimed complete.
