# Ablation report, Cloud Shell read summary

Cloud Shell read summary, NOT a verbatim copy of the raw file.
The raw file is ablation_report.txt, 669 bytes, dated 2026-10-27,
in Cloud Shell at ~/pa_final4/priorauth-agent/eval/. It was NOT
transferred back locally, so its exact formatting is NOT claimed
here. The values below are the values reported from that file and
from the full and no-citation runs.

Full system (citation verification on), 30/30: criterion 171/200,
case 28/30, false-ready 0/25, missing-evidence recall 12/14,
citation 89/89, cost $0.0784 script estimate.
No-citation arm (verification off), 30/30: criterion 173/200,
case 28/30, false-ready 0/25, missing-evidence recall 12/14,
citation 90/90, cost $0.0751 script estimate.
Delta (full minus no-citation): criterion accuracy -0.01, case
readiness accuracy 0.0, false-ready rate 0.0, citation precision
0.0 (rate), missing-evidence recall 0.0.
Plain conclusion, as reported: citation verification did NOT
demonstrably help on this 30-case set. Do NOT claim it improved
accuracy or prevented a false-ready decision on this run.
