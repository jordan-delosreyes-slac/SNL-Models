# snl-model-builder-agent — Example Prompts

Run from the repo root after activating the conda env:
```bash
conda activate rogue_v6.6.2
cd /sdf/group/faders/users/adave/Projects/hlsBs-examples-dave
```

---

## Full End-to-End Pipelines

```bash
# MLP on MNIST (ex5 reference example)
snl-agent "Train the MNIST MLP in ex5 and run the full HLS pipeline: csim, synthesis, package, and IP. Report resource utilization and timing."

# New CNN project from scratch
snl-agent "Create a new project in firmware/agent/agent_ml_training0. Build a 3-layer CNN on MNIST, generate the training script, Network.hh, and project config. Train the model, run csim, synthesis, package, and IP generation. Report resource and timing results."

# CNN with specific architecture
snl-agent "Create a project in firmware/agent/agent_ml_training0 with a CNN that has: Conv2D(8 filters, 3x3), MaxPooling2D(2x2), Conv2D(16 filters, 3x3), MaxPooling2D(2x2), Dense(64, ReLU), Dense(10, Softmax). Train on MNIST, then run the full HLS pipeline."
```

---

## Training Only

```bash
snl-agent "Train the MNIST MLP in ex5 and report final test accuracy"

snl-agent "Create a CNN training script in firmware/agent/agent_ml_training0, train it on MNIST for 10 epochs, and report accuracy"

snl-agent "Retrain the ex5 model with 128 hidden units instead of 64"
```

---

## Generate Files for a New Network

```bash
# Generate Network.hh from a trained model
snl-agent "Inspect the trained model at firmware/ex5/data/mnist_mlp.keras and generate the correct Network.hh"

# Create all project files from scratch
snl-agent "Create firmware/agent/agent_ml_training0 with: training script (3-layer CNN, MNIST), Network.hh, and project config CNN.py. Do not run the pipeline yet."

# Update an existing Network.hh
snl-agent "Change the first Conv layer in firmware/agent/agent_ml_training0/include/Network.hh from 8 to 16 filters and rebuild the adapter"
```

---

## Run a Single Pipeline Stage

```bash
snl-agent "Run SnlBuildAcquirerAll and check it succeeded"

snl-agent "Run SnlBuildAdapter for firmware/ex5/include/Network.hh"

snl-agent "Run hlsWs --create for ex5"

snl-agent "Run hlsCfg --create for ex5 and show the generated cfg file"

snl-agent "Run csim for ex5 and report pass/fail"

snl-agent "Run synthesis for ex5 and report LUTs, FFs, DSPs, BRAMs, and whether timing is met"

snl-agent "Run package and IP generation for ex5 and confirm the zip was created"
```

---

## Diagnose and Fix Problems

```bash
snl-agent "csim is failing for ex5 — read the cfg file, find what is wrong, and fix it"

snl-agent "SnlBuildAdapter failed — check the output and fix the error"

snl-agent "Check if the ex5 cfg file has the correct tb.file and syn.file entries, fix if missing"

snl-agent "Synthesis completed — show me the full resource utilization and timing summary"
```

---

## Modify an Existing Network

```bash
snl-agent "Change the MLP hidden units in ex5 from 64 to 128, update Network.hh and train_mlp.py, retrain the model, then rebuild the IP"

snl-agent "Add a second Conv layer to firmware/agent/agent_ml_training0/include/Network.hh and rerun the pipeline from SnlBuildAdapter"

snl-agent "Change the FPGA clock period in ex5 from 5ns to 4ns and rerun synthesis"
```

---

## Resource and Timing Reports

```bash
snl-agent "Run synthesis for ex5 and give me a table of: LUTs used, Flip-Flops, DSP blocks, BRAMs, and worst negative slack"

snl-agent "Compare resource usage between a 64-unit and 128-unit hidden layer — run synthesis for both and report"
```

---

## Tips

- Be specific about the **project path** when working outside ex5
- The agent will use `project_config=` automatically for new directories not in `setup_env.sh`
- Add `--verbose` to see turn numbers and tool calls:
  ```bash
  snl-agent --verbose "Run csim for ex5"
  ```
- If a stage fails the agent will diagnose and retry automatically
