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