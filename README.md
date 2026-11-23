# Do revisions to a fly's brain map change which feeding responses it predicts?

I reran a published fruit-fly brain model on its original wiring map, v630. For 16 of the 17 cell types I tested, it gave the same yes/no prediction as the paper. The remaining case, TH_VUM, came down to one spike in the published run and none in mine.

The next experiment compares those results with v783, a later release of the same brain reconstruction. I'll recover neurons whose identifiers changed between releases and repeat any changed predictions on both maps. The v630 reproduction is complete. The v783 simulations are planned.

## Result so far

Each cell type received 50 Hz input for 30 one-second trials. The panel includes all 14 cell types that triggered rostrum extension in the lab, plus kitty, peacock and peahen. Rostrum extension is movement of one part of the proboscis, the fly's feeding tube. In the tables, "fed" refers to observed rostrum extension.

I scored a predicted response when the left MN9 motor neuron, as labelled by the authors, fired at least once across the batch. Two published true positives had mean left MN9 rates below 1 Hz. Only TH_VUM changed its any-spike prediction in my v630 rerun.

FMIn fired 18 spikes in 10 of my 30 trials. It remained positive under the any-spike rule in both datasets. With a threshold above 1 Hz, my run and the published run both detect 8 of the 14 observed responses. That threshold is a sensitivity check.

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

The SD column describes variation between individual trials. Dividing it by the square root of 30, about 5.5, estimates the standard error of the batch mean under independent sampling. "Same prediction?" compares my binary call with the published call, using the unrounded spike counts.

Diatom varied widely, with a mean near 30 Hz and an SD near 33 Hz. Left MN9 fired in all 30 trials, while right MN9 fired in 12. G2N_1 averaged 9.2 Hz against the paper's 12.4, and sink_sync averaged 26.7 against 22.2. Both kept the same binary prediction. The size and cause of those rate differences need further checking.

TH_VUM's right MN9 response was 2.6 Hz. Its left-side miss therefore depends on which motor neuron is used for scoring.

## The published benchmark

Shiu and colleagues tested 106 cell types by optogenetic stimulation and compared observed rostrum extension with simulated MN9 activity. At 50 Hz model input, they reported 101 correct predictions. [Figure 2 and Supplementary Table 3](https://doi.org/10.1038/s41586-024-07763-9)

| Model prediction | Real flies fed | Real flies did not feed |
|---|---:|---:|
| Feeding | 10 | 1 |
| No feeding | 4 | 91 |

Only 14 of the 106 cell types triggered the movement. An always-negative prediction would score 92 of 106, so I also report how many responses the model detected and how many false positives it produced. In the published screen, those counts were 10 of 14 responses and one false positive.

The first notebook rebuilds these counts from all 106 rows of the paper's spreadsheet (`notebooks/01_fly_feeding_baseline.ipynb`). My panel of 17 cell types matched observed movement on 11 of 17 cases. The published model matched 12 of those same 17.

## How the score depends on scoring choices

Using left MN9 above 0 Hz reproduces the published screen's counts, including the five extra false positives reported at 200 Hz. I use that as the primary rule. Taking activity on either side changes the published 50 Hz score from 101 to 99 because peacock and peahen each had one right MN9 spike across 30 trials, about 0.033 Hz.

I'll also score each batch at a threshold above 1 Hz and using either MN9. The comparison will show which changes depend on the threshold or side chosen.

## Method

I used the authors' leaky integrate-and-fire model with the v630 data and neuron lists from `sez_neurons.pickle`. Each listed neuron received 50 Hz Poisson input, with 30 trials of 1 second per cell type. The primary readout was left MN9, FlyWire ID 720575940660219265. Side names follow the authors' dataset labels, whose orientation differs from the physical fly. [Model and code](https://github.com/philshiu/Drosophila_brain_model)

The batch took about two hours on free Google Colab. Most cell types took 6 to 9 minutes, while diatom, with 14 stimulated neurons, took about 17. Joblib printed worker-stopped warnings. I checked the saved output before analysing it.

The independent checker, `scripts/v630_batch_check.py`, reads each raw spike file, checks trial coverage and spike times, and counts both MN9 outputs by trial. All 17 files contain records for all 30 trial IDs. Its summary, `results/v630_50Hz_MN9_summary.csv`, agrees with the rate table above.

The upstream `run_exp` at commit `91bdd1e` has no seed argument and does not record seeds. These batches are unseeded. Fresh batches will use new simulation calls, with that limitation recorded in their metadata.

## Comparing with v783

The following protocol is fixed before my v783 simulations.

1. Run roundup first to check the v783 pipeline, then FMIn. Both retain their original input IDs. Each gets 30 one-second trials at 50 Hz using `Completeness_783.csv` and `Connectivity_783.parquet`.
2. Match the changed input neurons to the v783 snapshot. Across the full 106-cell inventory, 63 types retain every original ID, 38 retain some and five retain none. Record the evidence for each match, including splits, merges and exclusions. Stimulate the verified counterparts of the original input set. Left MN9 retains its ID. Right MN9 needs a verified replacement for the either-side check. An unresolved match is recorded as unavailable.
3. Prioritise TH_VUM for recovery. Its only input ID changed, and the earlier v783 screen omitted it. Compare both MN9 outputs once their identities are verified. Use marge as a secondary check, comparing its surviving input alone with both recovered inputs on v783. Its v630 result was zero even with both neurons, so zero in both v783 conditions remains a possible result.
4. Complete the remaining matched members of the 17-cell panel. Use my completed 30-trial v630 batch as the primary baseline and keep the published values as a reference.
5. For every cell type whose primary call flips between releases, run one fresh 30-trial batch on each release. A flip is confirmed in a second batch only when the fresh v630 and v783 calls each reproduce their first-batch calls. Otherwise report it as unconfirmed and record which release failed to repeat: v630 only, v783 only, or both. A v630 call that does not repeat points to a fragile original prediction; a v783 call that does not repeat points to a fragile release effect. Keep each batch separate when applying the any-spike rule and stop after this scheduled confirmation pair.
6. Report the four outcomes against the lab observations as stayed correct, stayed wrong, improved or worsened. Give the matched denominator and exclusions, and attach the confirmation status to every flip. Show mean rates, total spikes and trials containing a spike alongside the binary calls.

A repeated flip provides evidence of repeatability under this protocol. Establishing statistical significance would require an additional analysis. Zero spikes in 30 trials also leaves uncertainty about rare responses. The rate differences and sensitivity checks will be reported with their observed variation.

## Limitations

Both releases describe the same scanned fly. This comparison measures sensitivity to revisions of that reconstruction. Transfer to another animal remains an open question.

The 17-cell panel was selected to include observed responses and known problem cases. The other 89 types were negative in both the original model and lab screen. A broader claim about new false positives would require testing those cases too.

The simulation uses predicted neurotransmitter identities to assign connection signs. Replacing the released data can change more than a neuron's identifier. I'll record the exact input files and model settings, and describe any difference as a release effect until its cause has been checked. The planned comparison covers 50 Hz stimulation.

## Related work

Suifei's flywire-fly-lab reported a v783 feeding screen in commit 2dd2641 on 19 September 2026. It used three trials per condition and agreed with the published model on 100 of 101 tested cell types. FMIn was the disagreement, with 0 Hz against the paper's approximately 0.37 Hz. Its code retains only original input IDs still present in v783. It therefore excludes TH_VUM, Salivary_MN13, bamboo, gallinule and meteor, and stimulates reduced sets for partly changed types, including one marge neuron, three kitty neurons and 13 diatom neurons. [Experiment and code](https://github.com/suifei/flywire-fly-lab/commit/2dd26416f1894ac575430b16945cd4fe1973a6a9) · [Results](https://github.com/suifei/flywire-fly-lab/blob/main/results/screen/sufficiency/summary.json)

In my v630 batch, FMIn fired in 10 of 30 trials. Of the possible selections of three distinct trials, about 28% contain no spikes. That calculation illustrates how a short batch can miss this response. A 30-trial v783 batch will give a more informative comparison, while uncertainty about a release effect remains.

This project adds recovery of changed neuron IDs, 30 trials per condition, and a confirmation rule committed before my v783 results. It compares the same intended biological inputs across releases and checks whether a changed call recurs in a fresh batch.

A November 2026 preprint by Asis studies odour learning in a whole-brain model based on Shiu et al.'s. Its v783 validation drops connections with fewer than five synapses and flips the signs of 44 antennal-lobe neurons, reporting reproduction of 8 of 13 benchmark results. Those model changes need to be considered when comparing its results with the original. [Preprint](https://arxiv.org/abs/2611.09930)

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

The raw files support analysis without repeating the simulation. Point `config['path_res']` at `results/raw_v630` to run the checker on the saved output.

## Reproducing the results

1. Open `notebooks/02_v630_reproduction.ipynb` in Google Colab.
2. Run the setup cells to install dependencies and load the model and `sez_neurons.pickle`.
3. Mount Google Drive and set `config['path_res']` to a Drive folder.
4. Run the batch cell. The runner skips existing experiment files. After an interruption, check those files before resuming.
5. Run the comparison cell to write `v630_reproduction_17.csv`.
6. Upload `scripts/v630_batch_check.py` to Colab and call `check_batch(config, params)` to write `v630_50Hz_MN9_summary.csv`.

The completed run used Python 3.13.18 in Colab, Brian2 2.11.0 and the authors' code at commit `91bdd1e`. Save each release and repeat batch in its own folder so an existing filename cannot cause a confirmation run to be skipped. Drive retains finished files, but a disconnect can lose the experiment currently running.

## Credits

The FlyWire Consortium reconstructed the brain. [Dorkenwald et al., Nature (2024)](https://doi.org/10.1038/s41586-024-07558-y)

Shiu and colleagues developed the model and collected the experimental comparison data. The supplementary data used here are licensed under CC BY 4.0. [A Drosophila computational brain model reveals sensorimotor processing, Nature (2024)](https://doi.org/10.1038/s41586-024-07763-9)

I reproduced the v630 benchmark and checked how its score depends on the readout. Matching and comparing releases is the next stage. I used AI assistance for planning, code and writing, including the Avoid AI Writing plugin for this README. I ran the completed simulations in Colab and checked the results against the published data.
