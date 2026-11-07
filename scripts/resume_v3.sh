#!/bin/sh
# Resume evidence-access v3 after the 402 credit stop (amendment 02). Stops at the first failure.
set -u
cd /root/projects/witness
E=research/experiments/20261101-evidence-access-v3
A=$E/adjudications
C=$E/gates/corpus-v3
run() {
  echo "== $1 start $(date -u +%FT%TZ)"
  .venv/bin/python scripts/check_credit.py "$2" || { echo "STOP: credit below $2 for $1"; exit 1; }
  shift 2
  .venv/bin/python -m swarm_lab.evidence_access.audit --stage 3 --corpus $C --live "$@" || { echo "STOPPED"; exit 1; }
  echo "== done $(date -u +%FT%TZ)"
}
run sol 4.48 --model openai/gpt-6.1-sol --out $E/runs/stage3-gpt-6-1-sol-02 \
  --continue-from $E/runs/stage3-gpt-6-1-sol-01 --batch-ceiling 4.48 --amendment $A/protocol-amendment-02/amendment.md
run gemini 0.50 --model google/gemini-3.8-flash --out $E/runs/stage3-gemini-3-8-flash-02 \
  --continue-from $E/runs/stage3-gemini-3-8-flash-01 --batch-ceiling 0.50 --amendment $A/protocol-amendment-01/amendment.md
run sonnet 15 --model anthropic/claude-sonnet-5.5 --out $E/runs/stage3-claude-sonnet-5-5-01 \
  --batch-ceiling 15 --amendment $A/protocol-amendment-01/amendment.md
echo ALL_DONE
