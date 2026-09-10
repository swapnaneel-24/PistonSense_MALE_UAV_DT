# **PROJECT PIPELINE FRAMEWORK: EDGE-TO-CLOUD DIGITAL TWIN FOR MALE UAV AERO PISTON ENGINES**&nbsp;&nbsp;

**SIH Problem Statement ID**: 26054&nbsp;

**Version**: 4.0 (Distributed Architecture & Hard-Physics Corrected)&nbsp;

**Objective**: An Edge-to-Cloud Digital Twin system for aero piston engine health monitoring, utilizing onboard Crank-Angle Domain Normalization to bypass RF bandwidth bottlenecks, and Physics-Informed Residual Analysis to account for thermodynamic phase-lags.&nbsp;

# **PHASE 0 — Engineering Scope Locking**

**Purpose:** Define the project around Rotordynamics, Aeroelasticity, Thermodynamic Cycles, and strict Line-of-Sight (LOS) RF bandwidth constraints tailored for a high-altitude MALE UAV.

**Actions:**

* **Scope Statement**: "Develop a distributed Digital Twin that estimates the expected state of a turbocharged piston engine and its Remaining Useful Life (RUL). The system detects anomalies by analyzing Thermal Residuals (Δ) and Sub-Harmonic Orders specific to 4-stroke combustion, executing high-frequency processing on an Edge node to satisfy UAV bandwidth limitations.".  
* **The "Cycle" Constraint:** Explicitly states that the algorithm accounts for Manifold Pressure, Density Altitude (DA), and True Airspeed (TAS) to mathematically isolate mechanical cooling failures from environmental load changes and high-altitude convective cooling drops.&nbsp;  
* **The "Telemetry" Constraint:** Mandate that all raw, high-frequency vibration data is processed onboard the aircraft, transmitting only a heavily compressed "Health State Vector" to the Ground Control Station (GCS).&nbsp;

**Output:** A scope document defining success as "Analytical Redundancy" functioning within the processing and transmission constraints of an autonomous edge-to-cloud aerospace environment.&nbsp;

**Decision point:** If the model cannot distinguish between "High CHT due to high Density Altitude and low convective airflow" (Normal) and "High CHT due to a mechanical cooling failure" (Fault) without streaming raw megabytes of data to the ground, the scope is invalid&nbsp;

# **PHASE 1 — Data Acquisition (The SITL/Simulation Strategy)**

**Purpose:** Acquire data that accurately represents high-altitude Internal Combustion Engine (ICE) physics and route it through a defense-grade ECU communication protocol, proving hardware-agnostic deployment.&nbsp;

**Stream A — Simulation Proxy & SocketCAN Ingestion (Primary)**&nbsp;

* **Tool**: X-Plane 12 (High-fidelity physics engine) piped into a Linux Virtual CAN bus (`vcan0`).&nbsp;  
* **Why**: X-Plane accurately models turbocharged piston engines (e.g., Rotax 914iS), including realistic CHT/EGT phase-lag and thin-air cooling efficiency. Piping this into `vcan0` via `python-can` ensures our software reads data exactly as it would from a real physical Engine Control Unit (ECU).&nbsp;  
* **Process**: Run automated scripted flights (Takeoff  → High-Altitude Climb → High-DA Loiter →Landing) while the Virtual CAN bus continuously broadcasts the telemetry.&nbsp;

**Stream B — Synthetic Noise Injection:**

**The "Physics" Injection**: Piston engines do not run smoothly. Inject synthetic vibration signatures into the simulated clean data:&nbsp;

* 1.0× and 2.0× Orders: Aeroelastic loads (gyroscopic precession and P-factor from high-pitch/yaw maneuvers) AND structural Propeller Imbalance.  
  * 0.5× and 1.5× Orders: Misfire and valve-train lash (Camshaft/Valve issues).  
  * High Frequency Broadband: Main bearing wear and mechanical friction.

**Stream C — Domain Logs (Validation):**

* **Action**: A synthetic "Digital Earth" dataset containing RPM, MAP, EGT, CHT, DA, TAS, and Vibration Channels, streaming dynamically through a SocketCAN interface.&nbsp;

**Output:** A synthetic "Digital Earth" dataset containing RPM, Manifold Pressure, EGT, CHT, Density Altitude, TAS, and Synthetic Vibration Channels.

**Decision point:** If the X-Plane 12 flight model fails to simulate engine choking at 25,000 ft, or if the data ingestion scripts fail to read from `vcan0`, the hardware-emulation setup is flawed.&nbsp;

# **PHASE 2 — Preprocessing (Order Tracking & Dual-Loop Transformation)**

**Purpose:** Execute high-frequency signal processing natively on the onboard UAV Edge computing module (e.g., simulated Jetson Orin Nano). Convert raw time-series telemetry into Order-Domain signals to handle RPM transients, thereby reducing megabytes of vibration data into a highly compressed sparse array suitable for RF transmission. .

**Action 1: Decoupled High-Fidelity Synthesis (The Spatial Nyquist Architecture)**

* **The Problem**: Standard flight simulators output scalar RPM values at a low frequency (\~20–60 Hz). At a 2400 RPM cruise, the engine cycles at 40 Hz, yielding roughly one sample per revolution—rendering direct high-resolution angular interpolation physically impossible.  
* **The Solution**: Implement a dual-loop framework. A low-frequency Control Loop tracks the vehicle’s macro-telemetry from X-Plane via UDP. These states instantaneously feed a high-frequency (10 kHz) software vibration generator in Python, bypassing simulator data rate limits.  
* **Fault Modeling**: To ensure the high-frequency loop represents reality, the generator utilizes Gaussian Pulse Synthesis for fault injection to mimic the sharp physical impact of a misfire or valve slap at a specific crank angle (ϕ):&nbsp;  
  $V_{\text{fault}}(\theta) = A \cdot \exp\left(-\frac{(\theta - \phi)^2}{2\sigma^2}\right)$

**Action 2: Drift-Corrected Crank-Angle Reconstruction**

* **The Challenge**: Accumulative numerical Euler integration introduces floating-point arithmetic errors that compound over long flight logs, causing the 720° cycle markers to drift.&nbsp;  
* **The Solution**: Synchronize the integration to the absolute system timestamp rather than a local loop step variable. Calculate the instantaneous angle θ(t) dynamically and clamp it via a strict modulo-720° tracking step:&nbsp;  
  $$\\theta(t) \= \\left( \\int\_{0}^{t} 6 \\cdot RPM(\\tau) d\\tau \\right) \\text{ mod } 720^\\circ$$  
* (Note: The constant 6 converts RPM directly to degrees per second. The modulo 720° zeroes out the phase counter every two complete crankshaft rotations to perfectly match a 4-stroke thermodynamic cycle)&nbsp;

**Action 3: Resampling (Time → Angle)**

* **The Process**: Using θ(t) as an unwavering reference clock, interpolate the raw high-frequency vibration data V(t) into constant degree intervals (e.g., exactly every 1° of crank rotation).  
* **Result**: Complete structural conversion from V(t) (Amplitude vs. Time) to V(θ) (Amplitude vs. Crank Angle), rendering the signal completely invariant to engine acceleration.

**Action 4: Sub-Harmonic Order Analysis**

* **The Algorithm**: Perform an Order Tracking FFT on the newly mapped Angle-Domain signal V(θ).  
* **The "Locked" Spectral Bins**:  
  * **Bin 0.5x**: Tracks the Camshaft/Valve Train sub-harmonics (half crankshaft speed) to isolate impulsive fault signatures like valve train slack.  
  * **Bin 1.0x**: Evaluates primary Crankshaft rotation unbalance against expected aerodynamic gyroscopic loading.  
  * **Bin 2.0x**: Captures secondary engine firing frequencies and aerodynamic vibration from 2-bladed propeller assemblies.

**Action 5: Health State Vector Generation (The Edge Output)**

* **The Process:** The Edge Node discards the heavy raw vibration data. It packages the magnitudes of the locked spectral bins (0.5×, 1.0×, 2.0×) alongside current macro-telemetry (CHT, EGT, RPM) into a lightweight JSON array.&nbsp;  
* **The Process:** The Edge Node discards the heavy raw vibration data. It packages the magnitudes of the locked spectral bins (0.5×, 1.0×, 2.0×) alongside current macro-telemetry (CHT, EGT, RPM) into a lightweight JSON array.&nbsp;

**Decision point:** Apply an automated cutoff filter when RPM reaches 0 to prevent division-by-zero structural exceptions during the complete engine shutdown sequence.&nbsp;

# **PHASE 3 — Edge Inference & GCS Prognostics (The Distributed Twin)**&nbsp;

**Purpose:** Implement the lightweight State Estimator on the UAV Edge node to generate Thermal Residuals ($\\Delta$) and detect Mechanical Faults, subsequently transmitting a compressed vector to the Ground Control Station (GCS) for RUL prognostics.&nbsp;

**Branch A — The Mechanical Ear (Edge Node 1D-CNN)**&nbsp;

* **Input**: The Order-Domain Spectrogram from Phase 2\.  
* Model: 1D Convolutional Neural Network (1D-CNN) compiled via ONNX Runtime for zero-overhead embedded inference.  
* **Logic**: The CNN scans the locked spectral bins. High 0.5× Amplitude indicates a localized Valve Train Fault or Cylinder Misfire, while High 1.0× Amplitude is evaluated against expected gyroscopic maneuver loads to isolate genuine Propeller Imbalance.&nbsp;

**Branch B — The Baseline Twin (Edge Node State Estimator)**

* **Model**: Gradient Boosting Regressor (XGBoost) optimized for Edge deployment.  
* **Input**: Current State (RPM, Manifold Pressure, Density Altitude, True Airspeed).&nbsp;  
* **Thermal Inertia Fix**: To account for the engine metal's thermal mass delay, the model utilizes time-series input arrays featuring Lagged Rolling-Average Features (e.g., `MAP_rolling_30s`, `RPM_rolling_45s`). This physically prevents the AI from mapping instantaneous throttle steps to impossible temperature jumps.&nbsp;  
* **Task**: Predict expected "Healthy" operational values:  
  *  $EGT\_{\\text{Predicted}} \= f(\\text{RPM}, \\text{MAP}, \\text{OAT}, \\text{Lagged\\\_Inputs})$  
  * $CHT\_{\\text{Predicted}} \= f(\\text{RPM}, \\text{MAP}, \\text{OAT}, \\text{Lagged\\\_Inputs})$

**Branch C — Thermal Residual Generation (Δ) & Secure Transmission**&nbsp;

* **Calculation**: Determine the thermodynamic delta vectors onboard the UAV :  
  * $\\Delta EGT \= EGT\_{\\text{Actual}} \- EGT\_{\\text{Predicted}}$  
  * $\\Delta CHT \= CHT\_{\\text{Actual}} \- CHT\_{\\text{Predicted}}$  
* **The Transient Invalidation Gate:** Temporarily suppress thermal anomaly alarms for $N$ seconds while the physical engine blocks establish a new steady-state thermal equilibrium if:  
  $\left| \frac{d(\text{RPM})}{dt} \right| > \text{Threshold} \quad \text{OR} \quad \left| \frac{d(\text{MAP})}{dt} \right| > \text{Threshold}$&nbsp;  
* Transmission: The Edge Node compresses the gated residuals ($\\Delta$) and Mechanical Ear scores into a lightweight Health State Vector, transmitting it to the GCS via TLS-encrypted MQTT to bypass RF bandwidth bottlenecks.

**Branch D — Remaining Useful Life (RUL) Prognostics (GCS Node)**&nbsp;

* **Model**: Statistical degradation tracking models (e.g., Survival Analysis or Particle Filters).  
* **Logic**: The GCS server ingests the MQTT Health State Vector and compares it against historical fleet-level telemetry. It maps degradation trends over time (e.g., slow accumulation of $\\Delta CHT$ indicating gradual cooling fin degradation) to predict the exact remaining flight hours before component failure.  
* **Decision point**: If the RUL model exhibits high variance, recalibrate the stochastic state-space filter parameters to better map the specific engine's baseline wear rate.

# **PHASE 4 — Methodological Evaluation (Synthetic Fault Injection & Emulation )**

**Purpose:** Validate the Edge hardware constraints, RF bandwidth limits, and thermodynamic physics models using high-fidelity Software-in-the-Loop (SITL) simulation.&nbsp;

**Action:**

* **Scenario 1 (Edge Resource Profiling):** Use Linux `cgroups` and ONNX profiling to artificially constrain the local processing environment, mimicking the exact CPU/RAM limits of an NVIDIA Jetson Orin Nano or Raspberry Pi CM4.&nbsp;  
  * *Check:* Verify that the Crank-Angle Normalization and 1D-CNN inference execute without crashing or inducing latency, mathematically proving edge-deployment viability.  
* **Scenario 2 (Thermal Lag & Leaning) :** Simulate a fuel flow restriction that shifts the combustion profile relative to Peak Exhaust Gas Temperature (Peak EGT).&nbsp;  
  * *Check:* Verify the system identifies the non-linear relationship between EGT and CHT. If entering a Lean-of-Peak (LOP) state, the system must detect a drop in EGT followed by a time-lagged drop in CHT. .  
* **Scenario 3 (Aeroelasticity vs. Mechanics) :** Superimpose a 1.0× and 2.0× order vibration curve that mathematically mirrors gyroscopic precession and P-factor bending moments during a high-pitch/yaw maneuver.  
  * *Check:* Verify the 1D-CNN filters expected aeroelastic propeller loading from a genuine mechanical unbalance or bearing failure.&nbsp;  
* **Scenario 4 (High-Altitude Convective Cooling) :** Hold engine power output constant while artificially decreasing True Airspeed (TAS) and increasing Density Altitude (DA) to reduce convective cooling mass airflow.&nbsp;  
  * *Check:* Verify the Baseline Twin predicts the natural CHT rise caused by thin air mass without triggering a false "thermal runaway" alarm.&nbsp;

**Output:** Edge latency metrics (Time-to-Detect) and Confusion Matrices for Fault Classification, rigorously validating both the hardware emulation and thermodynamic models.&nbsp;

# **PHASE 5 — Explainability & Hybrid RAG Advisory (The GCS Dashboard)**

**Purpose:** Generate operationally safe, context-aware troubleshooting checklists on the GCS server using a Flight-State-Aware LLM constraint, transitioning the system from reactive alerts to autonomous maintenance advisories.

**Explainability (Temporal SHAP):**

* Apply Temporal (Time-Series) SHAP to the Gradient Boosting component to map lagged feature importance. Identify exactly *when* a trigger occurred (e.g., outputting that a thermal overheat at minute 45 was caused by a rapid throttle advance 90 seconds prior due to thermal mass).

**The RAG Architecture Upgrade:**

* **Retrieval Layer:** *Hybrid Search (BM25 \+ Dense Vector)*. Combine a Dense Retriever for fuzzy operational symptoms with a Sparse Retriever (BM25) for strict alphanumeric strings (e.g., "Error E-504", "Rotax 914 Manual"). Rank via reciprocal rank fusion.  
* **Context Injection (The Flight Envelope Module):** Dynamically append Density Altitude (DA) and True Airspeed (TAS) into the prompt context. The LLM must differentiate between a safe CHT cooling profile at sea level and a severe shock-cooling hazard at 25,000 feet.&nbsp;  
* **Output Formatting (The Physics Constraint):** Inject a strict constraint: *"You are an autonomous systems mechanic. Do not output standard manned-aviation procedures. Account exclusively for uncrewed MALE Drone constraints. Output solutions exclusively as Markdown Checklists with \[IMMEDIATE ACTION\] priority markers. Forbid narrative paragraphs."*&nbsp;

  &nbsp;

* **RAG Metric Evaluation:**  
  * Integrate the RAGAS framework to continuously measure Context Recall and Context Precision to eliminate text generation hallucinations.&nbsp;  
  * **Physics Rule Adherence:** Implement a custom metric to heavily penalize the generation of any physically destructive recommendations (e.g., commanding a mixture enrichment when telemetry proves the engine is suffering from rich-induced spark plug fouling).&nbsp;

**Decision point:** If the RAG system indexes irrelevant documentation or violates thermodynamic principles (e.g., ignoring thermal shock at high DA), recalibrate the vector database similarity thresholds and tighten the prompt injection constraints.

# **PHASE 6 — Limitations & Gap Analysis**

**Purpose:** Define the boundaries, constraints, and operational limitations of the distributed Digital Twin architecture.

**Gap Categories:**

* **Hardware Emulation Fidelity:** While Docker containerization and `cgroups` mathematically prove processing viability, physical deployment requires validation on actual edge silicon (Jetson/CM4) interfacing with a physical CAN bus under severe drone vibrational profiles.&nbsp;  
* **Simulation Fidelity (SITL):** X-Plane 12 beautifully models macro-thermodynamics and atmospheric physics but cannot natively capture micro-structural manufacturing material variations (e.g., microscopic hairline cracks in a piston ring).&nbsp;  
* **Sensor Latency:** Physical thermocouples (CHT/EGT probes) suffer from their own inherent thermal phase lag. The current twin architecture assumes perfectly synchronized temporal data arrays from the virtual CAN bus.&nbsp;  
* **Combustion Chemistry:** The model treats fuel as an optimized energy source. It cannot detect physical fuel contamination (e.g., water in the fuel tank) until it physically alters the baseline thermal equilibrium of the cylinders.&nbsp;

**Output:** A "Deployment Conditions" constraints document.

**Decision point:** If the system is ported from the X-Plane 12 SITL environment to an operational aircraft (such as a Rotax 916iS) without recalibrating the baseline manifold pressure and SocketCAN ingestion protocols, the Thermal Residuals and Edge transmission pipelines will be completely invalid.&nbsp;

# **Key Technical Glossary**

* **Crank-Angle Domain Normalization:** The digital preprocessing technique of mathematically integrating scalar RPM data into an angular reference clock (0° to 720°) and resampling raw time-series vibration data against it. This transforms the dataset from the time domain to the angular domain, completely eliminating frequency smearing during rapid RPM transients.&nbsp;  
* **Sub-Harmonic Order Analysis:** The specific algorithmic identification of 0.5× and 1.5× order components within an Order-Tracking FFT. Because these frequencies represent fractions of the engine speed, they are structurally locked to the camshaft and valve train dynamics unique to a 4-stroke reciprocating internal combustion engine, making them primary indicators of misfires or valve lash errors.  
* **Aeroelastic & Gyroscopic Coupling:** The aerodynamic reality of a MALE Drone in flight, where steep banking, high-pitch, or high-yaw maneuvers induce gyroscopic precession and P-factor bending moments on the crankshaft. The diagnostic model must mathematically isolate these natural 1.0× and 2.0× order aerodynamic loads to prevent them from being misclassified as genuine mechanical unbalances or bearing failures.  
* **Thermal Residual Generation (Δ):** The real-time mathematical calculation of the difference between an engine's actual sensor readings (EGT_{\text{Actual}}, CHT_{\text{Actual}}) and the baseline states predicted by the Digital Twin model. This isolates true structural engine faults from normal thermal fluctuations caused by changing environmental variables (like Airspeed, Outside Air Temperature, or Density Altitude).  
* **Thermal Inertia Phase-Lag:** The physical property of engine metal blocks where Cylinder Head Temperature (CHT) changes lag significantly behind instantaneous Exhaust Gas Temperature (EGT) shifts due to thermal mass. The diagnostic pipeline accounts for this non-linear relationship (e.g., recognizing when an engine enters a Lean-of-Peak state, where EGT drops immediately but CHT drops tens of seconds later) to prevent false anomaly alarms.  
* **Temporal (Time-Series) SHAP:** An advanced explainability framework applied to the gradient boosting model that maps the importance of lagged features. Instead of only evaluating instantaneous data, it identifies specific time-delayed triggers for state changes (e.g., identifying that a thermal overheat at minute 45 was caused by a rapid throttle advance at minute 43).  
* **Analytical Redundancy:** A cyber-physical systems architecture where software-based mathematical models (the Digital Twin) continuously cross-check and validate physical hardware sensors. This virtual fault tolerance allows the system to accurately diagnose an engine failure even if a physical sensor malfunctions or reports erratic data.  
* **Convective Cooling Mass Airflow:** A critical thermodynamic variable for high-altitude MALE Drones. It measures the cooling efficiency over the engine block, which drops drastically at high Density Altitudes (DA). The system dynamically evaluates DA and True Airspeed (TAS) to predict baseline CHT rises, differentiating between normal high-altitude operation and severe thermal runaway or shock-cooling hazards.  
* **Software-in-the-Loop (SITL) Simulation:** A virtual testing methodology that utilizes high-fidelity flight simulation software running fully inside a computing environment to model aerodynamics, atmospheric conditions, and reciprocating engine physics. This allows for the generation of clean baseline telemetry and the safe script-injection of structural or thermodynamic faults.  
* **Flight-State-Aware Hybrid RAG:** An advanced information retrieval method combining Dense Vector (semantic meaning) and Sparse Keyword (BM25 for strict alphanumeric codes) search, dynamically injected with real-time MALE Drone telemetry (Density Altitude, TAS, Flight Phase). It incorporates a strict Physics Rule Adherence metric to ensure the LLM generates physically sound troubleshooting checklists without hallucinations or physically destructive commands.

&nbsp;

&nbsp;

&nbsp;

&nbsp;

# **PROJECT PROPOSAL**

# **1\. Project Statement**

**Title:** Piston-Sense: An Edge-to-Cloud Digital Twin System for Health Monitoring, Fault Prediction, and RUL Estimation of MALE UAV Aero Piston Engines&nbsp;

**SIH Problem Statement ID:** 26054&nbsp;

**Problem Statement:** Medium Altitude Long Endurance (MALE) UAVs are critical assets for ISR and strategic defence missions, relying heavily on turbocharged reciprocating piston engines for endurance. Current engine monitoring systems are threshold-based, reactive, and often fail during dynamic flight maneuvers or high-altitude operations. Furthermore, traditional systems face a severe bandwidth bottleneck: transmitting high-frequency vibration and telemetry data from a UAV to a Ground Control Station (GCS) over constrained Line-of-Sight (LOS) RF or SATCOM links is impossible due to strict bandwidth limits and frequent packet drops.

We propose an indigenous, scalable Edge-to-Cloud Digital Twin framework. By deploying lightweight, physics-informed AI (incorporating aeroelastic and thermodynamic modeling) on an onboard Edge computing node, the system mathematically reduces megabytes of raw data into a highly compressed, kilobyte-sized "Health State Vector". Pushing this vector to a GCS for Remaining Useful Life (RUL) prediction, RAG-based maintenance advisory, and mission replay, this system seamlessly transitions UAV maintenance from reactive threshold alarms to intelligent, predictive diagnostics.

---

# **2\. Detailed Description**

## **2.1 Context and Motivation**

* **The Telemetry & Bandwidth Bottleneck:** High-fidelity vibration sensors generate megabytes of raw data per second. Streaming this raw data to ground operators is physically unfeasible over standard UAV communication links. Analytics must execute directly at the Edge, interfacing locally with the UAV's Engine Control Unit (ECU).&nbsp;  
* **The "Aeroelastic & Transient" Challenge:** Standard Fast Fourier Transform (FFT) vibration analysis fails because engine RPM changes constantly across the flight envelope, causing mechanical frequencies to "smear" across the spectrum. Additionally, aggressive pitch/yaw maneuvers induce aerodynamic gyroscopic precession and P-factor bending moments that mimic the $1.0\\times$ and $2.0\\times$ order frequencies of a mechanical failure.&nbsp;  
* **The Thermodynamic Gap:** Engine block temperatures (CHT) do not rise instantly with Exhaust Gas Temperatures (EGT) due to the massive thermal inertia of reciprocating machinery. Standard threshold-based systems trigger false alarms because they ignore this temporal phase-lag and fail to account for the drastic loss of convective cooling mass airflow at high Density Altitudes (DA).&nbsp;  
* **The Prognostic Deficit:** Operators currently lack visibility into degradation trends. Without Remaining Useful Life (RUL) estimation, piston-engine failures often lead to unsafe recovery conditions, mission aborts, or asset loss.&nbsp;

## **2.2 Proposed Solution Overview (Distributed Architecture)**

To solve the RF bandwidth constraint and deliver real-time intelligence, the Digital Twin is split into two synchronized nodes:&nbsp;

**Node A: The Edge Intelligence Layer (Onboard UAV)**

* **Virtual CAN Ingestion:** Reads real-time telemetry (RPM, CHT, EGT, MAP, Oil Pressure/Temp, Fuel Flow, Battery/Alternator health, and Vibration) via SocketCAN, interfacing directly with the ECU/FADEC.  
* **The Mechanical Ear:** Runs high-frequency Crank-Angle Domain Normalization in real-time, feeding a lightweight 1D-CNN (compiled via ONNX Runtime) to classify structural faults while filtering out expected aeroelastic maneuver noise.&nbsp;  
* **The Thermal Twin:** A lightweight XGBoost regressor that dynamically tracks True Airspeed (TAS) and Density Altitude (DA) to calculate accurate Thermal Residuals ($\\Delta$), respecting thermal inertia without triggering false alarms during rapid throttle transients.&nbsp;  
* *Output: Transmits only a highly compressed, TLS-encrypted MQTT "Health State Vector" to the GCS, completely bypassing the RF bandwidth bottleneck.*

**Node B: The Ground Control Station (GCS Server / Cloud)**

* **RUL Prognostics Engine:** Analyzes incoming health vectors against fleet-level historical data using statistical degradation tracking models (e.g., Survival Analysis or Particle Filters) to predict degradation trends and estimate Remaining Useful Life.&nbsp;  
* **Temporal Explainability & RAG Advisory:** Utilizes Temporal (Time-Series) SHAP to explain exactly *when* a lagged variable triggered a fault. A Flight-State-Aware Hybrid RAG system (BM25 \+ Dense Vector) dynamically appends DA and TAS into the prompt context to generate uncrewed-safe Markdown troubleshooting checklists, governed by strict Physics Rule Adherence constraints.&nbsp;  
* **HMI Dashboard & Mission Replay:** An intuitive visualization interface for propulsion engineers, offering real-time parameter monitoring, 3D spatial mission replay, and time-lagged fault alerts.&nbsp;

&nbsp;

## **2.3 End-to-End Workflow**

* **Data Acquisition:** High-altitude telemetry is generated via X-Plane 12 SITL simulation and piped into a Linux Virtual CAN bus (`vcan0`) via the `python-can` library to simulate real-world hardware ingestion.  
* **Edge Processing:** The onboard script continuously evaluates the telemetry, calculating sub-harmonic mechanical orders ($0.5\\times$, $1.0\\times$, $2.0\\times$) and thermodynamic residuals.  
* **Secure Transmission:** Anomalies and compressed health vectors are transmitted to the ground via TLS-encrypted MQTT (e.g., Eclipse Mosquitto), ensuring zero packet-drop vulnerabilities over constrained data links.  
* **Predictive Analytics:** The GCS ingests the vector, updates the RUL trajectory, and triggers the Temporal SHAP / RAG pipeline if an anomaly crosses the stochastic degradation threshold.  
* **Visualization & Replay:** The operator views the engine's health status on the Dashboard, capable of rewinding the telemetry stream to replay the exact environmental conditions (e.g., Hot-weather operation, High-DA) that led to the fault.

&nbsp;

## **2.4 Why This Is a Supervised / Hybrid Learning Project**

* **Synthetic Labeling via SITL:** We utilize Software-in-the-Loop simulation to generate "ground truth" data. By artificially injecting specific complex faults (e.g., Lean-of-Peak fuel drops demonstrating thermal phase-lag, misfires, oil pressure drops), we create a rich, labeled dataset impossible to safely gather in the real world.  
* **Edge-Optimized Supervised Training:** The 1D-CNN and XGBoost models are trained on these labeled inputs to establish strict, physics-informed classification boundaries suitable for lightweight edge hardware deployment.&nbsp;  
* **Hybrid RAG & Unsupervised Prognostics:** The Edge node relies on supervised boundaries, while the GCS utilizes statistical state-space filtering for RUL and semantic search (Hybrid RAG) for context-aware maintenance planning.&nbsp;

---

# **3\. Project Objective**

To design and implement a scalable, indigenous Digital Twin system capable of:&nbsp;

* **Edge AI & Sensor Fusion:** Ingesting expanded sensor suites via CAN bus (SocketCAN) and performing lightweight, RPM-invariant mechanical and thermal anomaly detection directly onboard the UAV, effectively eliminating the RF telemetry bandwidth bottleneck.&nbsp;  
* **RUL Estimation:** Transitioning from reactive threshold alarms to predictive analytics by forecasting component degradation and estimating Remaining Useful Life using historical mission data.&nbsp;  
* **Context-Aware Advisories:** Providing physics-constrained maintenance instructions via a Flight-State-Aware Hybrid RAG system capable of explaining time-lagged fault triggers (Temporal SHAP) without hallucinating physically destructive commands.  
* **Comprehensive HMI Visualization:** Delivering a secure, interactive GCS dashboard that supports real-time monitoring, trend analysis, and historical mission replay for post-flight analysis.

---

# **4\. Deliverables**

&nbsp;

| \# | Deliverable | Description |
| :---- | :---- | :---- |
| 1 | **SocketCAN Data Ingestion Module** | Python architecture to read/simulate ECU telemetry (RPM, Temps, Oil, Fuel, Battery, Vibration) using vcan0 and the python-can library. |
| 2 | **Edge Inference Engine** | The onboard lightweight processing pipeline, containing the Crank-Angle preprocessor, 1D-CNN (Mechanical), and XGBoost Baseline (Thermal).&nbsp; |
| 3 | **Prognostics & RUL Module** | A GCS-side stochastic degradation tracking algorithm that calculates the Remaining Useful Life (RUL) of critical engine sub-systems |
| 4 | **Hybrid RAG Advisory System** | A LangChain-based system utilizing Temporal (Time-Series) SHAP and Hybrid Vector search to generate uncrewed-safe maintenance checklists.&nbsp; |
| 5 | **GCS Visualization Dashboard** | An interactive user interface displaying real-time engine health indices, predictive fault alerts, RUL trends, and spatial Mission Replay capabilities.&nbsp; |
| 6 | **Synthetic SITL Dataset** | A comprehensive labeled dataset generated via X-Plane 12 containing high-altitude flight telemetry and physically injected faults.&nbsp; |
| 7 | **Secure Telemetry Pipeline** | Implementation of a TLS-encrypted MQTT broker to facilitate low-bandwidth, drop-resistant Edge-to-GCS communication.&nbsp; |
| 8 | **System Architecture Document** | Detailed technical documentation, Edge/Cloud deployment roadmap, and RAGAS metric evaluation reports focusing on Physics Rule Adherence.&nbsp; |

---

# **5\. Novelty & Desired Innovation Areas Addressed**

* **1\. Edge AI & Secure Telemetry:** By mathematically reducing raw vibration data via Crank-Angle Domain Normalization natively at the edge, the system circumvents the MALE UAV LOS RF bandwidth bottleneck. This enables real-time mechanical monitoring over standard encrypted MQTT data links.&nbsp;  
* **2\. Physics-Informed Thermodynamic Modeling:** Instead of relying on instantaneous black-box AI, the system models the physical phase-lag between EGT and CHT. By dynamically tracking Density Altitude (DA), it calculates real-time convective cooling efficiency, preventing false thermal alarms at high loiter altitudes where air density drops drastically.&nbsp;  
* **3\. Explainable AI (Temporal RAG):** The system maps time-lagged variables via Temporal SHAP to explain *when* an anomaly was triggered. It utilizes a strict "Physics Rule Adherence" constraint to prevent the LLM from hallucinating unsafe actions (e.g., ignoring a severe shock-cooling hazard during a rapid descent).&nbsp;  
* **4\. Simulation & Mission Replay:** The integration of Software-in-the-Loop (SITL) not only generates ground-truth training data but serves as the backbone for the post-flight mission replay dashboard. This allows propulsion engineers to visually simulate how environmental factors (Hot-weather operation, High-DA) degraded the engine over a specific flight path.&nbsp;

# **6\. Project Outcome**

A working, prototype of the Piston-Sense Digital Twin that demonstrates:

1. **Robust Onboard Edge Processing:** Successful ingestion of CAN bus data and accurate detection of misfires, injector abnormalities, and gyroscopic loads using lightweight AI algorithms optimized for embedded hardware.  
2. **Predictive Reliability:** Accurate calculation of Remaining Useful Life (RUL) and degradation trends over simulated long-endurance missions.  
3. **Operational Utility:** An intuitive GCS Dashboard that visualizes real-time health, replays historical flights, and outputs specific, actionable RAG maintenance advisories based on the current flight state.  
4. **Hardware Scalability:** A modular Edge-to-Cloud architecture designed for immediate deployment on standard UAV ground control stations and flight computers.

---

**7\. Proposed Datasets and Resources**

## **7.1 Primary Datasets & Data Streams**

Because classified, high-rate flight recorder data from operational military MALE UAVs is inaccessible, this project implements a multi-stream data strategy combining high-fidelity physical simulation, synthetic fault injection, and open-source domain telemetry.

&nbsp;

| Dataset / Stream | Type | Description & Specific Operational Purpose |
| :---- | :---- | :---- |
| **Stream A: SITL High-Altitude Simulation Telemetry** | Synthetic Flight Data (X-Plane 12\) | Scripted multi-phase flights (Takeoff→Climb  Loiter→Descent→Landing) modeling turbocharged reciprocating engines (Rotax 914 / Turbo-Lycoming). **What it is for:** Capturing clean baseline parameters (RPM, Manifold Pressure, CHT, EGT, Oil Temp/Pressure, Fuel Flow, Battery/Alternator) under varying Density Altitudes (DA) and True Airspeeds (TAS) to train the Baseline Twin. |
| **Stream B: Synthetic Multi-Order Fault Injection Set** | Synthetically Corrupted Data | Artificially injected fault signatures superimposed onto clean simulated baselines: **1.0× & 2.0× Orders:** Structural propeller unbalance vs. gyroscopic maneuver loads. **0.5× & 1.5× Orders:** Camshaft valve lash and misfires. **Broadband High-Frequency:** Main bearing degradation. **Thermodynamic Drift:** Lean-of-Peak fuel restrictions modeling CHT/EGT phase-lag and convective cooling losses. **What it is for:** Providing labeled ground truth for supervised training of the 1D-CNN classifier and calibrating the LSTM Autoencoder residual threshold. |
| **Stream C: Empirical Piston UAV Domain Logs** | Empirical Reference Logs | Real-world telemetry collected from experimental fixed-wing gas UAVs and small aircraft engine test benches. **What it is for:** Serving strictly as an out-of-distribution validation set (zero-shot test) to ensure the trained neural models generalize beyond synthetic simulation boundaries. |

&nbsp;

## **7.2 Technical Manuals & Maintenance Repositories (RAG Knowledge Base)**

These documents form the unstructured text and vector corpus indexed by the Hybrid Search (BM25 \+ Dense Vector) module to generate context-aware maintenance checklists.

* **Rotax 914 / 916 iS Line and Heavy Maintenance Manuals (MML / MMH):**  
  * *What it is for:* Supplies authoritative alphanumeric diagnostic codes (e.g., E-series errors), torque limits, structural clearances, and component overhaul intervals required for precision keyword retrieval (BM25).  
* **Rotax Fault-Finding Manual for 912/914/916 Series:**  
  * *What it is for:* Provides OEM diagnostic trees and troubleshooting tables for symptoms like rough engine running, sudden CHT rise, low oil pressure, and turbocharger wastegate failures.  
* **FAA-H-8083-32B (Aviation Maintenance Technician Handbook – Powerplant, Volume 1 & 2):**  
  * *What it is for:* Serves as the generalized domain foundation for 4-stroke aero-engine mechanics, ignition harness continuity, spark plug fouling patterns, and fuel metering systems.  
* **OEM Service Bulletins (SBs) & Airworthiness Directives (ADs):**  
  * *What it is for:* Ingests critical recurring field issues (e.g., exhaust valve sticking, fuel rail vapor lock, turbocharger oil coking) into the vector store to prioritize high-risk failure modes.

## **7.3 Foundational Engineering Textbooks (Self-Study & Theoretical Grounding)**

These authoritative references and video lectures establish the physical laws underlying your digital twin's algorithms and provide real-world mechanical context for your data streams.

#### **Core Textbooks**

* ***Internal Combustion Engine Fundamentals*** **(John B. Heywood):**  
  * **What it is for:** Grounding the Baseline Twin in combustion stoichiometry, cylinder heat transfer equations, and manifold air density dynamics across altitude regimes.  
* ***Mike Busch on Engines: What Every Aircraft Owner Needs to Know About the Mechanics of Piston Aircraft Engines*** **(Mike Busch):**  
  * **What it is for:** Practical aviation thermodynamics—specifically mapping CHT thermal mass/inertia, Lean-of-Peak (LOP) vs. Rich-of-Peak (ROP) combustion curves, and rapid descent shock-cooling mechanics.  
* ***Vibration-based Condition Monitoring: Industrial, Aerospace and Automotive Applications*** **(Robert Bond Randall):**  
  * **What it is for:** Algorithmic foundation for Crank-Angle Domain Normalization, angular resampling, and computed order tracking to prevent spectral smearing during engine acceleration.  
* ***Mechanical Vibrations*** **(Singiresu S. Rao):**  
  * **What it is for:** Deriving structural vibration modes, isolating 1.0×/2.0× unbalance frequencies, and calculating gyroscopic moment coupling on rotating propeller shafts.  
* ***Prognostics and Health Management: A Guide on Reliability Engineering, Predictive Maintenance and Dynamic System Modeling*** **(Xiao-Sheng Si et al.):**  
  * **What it is for:** Statistical degradation modeling, stochastic drift filtering, and survival analysis algorithms implemented in the GCS Remaining Useful Life (RUL) engine.

#### **High-Yield YouTube Channels & Video Lectures**

* **Savvy Aviation Webinars (Mike Busch):**  
  * **What it is for:** Outstanding video breakdowns of real flight-recorder data analyzing EGT/CHT phase lags, valve sticking, spark plug fouling, and deciphering engine telemetry.  
* **Steve Brunton (University of Washington):**  
  * **What it is for:** Premier engineering video lectures on Physics-Informed Neural Networks (PINNs), Dynamical Systems, Fast Fourier Transforms (FFT), dynamic mode decomposition, order tracking, and data-driven modeling.  
* **Rotax-Owner / FlyRotax Official Channel:**  
  * **What it is for:** Direct mechanical video teardowns of Rotax 912/914/916 series engines showing dry-sump oil paths, dual carburetors/injectors, turbo-wastegate controllers, and ECU wiring.

## **7.4 Key Research Papers & Technical Literature**

These papers substantiate the novel machine learning and signal processing methods cited in the project proposal.

* **Computed Order Tracking (COT):**  
  * *Reference:* Fyfe, K. R., & Munck, E. D. S. (1997). "Analysis of computed order tracking." Mechanical Systems and Signal Processing, 11(2), 187–205.  
  * *What it is for:* Theoretical backing for integrating variable shaft speed $\\theta(t) \= \\left( \\int\_{0}^{t\_{\\text{sim}}} 6 \\cdot \\text{RPM}(t) \\, dt \\right) \\pmod{720^\\circ}$ time-series vibration data into stationary angular cycles.  
* **Time-Series Explainable AI (Temporal SHAP):**  
  * *Reference:* Lundberg, S. M., & Lee, S.-I. (2017). "A Unified Approach to Interpreting Model Predictions." NeurIPS.  
  * *What it is for:* Justifies mapping feature contributions across lagged time steps to explain thermal inertia delays (e.g., attributing a minute-45 overheat to a minute-43 throttle transient).  
* **RAG Evaluation Architecture:**  
  * *Reference:* Es, S., et al. (2023). "Ragas: Automated Evaluation of Retrieval Augmented Generation." arXiv:2309.15217.  
  * *What it is for:* Defining mathematical metrics for Context Recall, Context Precision, and enforcing custom Physics Rule Adherence constraints against hallucinated maintenance procedures.  
* **Edge AI for UAV Prognostics:**  
  * *Reference:* ISO 11898-1/2 (Controller Area Network standard) and ONNX Runtime Technical Specifications.  
  * *What it is for:* Standardizing the communication interface between onboard Linux SocketCAN abstractions (vcan0) and lightweight edge-compiled ONNX models.

## **7.5 Software Tools, Virtualization & Hardware-Emulation Resources**

These engineering tools allow full prototype development, validation, and benchmarking on a standard workstation without requiring physical edge silicon.

* **Simulation & Ingestion Stack:**  
  * X-Plane 12 \+ NASA XPC / UDP SDK: Generates 60 Hz aero-propulsion telemetry under atmospheric variations.  
  * Linux SocketCAN (vcan0) & python-can: Emulates the physical aircraft CAN bus / ECU broadcast interface.  
* **Edge Containerization & Resource Constraints:**  
  * Docker & Linux cgroups: Limits local CPU cores (--cpus="2.0") and RAM (--memory="3g"), proving edge suitability on hardware classes equivalent to an NVIDIA Jetson Orin Nano or Raspberry Pi CM4.  
  * ONNX Runtime (C++ / Python): Compiles PyTorch/XGBoost models for zero-overhead inference on embedded ARM/x86 architectures.  
* **Telemetry Link & Server Stack:**  
  * Eclipse Mosquitto (MQTT with TLS): Handles low-bandwidth, encrypted transmission of compressed Health State Vectors from Edge to GCS.  
  * FastAPI & React / Streamlit HMI: Serves diagnostic endpoints and renders the operator dashboard with 3D flight parameter replay.  
* **Online Engineering Lecture & Teardown Channels:**  
  * Savvy Aviation Webinars (Mike Busch): Detailed real-world flight recorder breakdowns analyzing CHT/EGT phase lags, valve sticking, and spark fouling.  
  * Steve Brunton (University of Washington): Video lectures on dynamic mode decomposition, order tracking, and physics-informed machine learning.  
  * FlyRotax / Rotax-Owner Technical Channel: Video maintenance teardowns showing dry-sump lubrication routes, dual-carburetor/injector balances, and ECU wiring.