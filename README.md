# Do revisions to a fly's brain map change which feeding responses it predicts?

A fruit fly extends its feeding tube (the proboscis) when certain neurons fire. Shiu and colleagues (2024) built a model of the whole fly brain from the FlyWire wiring map and used it to predict which groups of neurons can trigger that movement. They then tested those predictions in living flies.

The wiring map has since been corrected and re-released. This project asks whether those corrections change the model's predictions, and if so, whether the predictions get closer to what real flies do.

**Status:** Part 1 (reproducing the published model on the original map, v630) is done. Part 2 (matching neurons across releases and rerunning on v783) is in progress.

## Result so far

I reran the published model on FlyWire v630 for 17 cell types: the 14 that triggered feeding in real flies, the model's one false alarm (kitty), and two cases near zero (peacock and peahen). Each was stimulated at 50 Hz for 30 runs of 1 second, using the authors' code.

**My runs agreed with the paper on 16 of the 17 cell types.** The one disagreement was TH_VUM. In the paper it counted as a correct prediction because the motor neuron fired a single spike across all 30 runs. In my runs it fired none.

If "predicts feeding" means the motor neuron fires above 1 Hz rather than at all, my results and the paper's give the same 8 hits out of 14. Every disagreement sits below 1 Hz, where a few random spikes decide the outcome. So the model's main predictions reproduce reliably, but 2 of the paper's 10 hits (FMIn and TH_VUM) depend on a handful of random spikes.

| Cell type | Real flies (fraction that fed) | Paper, left MN9 (Hz) | My run, left MN9 (Hz) | Run-to-run SD (Hz) | My run, right MN9 (Hz) | Same prediction? |
|---|---:|---:|---:|---:|---:|:---:|
| roundup | 1.0 | 79.50 | 78.77 | 7.33 | 82.27 | yes |
| diatom | 0.6 | 29.13 | 30.47 | 33.07 | 30.73 | yes |
| sink_sync | 0.2 | 22.17 | 26.67 | 9.11 | 27.60 | yes |
| G2N_1 | 1.0 | 12.37 | 9.17 | 4.78 | 9.73 | yes |
| clavicle | 0.5 | 10.50 | 10.00 | 2.62 | 6.73 | yes |
| Fdg | 0.8 | 22.53 | 22.90 | 4.91 | 20.93 | yes |
| bract | 0.8 | 33.67 | 32.60 | 4.85 | 24.23 | yes |
| rattle | 0.9 | 1.87 | 2.57 | 2.14 | 1.37 | yes |
| FMIn | 1.0 | 0.37 | 0.60 | 1.02 | 0.17 | yes |
| TH_VUM | 1.0 | 0.03 | 0.00 | 0.00 | 2.60 | **no** |
| marge | 0.1 | 0.00 | 0.00 | 0.00 | 0.00 | yes |
| phantom | 0.6 | 0.00 | 0.00 | 0.00 | 0.00 | yes |
| tentacular | 0.5 | 0.00 | 0.00 | 0.00 | 0.00 | yes |
| usnea | 1.0 | 0.00 | 0.00 | 0.00 | 0.00 | yes |
| kitty | 0.0 | 7.30 | 6.93 | 2.25 | 11.00 | yes |
| peacock | 0.0 | 0.00 | 0.00 | 0.00 | 0.03 | yes |
| peahen | 0.0 | 0.00 | 0.00 | 0.00 | 0.13 | yes |

"Run-to-run SD" is how much the firing rate varied between single runs. The uncertainty on each 30-run average is roughly that figure divided by 5.5. "Same prediction?" uses the paper's rule: the model predicts feeding if the left MN9 fires at all.

Other things worth noting:

- **diatom varies a lot between runs** (mean 30 Hz, SD 33 Hz). The left MN9 fired in all 30 runs, but at very different rates, and the right MN9 fired in only 12 of 30. I haven't looked into why yet.
- **G2N_1 (9.2 vs 12.4 Hz) and sink_sync (26.7 vs 22.2 Hz)** differ from the paper by a bit more than random variation alone would suggest. Neither changes the prediction. It could be chance across 17 comparisons, or a difference in software versions. I've reported it rather than leaving it out.
- **TH_VUM drives the right MN9 (2.6 Hz) but barely the left.** The miss depends on which side's neuron is used as the readout.

## The published benchmark

Shiu and colleagues compared the model with experiments on 106 cell types at 50 Hz stimulation ([Figure 2 and Supplementary Table 3](https://doi.org/10.1038/s41586-024-07763-9)):

| Model prediction | Real flies fed | Real flies did not feed |
|---|---:|---:|
| Feeding | 10 | 1 |
| No feeding | 4 | 91 |

That's 101 of 106 correct. Only 14 of the 106 cell types made real flies feed, though, so a model that always predicted "no feeding" would already score 92 of 106. The more useful numbers are **10 of 14 real responses caught, with 1 false alarm**.

I first rebuilt this table from the paper's spreadsheet and checked all 106 rows against the original file (`notebooks/01_fly_feeding_baseline.ipynb`).

## How the score depends on scoring choices

The paper counts a predicted feeding response when the left MN9 motor neuron fires at all. Two things I checked:

- **Counting either MN9 (left or right) lowers the score from 101 to 99.** Two extra cell types, peacock and peahen, become false alarms. Their right MN9 fired at 0.033 Hz in the paper's data, which is one spike across 30 runs. With an "any spike" threshold, one stray spike turns a correct "no" into a wrong "yes".
- **Raising the threshold to 1 Hz** removes those noise-level cases. On the paper's own numbers, that gives 8 hits out of 14 instead of 10.

For the comparison between map versions, I'll report the paper's rule (left MN9 above 0 Hz) as the main result, so it can be compared directly with the original. I'll also report the 1 Hz threshold and the either-side readout as checks. If a change between maps only shows up under one rule, I'll call it fragile.

## Method

- **Model:** the authors' leaky integrate-and-fire model and code ([philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model)), unchanged.
- **Map:** FlyWire v630, the release used in the paper.
- **Stimulation:** 50 Hz random (Poisson) input to every neuron in the cell type, using the authors' neuron lists from `sez_neurons.pickle`.
- **Runs:** 30 runs of 1 second per cell type, the same as the paper.
- **Readout:** left MN9 (FlyWire ID 720575940660219265), as labelled by the authors. FlyWire data is mirror-flipped compared with the real fly, so "left" here is the dataset's label, not necessarily the fly's left side.
- **Compute:** free Google Colab. Each cell type took 6 to 9 minutes, except diatom (14 stimulated neurons), which took 17. The 17 took about 2 hours in total.
- **Checks:** joblib logged "worker stopped" warnings during the runs, so I confirmed that every results file contains all 30 runs before using it. A separate script (`scripts/v630_batch_check.py`) reads the raw spike files directly, checks every trial is present and every spike time is within the trial, counts MN9 spikes run by run, and compares them with the spike counts from the paper. Its output (`results/v630_50Hz_MN9_summary.csv`) agrees with the table above.

## Next: comparing with the corrected map (v783)

1. **Match neurons across releases.** FlyWire neuron IDs change when proofreading edits a neuron. Of the 106 cell types, 63 keep all their neuron IDs in v783, 38 keep some, and 5 keep none. The left MN9 kept its ID, but the right MN9 did not. Each cell type will be recorded as matched cleanly, partly matched, or excluded, with the reason.
2. **Set the rule for a "real change" before looking at v783.** This is based on the run-to-run variation measured on v630.
3. **Rerun the same 17 cell types on v783** with identical settings, then sort each into: stayed correct, stayed wrong, improved, or got worse.

## Limitations

- Both map releases come from the same single fly, so this tests how sensitive the model is to corrections of that one map. It says nothing about how well the model would work on a different fly.
- I've rerun 17 of the 106 cell types. The other 89 are cases where both the real flies and the model showed no response.
- Only the 50 Hz stimulation setting is tested.
- Neurotransmitter identities (which decide whether each connection excites or inhibits) are machine-learning predictions in the original model. I haven't changed them, so errors there aren't tested here.

## Related work

A November 2026 preprint by Asis ([arXiv:2611.09930](https://arxiv.org/abs/2611.09930)) studies odour learning in a whole-brain model based on Shiu et al.'s. As a validation step, it runs a modified version of the model on v783: connections with fewer than 5 synapses are dropped, and the sign of 44 antennal-lobe neurons is flipped. With those changes it reports reproducing 8 of 13 benchmark results from Shiu et al. Because the map and the model change together there, the effect of the map corrections alone can't be separated out. This project changes only the map version and keeps the model exactly as published, so any difference can be put down to the map corrections.

## Repository contents

```
notebooks/
  01_fly_feeding_baseline.ipynb    rebuilds the published table from the paper's spreadsheet
  02_v630_reproduction.ipynb       runs the model on 17 cell types and compares with the paper
scripts/
  v630_batch_check.py              checks the raw spike files and scores them against the paper
results/
  fly_feeding_50hz_predictions.csv     published rates with left / either classifications
  fly_feeding_input_id_inventory.csv   which neuron IDs survive from v630 to v783
  v630_reproduction_17.csv             my v630 rates vs the paper's (table above)
  v630_50Hz_MN9_summary.csv            spike-count check of the same 17 runs
  raw_v630/                            raw spike output, one .parquet file per cell type (about 9 MB in total)
```

The raw spike files mean the comparison and the check script can be rerun without repeating the 2-hour simulation: point `config['path_res']` at `results/raw_v630`.

## Reproducing the results

1. Open `notebooks/02_v630_reproduction.ipynb` in Google Colab.
2. Run the setup cells (install, load the model, load `sez_neurons.pickle`).
3. Mount Google Drive and set `config['path_res']` to a Drive folder so results survive a disconnect.
4. Run the batch cell. Finished cell types are skipped automatically, so it can be restarted.
5. Run the comparison cell to produce `v630_reproduction_17.csv`.
6. Upload `scripts/v630_batch_check.py` to the Colab session and run `check_batch(config, params)` to produce `v630_50Hz_MN9_summary.csv`.

Software versions: Python 3.13.18 (Google Colab), Brian2 2.11.0, authors' code at commit `91bdd1e`.

## Credits

- **Brain map:** the FlyWire Consortium, Dorkenwald et al. (2024), *Nature*. [doi:10.1038/s41586-024-07558-y](https://doi.org/10.1038/s41586-024-07558-y)
- **Model, code and experimental data:** Shiu et al. (2024), *A Drosophila computational brain model reveals sensorimotor processing*, *Nature*. [doi:10.1038/s41586-024-07763-9](https://doi.org/10.1038/s41586-024-07763-9). Supplementary data used under CC BY 4.0.
- **My contribution:** reproducing the benchmark, checking how it depends on scoring choices, and comparing predictions across map releases.

I used an AI assistant to help plan the project and write code. I ran every simulation myself and checked the results against the published data.
