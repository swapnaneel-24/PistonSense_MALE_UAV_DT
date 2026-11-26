import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE_URL = "http://127.0.0.1:8086/api/v3"

def main(duration_sec: float = 15.0, interval_sec: float = 0.25) -> None:
    out_dir = Path("simulation/acquisition/pilot_logs")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # Read-only discovery of registered DataRefs (requires a flight loaded in X-Plane 12)
    resp = requests.get(f"{BASE_URL}/datarefs", timeout=5.0)
    resp.raise_for_status()
    payload = resp.json()
    entries = payload.get("data", payload) if isinstance(payload, dict) else payload

    registry_path = out_dir / f"dataref_registry_{stamp}.json"
    registry_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    name_to_id = {
        item["name"]: item["id"]
        for item in entries
        if isinstance(item, dict) and "name" in item and "id" in item
    }
    print(f"Discovered {len(name_to_id)} DataRefs -> {registry_path}")

    # Candidate names to inspect if present in the active session
    candidates = [
        "sim/cockpit2/engine/indicators/engine_speed_rpm",
        "sim/cockpit2/engine/indicators/MPR_in_hg",
        "sim/cockpit2/engine/indicators/CHT_deg_C",
        "sim/cockpit2/engine/indicators/EGT_deg_C",
        "sim/cockpit2/temperature/outside_air_temp_degc",
        "sim/flightmodel/position/true_airspeed",
        "sim/cockpit2/gauges/indicators/airspeed_kts_pilot",
        "sim/cockpit2/engine/indicators/fuel_flow_kg_sec",
        "sim/cockpit2/engine/indicators/oil_temperature_deg_C",
        "sim/cockpit2/engine/indicators/oil_pressure_psi",
    ]
    active = {k: name_to_id[k] for k in candidates if k in name_to_id}
    print("Matched candidate DataRefs:", list(active.keys()))

    csv_path = out_dir / f"readonly_telemetry_{stamp}.csv"
    fieldnames = ["utc_iso", "elapsed_s"] + list(active.keys())
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        t0 = time.monotonic()
        while (time.monotonic() - t0) < duration_sec:
            row = {
                "utc_iso": datetime.now(timezone.utc).isoformat(),
                "elapsed_s": round(time.monotonic() - t0, 4),
            }
            for k, dref_id in active.items():
                r = requests.get(f"{BASE_URL}/datarefs/{dref_id}/value", timeout=2.0)
                if r.ok:
                    val = r.json().get("data", r.json())
                    row[k] = val[0] if isinstance(val, list) and len(val) > 0 else val
                else:
                    row[k] = None
            writer.writerow(row)
            time.sleep(interval_sec)

    print(f"Saved read-only recording -> {csv_path}")

if __name__ == "__main__":
    main()
