# snl-model-builder-agent — Setup & Run Guide

---

## Prerequisites

- SLAC S3DF cluster account
- Python conda environment with TensorFlow:
  `/sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2`
- Anthropic API key (get one at https://console.anthropic.com → API Keys)

---

## Step 1 — Install the Anthropic SDK

Run once. Installs `anthropic` into the existing conda environment.

```bash
/sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2/bin/pip install anthropic
```

Verify it installed:

```bash
/sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2/bin/python -c "import anthropic; print(anthropic.__version__)"
```

Expected output: `0.118.0` (or newer)

---

## Step 2 — Set Your Anthropic API Key

Get your key from https://console.anthropic.com → API Keys → Create key.

**For the current terminal session only:**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**To make it permanent** (add to `~/.bashrc`):

```bash
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
source ~/.bashrc
```

> Replace `sk-ant-...` with your actual key.

---

## Step 3 — Run the Agent

Always run from the repo root:

```bash
cd /sdf/group/faders/users/adave/Projects/hlsBs-examples-dave
```

**Default task** — runs the full ex5 pipeline (csim → synthesis → package → IP):

```bash
/sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2/bin/python firmware/agent/agent.py
```

**Custom task** — describe what you want in plain English:

```bash
/sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2/bin/python firmware/agent/agent.py "Run csim for ex5 and report pass/fail"

/sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2/bin/python firmware/agent/agent.py "Full pipeline: train the MNIST model then run csim, synthesis, and IP generation"

/sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2/bin/python firmware/agent/agent.py "Change hidden units to 128, update Network.hh and retrain, then rebuild the IP"
```

**Verbose mode** — shows turn numbers and tool call details:

```bash
/sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2/bin/python firmware/agent/agent.py --verbose "Run synthesis and check for errors"
```

---

## Optional — Add a Shell Alias

Add to `~/.my_aliases.sh` for a shorter command:

```bash
alias snl-agent='/sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2/bin/python /sdf/group/faders/users/adave/Projects/hlsBs-examples-dave/firmware/agent/agent.py'
```

Then reload:

```bash
source ~/.my_aliases.sh
```

After that you can just run:

```bash
snl-agent "Run csim for ex5"
snl-agent --verbose "Full pipeline"
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `ANTHROPIC_API_KEY is not set` | Export your key: `export ANTHROPIC_API_KEY=sk-ant-...` |
| `ModuleNotFoundError: No module named 'anthropic'` | Run Step 1 again |
| `AuthenticationError` | Check your API key is correct and has credits |
| Agent says "bld_sub.sh always exits 0" | Normal — it is checking the output text for real errors |

---

## Files

```
firmware/agent/
  agent.py       — snl-model-builder-agent (main script)
  requirements.txt
  README.md      — architecture overview
  SETUP.md       — this file
```
