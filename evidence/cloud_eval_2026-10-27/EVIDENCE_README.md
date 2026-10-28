# Evidence directory: cloud evaluation, 2026-10-27

Read this file first. It states exactly what is and is not in
this directory.

## Verified inclusion record, updated 2026-10-27 (user upload)

The original raw evaluation files ARE included in this release,
unchanged, in the subdirectory `raw/` of this directory.
They were supplied by the user as PriorAuth_Raw_Evidence.zip,
extracted, and verified locally before copying: sizes match
the Cloud Shell records exactly, and hashes match the Cloud
Shell records exactly for six files. See the baseline hash
note below; that note is about a prior recorded hash string,
not about a change to the file.

Previous limitation wording ("Cloud Shell reads, 2026-10-27,
not local raw files") is SUPERSEDED by this record and must
not be quoted as the current state. The summaries in this
directory remain as summaries; the raw files in `raw/` are
the authoritative evidence.

## Cloud Shell source

Path in Cloud Shell: ~/pa_final4/priorauth-agent/eval/
Project: delivery-experience-511901. Model: gemini-3.5-flash.
Model location: global. Data location: us-central1.
Run window: 2026-10-27, 9:59 AM to 1:12 PM ET.
No standalone .log files were found in the Cloud Shell
project directory.

## Raw files included, unchanged, in `raw/`

- ablation_report.txt, 669 bytes, sha256 9e9c38d444b3b3ec59a3c03eef38637f0b3ab25e1722e5f14ad06403aa528154
- false_ready_report.txt, 188 bytes, sha256 d9630f92ebf0aa140a15dedac0636146a2da1bc845be4d1b21163049e9925ef7
- results_baseline.json, 104563 bytes, sha256 ba360bd79a319777f9183b0377579dae3b6025ee68347ebe2e05d825bf9bedf2
- results_no_citation_check.json, 475447 bytes, sha256 afd54544eb2cb866bd840308120c3c8f2fe99afe49d124286083b6467acacce7
- results_pilot.json, 52038 bytes, sha256 48756dd82c256562e23b30de80c284b1995f2035f060f2c261688a98e9320140
- results_real.json, 475878 bytes, sha256 d6869b0598bb741559da0b6aa1f430af72bf096fbc2a97a57cc3346381dad2f7
- results_real_partial14.json, 199995 bytes, sha256 b4248e9b966332aaa7a3d13997205be5ba462ad0fdce11b28cde10bef66a3030
- results_baseline_corrected.json, 116872 bytes, sha256 ed13f335aff8b1452a8419b39b33e1fa63e35a31710f18d115caff1d60986ff9 (corrected baseline rerun, 2026-10-27, 30/30, criterion 176/200, case 8/30, false-ready 18/25)

## Baseline hash note, read carefully

Six files match their previously recorded 64-character
sha256 hashes exactly. The seventh, results_baseline.json,
does NOT match the hash string recorded in earlier notes,
because that recorded string is only 63 characters long:
it is missing one '7' at position 28 (recorded
...037759d... versus actual ...0377579d...).
A 63-character string cannot be a sha256 hash.
The actual baseline file is consistent across the user
upload, the local verification copy, and the copy in
`raw/` (all three give the hash above), its size is
exactly 104563 bytes as recorded in Cloud Shell, and
its contents recompute to the reported baseline metrics
(see RAW_VERIFICATION_AND_RECOMPUTATION_2026-10-27.md).
The file was NOT altered to match the erroneous recorded
string. The correct hash to use from now on is the one
listed above.

## Credential scan

A credential grep over the raw files in `raw/` found
0 matches for: password, api_key, private_key,
service_account, AIza, ya29, BEGIN PRIVATE, secret,
bearer. Nothing was removed and no substantive record
was altered. Field names such as token_usage are usage
counters, not credentials.

## What else is in this directory

- aggregate_metrics.md, ablation_report_summary.md,
  false_ready_report_summary.md, per_case_readiness_summary.md:
  summaries from Cloud Shell reads, retained for readability.
  They are NOT substitutes for the raw files, and where a
  summary and a raw file disagree, the raw file wins.
- `raw/`: the eight files listed above, unchanged.
- The ablation and false-ready text files in `raw/` ARE the
  original 669-byte and 188-byte files, not summaries.

## Recomputation

scripts/recompute_metrics.py reads results_real.json, results_baseline.json, results_no_citation_check.json, and results_baseline_corrected.json from `raw/` (or from this directory if placed there),
recomputes the metrics from the rows, compares them to
the metrics embedded in the same files, and reports any
mismatch, never silently adjusting it. Run it as:
  python3 scripts/recompute_metrics.py --evidence-dir evidence/cloud_eval_2026-10-27/raw
One genuine mismatch was found and is documented, not
hidden: the baseline embedded token total is 0/0, while
its rows sum to 12020 prompt tokens and 4874 candidate
tokens (see the recomputation doc). The corrected baseline file recomputes cleanly (OK) on every compared field, including by-procedure results, failures list, tokens, latency, and cost. All other recomputed
values match the embedded metrics exactly, using the
repo's own percentile method (p50 = sorted[n//2],
p95 = sorted[int(n*0.95)]).

## Transfer history, for the audit trail

Browser download and Drive upload attempts in 2026-10-27
failed because the browser agent cannot access its own
Downloads folder or pick a local file for upload; a
private Drive folder was created but remained empty.
Those attempts did not produce these files. These files
came from the user's direct upload of
PriorAuth_Raw_Evidence.zip, verified as above.

## Corrected baseline rerun, 2026-10-27: raw file NOW included

The corrected baseline raw file, results_baseline_corrected.json
(116,872 bytes, SHA-256 ed13f335aff8b1452a8419b39b33e1fa63e35a31710f18d115caff1d60986ff9),
IS in raw/ in this pack, copied byte-for-byte from the user upload
of the Cloud Shell original at ~/pa_baseline_rerun/priorauth-agent/eval/
and recomputed from its rows (see corrected_baseline_summary_2026-10-27.md
in this directory for its metrics, comparison, cap/spend record,
and recomputation result). The original baseline raw file in
raw/results_baseline.json is kept unchanged and is labeled SUPERSEDED.
