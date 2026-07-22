# snl-model-builder-agent

A Claude-powered agent that drives the SNL/hlsBs build system end-to-end: from
Python model training through C-simulation, RTL synthesis, and Vivado IP packaging.

---

## Architecture

```
User task (natural language)
        │
        ▼
  claude-opus-4-7  (adaptive thinking, cached system prompt)
        │
    tool_use loop
        │
   ┌────┴────────────┐
   │                 │
bash_exec         read_file / write_file
   │                 │
HLS commands      Network.hh, MLP.py, .cfg files
(hlsWs, hlsCfg,
 hlsRun, SnlBuild*)
```

**Three tools:**

| Tool | Purpose |
|------|---------|
| `bash_exec(command, example)` | Run any shell command with Vitis HLS 2025.1 + hlsBs + SNL sourced automatically |
| `read_file(path)` | Read cfg files, Network.hh, logs |
| `write_file(path, content)` | Update Network.hh, MLP.py, or patch a broken .cfg |

---

## Setup

### 1. Install dependencies

```bash
pip install anthropic
# or
pip install -r firmware/agent/requirements.txt
```

### 2. Set your Anthropic API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

```bash
cd /path/to/hlsBs-examples-dave

# Default task: run full ex5 pipeline
python firmware/agent/agent.py

# Custom task
python firmware/agent/agent.py "Run csim for ex5 and report pass/fail"

# Full pipeline with verbose output
python firmware/agent/agent.py --verbose "Train MNIST model then run full HLS build"

# Targeted tasks
python firmware/agent/agent.py "Check if SnlBuildAcquirerAll succeeded"
python firmware/agent/agent.py "Synthesis is done — run package and IP generation"
python firmware/agent/agent.py "Change hidden units to 128 in Network.hh and retrain"
```

---

## What the agent knows

The system prompt encodes all pipeline knowledge so the agent can recover from
errors automatically:

- **Stage order**: SnlBuildAcquirerAll → SnlBuildAdapter → hlsWs → hlsCfg → csim → synthesis → package → ip
- **bld_sub.sh bug**: always exits 0 — agent checks output for `fatal error:` / `make: ***`
- **csim pass criterion**: `NErrors/NRead = 0/N` is the only line that matters
- **Expected synthesis warnings**: II violation (Softmax) and stream deadlock are normal for `float`
- **SNL.py 'file'→'files' key bug**: agent knows the correct cfg entries and can write them directly
- **SetSnlNetwork.hh missing**: agent knows where to copy it from

---

## Adapting for a different model

Tell the agent in natural language:

```bash
python firmware/agent/agent.py \
  "Change the network to 128 hidden units and 5 output classes, \
   update Network.hh and train_mlp.py, then rebuild the IP"
```

The agent will:
1. Edit `firmware/ex5/include/Network.hh` (Layer0 output 128, Layer1 output 5)
2. Edit `firmware/ex5/train_mlp.py` (HIDDEN_UNITS=128, NUM_CLASSES=5)
3. Retrain the model
4. Run SnlBuildAdapter to rebuild the adapter for the new architecture
5. Run hlsCfg, csim, synthesis, package, ip

---

## Files

```
firmware/agent/
  agent.py          ← main agent (bash_exec / read_file / write_file)
  requirements.txt  ← anthropic SDK
  README.md         ← this file
```
