# ex5 — MNIST MLP: From Training to FPGA IP (Standalone / Off-Site Setup)

This guide covers the same end-to-end pipeline as `README.md` but for a system
that is **not** SLAC's S3DF cluster.  You will install Vitis HLS yourself,
create your own Python environment, and adjust all paths to your local install.

---

## System Requirements

| Requirement | Notes |
|-------------|-------|
| **OS** | Linux x86_64 only. Ubuntu 20.04/22.04 or RHEL 8 recommended. Windows and macOS are **not** supported by the hlsBs/ruckus build system. |
| **RAM** | 16 GB minimum; 32 GB recommended for synthesis |
| **Disk** | ~80 GB free for Vitis HLS install; ~2 GB for project build products |
| **Shell** | bash |
| **git** | 2.13 or newer (needed for `--recurse-submodules`) |
| **cmake** | Must be available at `/usr/bin/cmake`. Install via your package manager (see below). |
| **gcc/g++** | 7.0 or newer (for csim fast path) |

Install system dependencies on Ubuntu/Debian:
```bash
sudo apt update
sudo apt install -y cmake gcc g++ make git python3-pip
```

On RHEL/CentOS:
```bash
sudo yum install -y cmake gcc gcc-c++ make git python3-pip
```

> **Why `/usr/bin/cmake`?**  The SNL adapter build scripts call `/usr/bin/cmake`
> explicitly to avoid picking up Vitis's bundled cmake.  A cmake installed via
> `apt`/`yum` lands at `/usr/bin/cmake`.  If your cmake is elsewhere, symlink
> it: `sudo ln -s $(which cmake) /usr/bin/cmake`

---

## Step 0 — Install Vitis HLS

Vitis HLS is AMD/Xilinx's high-level synthesis tool.  It is free to download
but requires a (free) AMD account and an appropriate license for synthesis.

### Download

1. Go to: https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vitis.html
2. Click **Download** and log in (create a free AMD account if needed).
3. Choose **Vitis HLS** (standalone) **or** the full **Vitis** unified installer.
   - The standalone HLS installer is smaller (~25 GB installed).
   - Version **2023.2 or newer is required**; this guide uses **2025.1**.
4. Download the Linux Self-Extracting Web Installer (`.bin` file).

### Install

```bash
chmod +x Xilinx_Unified_2025.1_*.bin
./Xilinx_Unified_2025.1_*.bin
```

Follow the GUI installer.  Select at minimum:
- **Vitis HLS** (required)
- **Vivado** (required for the `--package` and `--ip` stages)

Choose an install directory, e.g. `/opt/xilinx/2025.1`.

> **Disk space:** a Vitis HLS + Vivado install is approximately 75–90 GB.
> If disk is tight, install Vitis HLS only and skip the `--package`/`--ip` steps.

### Licensing

- **C simulation (`--csim`)**: no license required when using the fast path
  (direct g++ compile).
- **Synthesis, package, IP**: requires a license.
  - **Free WebPACK license** covers common parts: Artix-7, Kintex-7, Zynq-7000,
    some Kintex/Zynq UltraScale+.
  - The part used in `MLP.py` (`xcku115-flvb2104-2-i`, Kintex UltraScale+)
    **requires a full license**.  For learning purposes, substitute a
    WebPACK-supported part such as `xc7z020clg400-1` (Zynq-7020).
  - Obtain/activate a WebPACK license at: https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado/vivado-webpack.html

After install, note your installation directory.  The rest of this guide refers
to it as `<XILINX_ROOT>`, e.g. `/opt/xilinx/2025.1`.

---

## Step 0b — Install Python with TensorFlow

You need Python 3.9–3.11 with `tensorflow` (for training) and `numpy`.

### Option A: conda / miniconda (recommended)

```bash
# Install miniconda if not already present
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
source ~/.bashrc

# Create a dedicated env
conda create -n snl_ml python=3.10 -y
conda activate snl_ml
pip install tensorflow numpy
```

### Option B: pip into a virtualenv

```bash
python3 -m venv ~/snl_ml_env
source ~/snl_ml_env/bin/activate
pip install tensorflow numpy
```

Note the path to the Python binary:
```bash
which python   # e.g. /home/yourname/miniconda3/envs/snl_ml/bin/python
```
You will use this path when running `train_mlp.py`.

---

## Step 0c — Clone the Repo

```bash
git clone --recurse-submodules <repo-url> hlsBs-examples-dave
cd hlsBs-examples-dave
```

If you already cloned without submodules:
```bash
git submodule update --init --recursive
```

The two key submodules are:
- `firmware/submodules/ruckus` — the hlsBs build system
- `firmware/submodules/snl`    — the SNL ML template library

---

## One-Time Personal Setup

Create `~/.my_aliases.sh` with the two required aliases.
Replace the paths with **your actual install locations**:

```bash
# ~/.my_aliases.sh

# hlsLocate: sets the Xilinx search path.  Set `version` first, then run hlsLocate.
# Replace /opt/xilinx with wherever you installed Vitis/Vivado.
alias hlsLocate='export HLSBS_XILINX_SETUP=/opt/xilinx/${version}'

# Replace /home/yourname/hlsBs-examples-dave with your clone path.
alias hlsbs-dave="source /home/yourname/hlsBs-examples-dave/firmware/scripts/setup_env.sh"
```

Add to `~/.bashrc`:
```bash
if [ -f ~/.my_aliases.sh ]; then
    . ~/.my_aliases.sh
fi
```

Reload:
```bash
source ~/.bashrc
```

> **Verify the path:**  `ls /opt/xilinx/2025.1` (or your version) should show
> a `Vitis` directory and a `Vivado` directory.

---

## Per-Terminal Setup (run every new shell)

```bash
version=2025.1 ; hlsLocate    # (1) point to your Xilinx install
hlsbs-dave                    # (2) source the project env
hlsVersion 2025.1             # (3) activate the Vitis toolchain
exSelect ex5                  # (4) select the ex5 project
```

> If `hlsVersion` reports `HLSBS_XILINX_SETUP is not set`, you forgot step (1).
> Run `version=2025.1 ; hlsLocate` first.

---

## Step 1 — Train the Model

```bash
# From inside the repo root:
/home/yourname/miniconda3/envs/snl_ml/bin/python firmware/ex5/train_mlp.py
```

This trains on MNIST (~10 epochs, CPU, ~1–2 minutes) and writes three files to
`firmware/ex5/data/`:

| File | Shape | Used by |
|------|-------|---------|
| `mnist_mlp.keras` | — | SNL constants acquirer (weights at csim/cosim) |
| `mnist_test.npy` | (100, 28, 28, 1) float32 | SNL data acquirer |
| `mnist_golden.npy` | (100, 10) float32 | csim checker |

> **GPU note:** `train_mlp.py` sets `CUDA_VISIBLE_DEVICES=''` to force CPU,
> avoiding GPU driver compatibility issues on shared or older hardware.
> Training on CPU is fast enough for this small model.

---

## Step 2 — Review `include/Network.hh`

`firmware/ex5/include/Network.hh` describes the same architecture as
`train_mlp.py` in SNL C++ template syntax:

```
Input (28×28×1 float) → Dense(784→64, ReLU) → Dense(64→10, Softmax)
```

The numbers `64` (hidden units) and `10` (output classes) **must match**
`HIDDEN_UNITS` and `NUM_CLASSES` in `train_mlp.py`.

No changes are needed for the default ex5 run.

---

## Step 3 — Review `project/MLP.py`

`firmware/ex5/project/MLP.py` is the build-system config.  For a first run,
only one line may need changing — the FPGA part — if you are using a
WebPACK license:

```python
# Default (requires full license):
fpgas = [ Product.Fpga('xcku115-flvb2104-2-i', '5', None, 'f0') ]

# WebPACK alternative (Zynq-7020, free license):
fpgas = [ Product.Fpga('xc7z020clg400-1', '10', None, 'f0') ]
```

For csim only (no synthesis/IP), the FPGA part does not matter — leave it as-is.

---

## Step 4 — Build the SNL Acquirers *(one-time per SNL checkout)*

The acquirers are standalone x86 executables that load Keras/Npy files at
runtime and feed them to the HLS testbench.  Build them once per checkout:

```bash
SnlBuildAcquirerAll
```

Build artifacts land in:
```
firmware/submodules/snl/acquirer/.../build/x86_64-linux/Release/
```

> **Important:** the `bld_sub.sh` script always exits 0 even when `make`
> fails.  Scroll the output and look for the word `Error` or `fatal error` to
> verify success.  You should see all four targets built:
> `libSnlAcquirer.so`, `SnlAcquirerReader-Data`,
> `SnlAcquirerReader-Constants`, `SnlAcquirerReader-Golden`.

### If you see `fatal error: snl/support/SetSnlNetwork.hh: No such file or directory`

This file may be missing from the snl submodule checkout.
Check:
```bash
ls firmware/submodules/snl/include/snl/support/SetSnlNetwork.hh
```

If it is missing, the file needs to be restored to the submodule.  Contact the
repository maintainer or copy it from a complete reference checkout.

---

## Step 5 — Build the SNL Adapter *(once per network architecture)*

The adapter connects the testbench to the acquirers.  It reads `Network.hh` to
generate correctly-typed glue code, so rebuild it whenever the network
architecture changes.

```bash
SnlBuildAdapter firmware/ex5/include/Network.hh
```

Expected output in `firmware/ex5/include/build/x86_64-linux/Release/`:
```
libSnlAdapter.so
SnlAdapterReader-Data
SnlAdapterReader-Constants
SnlAdapterReader-Golden
```

> Same caveat as Step 4: `bld_sub.sh` exits 0 even on failure.
> Grep for `Error`/`fatal` in the output to confirm success.

---

## Step 6 — Create the HLS Workspace

```bash
hlsWs --create
```

Creates: `firmware/ex5/products/ws/2025.1/`

---

## Step 7 — Generate the HLS Configuration

```bash
hlsCfg --create project/MLP.py
```

Reads `MLP.py` and writes:
```
firmware/ex5/products/cfg/2025.1/Network-f0.cfg
```

Verify the cfg looks complete (it should contain `tb.file`, `syn.file`,
`csim.argv` lines):
```bash
cat firmware/ex5/products/cfg/2025.1/Network-f0.cfg
```

---

## Step 8 — C-Simulation

```bash
hlsRun --csim=m,r
```

Runs the HLS C++ testbench on your CPU using the trained weights and test images.

**Pass criterion:**
```
-- Final Results Check --
  NErrors/NRead = 0/10    <-- 0 errors = PASS
```

> The per-row "Error" lines in the Layer1 checker table are floating-point
> rounding differences between HLS C++ and Keras — this is expected and
> **does not mean the test failed**.  Only the "Final Results Check" matters.

**If csim fails:**  check that the adapter (Step 5) was built successfully and
that all three `.npy`/`.keras` files exist in `firmware/ex5/data/`.

---

## Step 9 — HLS Synthesis

> Requires a valid Vitis HLS license (WebPACK is sufficient for supported parts).

```bash
hlsRun --synthesis
```

Expected warnings with `float` / `datatype::Auto` — these are normal:

| Warning | Why it appears | Action |
|---------|---------------|--------|
| `II Violation … softmax_flush_norm_sum_loop` | Softmax normalization has a read-after-write dependency; HLS relaxes II | None — correctness unaffected |
| `internal stream 'l0_l1' … default size can result in deadlock` | Inter-layer FIFO depth advisory | Informational only |

No `ERROR:` lines = synthesis succeeded.

Synthesis output lands in:
```
firmware/ex5/products/ws/2025.1/Network-f0/Network-f0/hls/syn/
```

---

## Step 10 — Package the IP

> Requires Vivado (installed as part of Vitis or separately).

```bash
hlsRun --package
```

Packages the RTL into a Vivado IP core structure including sub-core IP blocks.

---

## Step 11 — Generate the IP Zip

```bash
hlsRun --ip
```

Produces:
```
firmware/ex5/products/ip/2025.1/Network-f0.zip   (≈ 1.6 MB)
```

This `.zip` is a Vivado IP catalog archive.  Add it to any Vivado project via
**IP Catalog → Add Repository**, then instantiate `processNetwork` as an IP block.

> **Note on the DCP:** `hlsRun --ip` will also attempt to produce a `.dcp`
> file, but this requires `hlsRun --implementation` (full Vivado
> place-and-route) to have been run first.  The `.zip` alone is sufficient for
> IP catalog integration.

---

## Adapting for Your Own Model

Change these three files; then re-run from Step 4.

### 1. `train_mlp.py` — your architecture
```python
HIDDEN_UNITS = 128   # new hidden layer size
NUM_CLASSES  = 5     # your number of output classes
```

### 2. `include/Network.hh` — mirror the Python change
```cpp
// Layer0: Dense(784→128, ReLU)
using Layer0 = snl::parameters::Dense
    <snl::LayerPosition::First, SrcStream, true,
     128,                    // <-- match HIDDEN_UNITS
     Type, snl::activator::Relu<>, Type, snl::datatype::Auto, PrintMin>;

// Layer1: Dense(128→5, Softmax)
using Layer1 = snl::parameters::Dense
    <snl::LayerPosition::Last, snl::SrcStream<Layer0>, true,
     5,                      // <-- match NUM_CLASSES
     Type, snl::activator::Softmax<>, Type, snl::datatype::Auto,
     snl::printer::Options<PrtLo, PrtLo, PrtHi>>;
```

### 3. `project/MLP.py` — FPGA part and IP name
```python
fpgas = [ Product.Fpga('xc7z020clg400-1', '10', None, 'f0') ]  # your FPGA part
```

### Rebuild
```bash
SnlBuildAdapter firmware/ex5/include/Network.hh
hlsCfg --create project/MLP.py        # or --replace if cfg already exists
hlsRun --csim=m,r
hlsRun --synthesis
hlsRun --package
hlsRun --ip
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `hlsVersion: HLSBS_XILINX_SETUP is not set` | Ran `hlsVersion` before `hlsLocate` | Run `version=2025.1 ; hlsLocate` first |
| `hlsVersion: Vitis version 2025.1 not found` | Wrong `HLSBS_XILINX_SETUP` path or version not installed | Verify `ls $HLSBS_XILINX_SETUP` exists |
| `cmake: command not found` during adapter build | cmake not installed or not at `/usr/bin/cmake` | `sudo apt install cmake` then verify `/usr/bin/cmake --version` |
| `fatal error: snl/support/SetSnlNetwork.hh` | File missing from snl submodule | Restore from reference checkout (see Step 4 note) |
| csim: `Cannot find C test bench` | `Network-f0.cfg` is missing `tb.file` lines | Re-run `hlsCfg --replace project/MLP.py` |
| csim: `libSnlAdapter.so: cannot open` | Adapter not built | Re-run Step 5 and check for errors |
| `mnist_mlp.keras` not found | Training not run yet | Run `train_mlp.py` (Step 1) |
| Synthesis: `ERROR: [Common 17-69] Command failed: licenseCheck` | License missing for selected FPGA part | Switch to a WebPACK part (e.g. `xc7z020clg400-1`) or obtain a license |

---

## Full Command Sequence (Quick Reference)

```bash
# ── Once per terminal ──────────────────────────────────────────────────────────
version=2025.1 ; hlsLocate     # points to /opt/xilinx/2025.1 (adjust to your install)
hlsbs-dave                     # sources the project env
hlsVersion 2025.1
exSelect ex5

# ── Phase 1: Train (CPU, once per model) ──────────────────────────────────────
/home/yourname/miniconda3/envs/snl_ml/bin/python firmware/ex5/train_mlp.py

# ── Phase 2: HLS build ─────────────────────────────────────────────────────────
SnlBuildAcquirerAll                                  # one-time per snl checkout
SnlBuildAdapter firmware/ex5/include/Network.hh      # once per network

hlsWs  --create
hlsCfg --create project/MLP.py

hlsRun --csim=m,r                                    # C-simulation (no license needed)
hlsRun --synthesis                                   # needs license
hlsRun --package                                     # needs Vivado
hlsRun --ip                                          # produces Network-f0.zip

# ── Output ─────────────────────────────────────────────────────────────────────
# firmware/ex5/products/ip/2025.1/Network-f0.zip
```
