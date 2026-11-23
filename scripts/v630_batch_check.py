"""Score the 17 saved v630 feeding experiments from the 50 Hz Colab batch.

In the notebook that ran the experiments, call check_batch(config, params).
It reads one Parquet file at a time and writes a small CSV beside the inputs.

The reference spike counts come from Shiu et al.'s 30 one-second trials.
The observed fractions come from Supplementary Table 3, using the same
experimental line as Figure 2. The left MN9 readout is the primary score.

Article and supplementary data (CC BY 4.0) — https://doi.org/10.1038/s41586-024-07763-9
Original spike archive, v3.0 (MIT) — https://doi.org/10.17617/3.CZODIW
Figure 2 ID order — https://github.com/philshiu/Drosophila_brain_model/blob/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960/figures.ipynb
"""

from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


MN9_LEFT = 720575940660219265
MN9_RIGHT = 720575940645521262
TRIALS = 30
REFERENCE_SECONDS = 30.0  # Total exposure in the published run, per cell type.

# Cell type, fraction of flies extending the rostrum, total left and right spikes.
REFERENCE = (
    ("roundup", 1.0, 2385, 2480),
    ("diatom", 0.6, 874, 850),
    ("sink_sync", 0.2, 665, 683),
    ("G2N_1", 1.0, 371, 419),
    ("clavicle", 0.5, 315, 213),
    ("Fdg", 0.8, 676, 610),
    ("bract", 0.8, 1010, 757),
    ("rattle", 0.9, 56, 35),
    ("FMIn", 1.0, 11, 3),
    ("TH_VUM", 1.0, 1, 74),
    ("marge", 0.1, 0, 0),
    ("phantom", 0.6, 0, 0),
    ("tentacular", 0.5, 0, 0),
    ("usnea", 1.0, 0, 0),
    ("kitty", 0.0, 219, 326),
    ("peacock", 0.0, 0, 1),
    ("peahen", 0.0, 0, 1),
)


def count_spikes(path, experiment, trial_seconds):
    """Verify trial records and count left and right MN9 spikes by trial."""
    coverage = np.zeros(TRIALS, dtype=bool)
    counts = np.zeros((2, TRIALS), dtype=np.int64)
    fields = ["t", "trial", "flywire_id", "exp_name"]
    with pq.ParquetFile(path) as source:
        missing = set(fields) - set(source.schema_arrow.names)
        if missing:
            raise ValueError(f"Missing columns: {sorted(missing)}")
        for field in ("trial", "flywire_id"):
            if not pa.types.is_integer(source.schema_arrow.field(field).type):
                raise ValueError(f"{field} must contain exact integers.")
        for events in source.iter_batches(batch_size=65_536, columns=fields):
            time, trial, neuron, label = events.columns
            if any(column.null_count for column in events.columns):
                raise ValueError("A spike row has a missing value.")
            if label.unique().to_pylist() != [experiment]:
                raise ValueError(f"Internal experiment name differs from {experiment}.")
            times = time.to_numpy()
            if not np.all((times >= 0) & (times < trial_seconds)):
                raise ValueError("A spike time falls outside the configured trial duration.")
            trials = trial.to_numpy()
            if np.any((trials < 0) | (trials >= TRIALS)):
                raise ValueError(f"Found a trial ID outside 0 to {TRIALS - 1}.")
            trials = trials.astype(np.intp, copy=False)
            coverage[trials] = True  # Across every neuron, including the stimulated cells.
            ids = neuron.to_numpy()
            for side, root in enumerate((MN9_LEFT, MN9_RIGHT)):
                counts[side] += np.bincount(trials[ids == root], minlength=TRIALS)
    return coverage, counts


def check_batch(config, params):
    """Print the coverage and rate comparison, then return the saved CSV path."""
    folder = Path(config["path_res"])
    if not folder.is_dir():
        raise FileNotFoundError(f"Check the Drive mount and results folder: {folder}")
    seconds = float(params["t_run"])  # Brian2 time quantities convert to SI seconds.
    if not np.isfinite(seconds) or seconds <= 0:
        raise ValueError("Use the positive trial duration from the simulation cell.")
    if params["n_run"] != TRIALS or not np.isclose(float(params["r_poi"]), 50.0):
        raise ValueError("Use the settings from the completed 50 Hz, 30-trial batch.")
    print(f"Reading {folder} | {TRIALS} trials of {seconds:g} s | 50 Hz input")
    print("The current model inputs are", Path(config["path_comp"]).name,
          "and", Path(config["path_con"]).name)
    if not np.isclose(seconds, 1.0):
        print("The paper used 1 s trials. The duration differs in this comparison.")

    outcomes = {
        (True, True): "TP", (True, False): "FP",
        (False, True): "FN", (False, False): "TN",
    }
    rows = []
    for name, observed, published_left, published_right in REFERENCE:
        label = f"{name}_50Hz"
        row = {
            "cell_type": name, "status": "check", "detail": "", "trials_seen": None,
            "trials_expected": TRIALS, "trial_seconds": seconds, "stimulus_hz": 50,
            "observed_fraction": observed,
            "paper_left_hz": published_left / REFERENCE_SECONDS,
            "paper_right_hz": published_right / REFERENCE_SECONDS,
            "left_spikes": None, "right_spikes": None,
            "left_trials_fired": None, "right_trials_fired": None,
            "left_hz": None, "right_hz": None, "left_matches_paper_call": None,
            "left_vs_lab": None, "either_vs_lab": None,
        }
        rows.append(row)
        try:
            covered, counts = count_spikes(folder / f"{label}.parquet", label, seconds)
        except FileNotFoundError:
            row["detail"] = "File missing"
            continue
        except (OSError, pa.ArrowException, ValueError, TypeError) as error:
            row["detail"] = str(error)
            continue
        row["trials_seen"] = int(covered.sum())
        if not covered.all():
            missing_ids = np.flatnonzero(~covered).tolist()
            row["detail"] = f"No spike rows from any neuron for trial IDs {missing_ids}"
            continue
        left, right = (int(n) for n in counts.sum(axis=1))
        left_fired, right_fired = (int(n) for n in (counts > 0).sum(axis=1))
        row.update(
            status="ok", left_spikes=left, right_spikes=right,
            left_trials_fired=left_fired, right_trials_fired=right_fired,
            left_hz=left / (TRIALS * seconds), right_hz=right / (TRIALS * seconds),
            left_matches_paper_call=(left > 0) == (published_left > 0),
            left_vs_lab=outcomes[left > 0, observed > 0],
            either_vs_lab=outcomes[left + right > 0, observed > 0],
        )

    report = pd.DataFrame(rows)
    ok = report["status"].eq("ok")
    print(f"\n{ok.sum()}/{len(report)} files contain spike records for all {TRIALS} trials.")
    view = ["cell_type", "status", "trials_seen", "left_hz", "paper_left_hz",
            "right_hz", "paper_right_hz", "left_matches_paper_call", "left_vs_lab"]
    print(report[view].to_string(index=False, na_rep="—", float_format=lambda v: f"{v:.4f}"))
    if ok.any():
        passed = report.loc[ok]
        matches = int(passed["left_matches_paper_call"].sum())
        correct = int(passed["left_vs_lab"].isin(["TP", "TN"]).sum())
        print(f"\n{matches}/{len(passed)} left MN9 calls match the published model.")
        print(f"{correct}/{len(passed)} agree with the observed fly movement.")
    if not ok.all():
        print("\nFiles to inspect")
        print(report.loc[~ok, ["cell_type", "detail"]].to_string(index=False))

    dest = folder / "v630_50Hz_MN9_summary.csv"
    with NamedTemporaryFile(dir=folder, suffix=".tmp", delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        report.to_csv(temp_path, index=False)
        temp_path.replace(dest)
    finally:
        temp_path.unlink(missing_ok=True)
    print(f"\nSaved {dest}")
    return dest
