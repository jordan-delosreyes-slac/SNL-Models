# ex5 — MNIST MLP: From Training to FPGA IP

End-to-end walkthrough: train a small neural network in Python, describe it in
C++ using the SNL library, simulate it in HLS, and package it as a Vivado IP.

---

## Overview

The pipeline has two phases:

```
Phase 1 – Python (CPU)
  train_mlp.py  →  mnist_mlp.keras   (trained weights)
                →  mnist_test.npy    (test inputs for simulation)
                →  mnist_golden.npy  (expected outputs for checking)

Phase 2 – HLS build
  Network.hh         (C++ network description, mirrors the Python model)
  project/MLP.py     (project config: FPGA, data paths, IP name, …)
        │
  SnlBuildAcquirerAll   (one-time: builds runtime data loaders)
  SnlBuildAdapter       (per-network: builds the HLS test adapter)
        │
  hlsWs  →  hlsCfg  →  hlsRun --csim  →  hlsRun --synthesis
         →  hlsRun --package  →  hlsRun --ip
        │
  products/ip/2025.1/Network-f0.zip   (Vivado IP catalog archive)
```

---

## Prerequisites

| Requirement | Where |
|-------------|-------|
| Linux (x86_64) | SLAC S3DF cluster |
| Vitis HLS 2025.1 | `/sdf/group/faders/tools/xilinx/2025.1` |
| Python with TensorFlow/Keras | conda env below |
| `hlsBs-examples-dave` repo (with submodules) | your clone |

**Conda env with TensorFlow:**
```bash
/sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2/bin/python
```
(or any Python 3.x env that has `tensorflow`, `numpy`)

**Clone the repo with all submodules:**
```bash
git clone --recurse-submodules <repo-url> hlsBs-examples-dave
```
If already cloned without submodules:
```bash
git submodule update --init --recursive
```

---

## One-Time Personal Setup

Create `~/.my_aliases.sh` with these two aliases:

```bash
# ~/.my_aliases.sh

# hlsLocate: tell hlsBs where the Xilinx tools are.
# Set `version` first, then run hlsLocate.
alias hlsLocate='export HLSBS_XILINX_SETUP=/sdf/group/faders/tools/xilinx/${version}'

# hlsbs-dave: source the project environment (defines exSelect, SNL paths, hls commands).
alias hlsbs-dave="source /path/to/hlsBs-examples-dave/firmware/scripts/setup_env.sh"
```

Then add to `~/.bashrc`:
```bash
if [ -f ~/.my_aliases.sh ]; then
    . ~/.my_aliases.sh
fi
```

> **Adjust the path** in `hlsbs-dave` to wherever you cloned the repo.

---

## Per-Terminal Setup (run every new shell)

These three commands must be run in order at the start of every session before
any `hls*` command will work:

```bash
version=2025.1 ; hlsLocate    # (1) point to the Xilinx install
hlsbs-dave                    # (2) source the project env  (defines exSelect, SNL_ROOT, hls* functions)
hlsVersion 2025.1             # (3) activate the Vitis toolchain
```

Then select the ex5 example project:
```bash
exSelect ex5
```

---

## Step 1 — Train the Model

```bash
cd firmware/ex5
/sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2/bin/python train_mlp.py
```

`train_mlp.py` trains a 2-layer MLP on MNIST and writes three files to `ex5/data/`:

| File | Contents | Used by |
|------|----------|---------|
| `mnist_mlp.keras` | trained weights (Keras v3 format) | SNL constants acquirer (csim/cosim) |
| `mnist_test.npy` | 100 test images, shape (100,28,28,1) float32 | SNL data acquirer |
| `mnist_golden.npy` | model predictions, shape (100,10) float32 | csim checker (pass/fail) |

**Key parameters at the top of `train_mlp.py`** (keep in sync with `Network.hh`):
```python
HIDDEN_UNITS = 64   # Layer0 Dense output size
NUM_CLASSES  = 10   # Layer1 Dense output size  (10 MNIST digits)
N_SAMPLES    = 100  # test images saved to mnist_test.npy / mnist_golden.npy
```

---

## Step 2 — Define the Network in C++ (`include/Network.hh`)

The C++ file describes the same network architecture as `train_mlp.py`, using
SNL template types. HLS synthesizes this into RTL.

**Architecture (must mirror the Python model exactly):**
```
Input  (28×28×1 float)
  └─ Layer0: Dense(784→64, ReLU,    float weights)
       └─ Layer1: Dense(64→10,  Softmax, float weights)
```

Key things to match when adapting for your own model:

| `train_mlp.py` | `Network.hh` |
|----------------|-------------|
| `HIDDEN_UNITS = 64` | Layer0 output units `64` |
| `NUM_CLASSES  = 10` | Layer1 output units `10` |
| `activation='relu'` | `snl::activator::Relu<>` |
| `activation='softmax'` | `snl::activator::Softmax<>` |
| input shape `(28,28,1)` | `snl::Stream<float, snl::Shape<28,28,1>>` |

> **Note:** `using Type = float` is correct for simulation.
> For a resource-optimised FPGA build replace `float` with `ap_fixed<W,I>`.

---

## Step 3 — Configure the Project File (`project/MLP.py`)

`project/MLP.py` tells the build system which FPGA to target, where the data
files are, how many simulation tests to run, and what to name the IP.

The key section in `get_products()`:
```python
csim_argv = snl.argv(input=input, constants=constants, golden=golden, ntests=5)
fpgas     = [ Product.Fpga('xcku115-flvb2104-2-i', '5', None, 'f0') ]
#                           part number              clock(ns)   id
```

Adjust `ntests` (how many samples to run through csim), the FPGA part, and the
clock period (ns) for your target board.

---

## Step 4 — Build the SNL Acquirers  *(one-time per SNL checkout)*

The acquirers are standalone x86 executables that load Keras/Npy files at
runtime and stream them to the HLS testbench. They only need to be built once
per `snl` submodule checkout — not per network.

```bash
SnlBuildAcquirerAll
```

Build artifacts land in:
```
firmware/submodules/snl/acquirer/.../build/x86_64-linux/Release/
```

> **Important:** `bld_sub.sh` always exits 0 even when `make` fails.
> Scroll the output and look for the word `Error` or `fatal` to verify success.

---

## Step 5 — Build the SNL Adapter  *(once per network architecture)*

The adapter bridges the HLS testbench to the acquirers. It reads your
`Network.hh` to generate the correct types, so it must be rebuilt whenever
you change layers, types, or stream shapes.

```bash
SnlBuildAdapter firmware/ex5/include/Network.hh
```

Build artifacts land next to `Network.hh`:
```
firmware/ex5/include/build/x86_64-linux/Release/
  libSnlAdapter.so          ← loaded at csim/cosim runtime
  SnlAdapterReader-Data
  SnlAdapterReader-Constants
  SnlAdapterReader-Golden
```

> **Troubleshooting:** if you see
> `fatal error: snl/support/SetSnlNetwork.hh: No such file or directory`
> that file is missing from the snl submodule checkout.
> Copy it from the reference repo at
> `Abby_Latest_upgrade_V0/firmware/submodules/snl/include/snl/support/SetSnlNetwork.hh`.

---

## Step 6 — Create the HLS Workspace

```bash
hlsWs --create
```

Creates:
```
firmware/ex5/products/ws/2025.1/
```

---

## Step 7 — Generate the HLS Configuration

```bash
hlsCfg --create project/MLP.py
```

Reads `MLP.py` and writes:
```
firmware/ex5/products/cfg/2025.1/Network-f0.cfg
```

This `.cfg` file tells Vitis HLS the top function, testbench files, synthesis
source, include paths, defines, and simulation arguments.

---

## Step 8 — C-Simulation (csim)

```bash
hlsRun --csim=m,r
```

Runs the C testbench on your CPU. The SNL testbench:
1. Loads `mnist_test.npy` (test inputs) via the data acquirer.
2. Executes the HLS C++ `processNetwork` function on each input.
3. Compares results against `mnist_golden.npy` using the golden acquirer.

**What to look for:**
```
-- Final Results Check --
  NErrors/NRead = 0/10    <-- this is the pass/fail score; 0 errors = PASS
```

> The per-row "Error" lines in the Layer1 checker table are floating-point
> rounding differences between HLS and Keras — they are expected and do NOT
> mean the simulation failed.  Only the "Final Results Check" line matters.

---

## Step 9 — HLS Synthesis

```bash
hlsRun --synthesis
```

Vitis HLS compiles the C++ to RTL (VHDL/Verilog).
Expected warnings with `float` / `datatype::Auto`:

| Warning | Meaning | Action needed |
|---------|---------|---------------|
| `II Violation … softmax_flush_norm_sum_loop` | Softmax normalization loop has a read-after-write dependency; HLS increases II | None for correctness; reduce with `ap_fixed` if throughput matters |
| `internal stream 'l0_l1' … default size can result in deadlock` | Inter-layer FIFO depth warning | Informational only |

No errors = synthesis succeeded.

---

## Step 10 — Package the IP

```bash
hlsRun --package
```

Packages the RTL into a Vivado IP core structure.

---

## Step 11 — Generate the IP Zip

```bash
hlsRun --ip
```

Produces the deliverable:
```
firmware/ex5/products/ip/2025.1/Network-f0.zip    (≈1.6 MB)
```

This `.zip` is a Vivado IP catalog archive.  Add it to any Vivado project via
**IP Catalog → Add Repository**, then instantiate `processNetwork` as an IP.

---

## Adapting for Your Own Model

To build IP for a different network, change three things and rerun from Step 4:

### 1. `train_mlp.py` — change the architecture
```python
HIDDEN_UNITS = 128   # example: bigger hidden layer
NUM_CLASSES  = 5     # example: 5-class problem instead of 10
```

### 2. `include/Network.hh` — mirror the Python change
```cpp
// Layer0: Dense(784→128, ReLU)
using Layer0 = snl::parameters::Dense
        <snl::LayerPosition::First,
         SrcStream,
         true,
         128,                        // <-- match HIDDEN_UNITS
         ...
         >;

// Layer1: Dense(128→5, Softmax)
using Layer1 = snl::parameters::Dense
        <snl::LayerPosition::Last,
         snl::SrcStream<Layer0>,
         true,
         5,                          // <-- match NUM_CLASSES
         ...
         >;
```

### 3. `project/MLP.py` — update `ntests` / FPGA / IP name if needed
```python
csim_argv = snl.argv(..., ntests=10)           # more tests
fpgas     = [ Product.Fpga('xc7z020clg400-1', '10', None, 'f0') ]  # different part
```

Then rebuild:
```bash
SnlBuildAdapter firmware/ex5/include/Network.hh   # Step 5 (rebuild adapter)
hlsCfg --create project/MLP.py                    # Step 7 (regenerate cfg)
hlsRun --csim=m,r                                 # Step 8
hlsRun --synthesis                                # Step 9
hlsRun --package                                  # Step 10
hlsRun --ip                                       # Step 11
```

---

## Full Command Sequence (Quick Reference)

```bash
# ── Once per terminal ──────────────────────────────────────────────────────────
version=2025.1 ; hlsLocate
hlsbs-dave
hlsVersion 2025.1
exSelect ex5

# ── Phase 1: Train (CPU, one time per model) ───────────────────────────────────
/sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2/bin/python firmware/ex5/train_mlp.py

# ── Phase 2: HLS build ─────────────────────────────────────────────────────────
SnlBuildAcquirerAll                                  # one-time per snl checkout
SnlBuildAdapter firmware/ex5/include/Network.hh      # per network

hlsWs  --create
hlsCfg --create project/MLP.py

hlsRun --csim=m,r
hlsRun --synthesis
hlsRun --package
hlsRun --ip

# ── Output ─────────────────────────────────────────────────────────────────────
# firmware/ex5/products/ip/2025.1/Network-f0.zip
```
