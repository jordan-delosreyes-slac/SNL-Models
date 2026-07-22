#!/usr/bin/env python3
"""
snl-model-builder-agent — drives the SNL/hlsBs build system using Claude claude-opus-4-7.

The agent can train ML models, run C-simulation, synthesize RTL, and generate
Vivado IP archives.  It handles all the environment-sourcing quirks of the
hlsBs build system automatically.

Usage:
    python agent.py
    python agent.py "Run csim for ex5 and report pass/fail"
    python agent.py --verbose "Full pipeline: train, csim, synthesis, IP"
    python agent.py --example ex5 "Check synthesis warnings"
"""

AGENT_NAME = 'snl-model-builder-agent'

import sys
import os
import subprocess
import json
import argparse
import anthropic

# Flush stdout immediately so output appears in real time when piped.
sys.stdout.reconfigure(line_buffering=True)

# ── Paths ──────────────────────────────────────────────────────────────────────

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SETUP_ENV  = os.path.join(REPO_ROOT, 'firmware', 'scripts', 'setup_env.sh')
PYTHON_BIN = '/sdf/group/faders/users/adave/miniforge3/envs/rogue_v6.6.2/bin/python'
XILINX_VER = '2025.1'

# Shell preamble injected before every command so hlsBs bash functions are in scope.
# exSelect <example> is appended at call time.
_SETUP_BASE = f"""\
set -e
export version={XILINX_VER}
export HLSBS_XILINX_SETUP=/sdf/group/faders/tools/xilinx/${{version}}
source {SETUP_ENV}
hlsVersion {XILINX_VER} >/dev/null 2>&1
"""

# ── Tool implementations ───────────────────────────────────────────────────────

def bash_exec(command: str, example: str = 'ex5', project_config: str = None) -> dict:
    """Run a shell command with the HLS environment pre-sourced.

    For registered examples (ex0-ex5) pass example='exN'.
    For new project directories pass project_config='/abs/path/to/project/Config.py'
    — this sets HLSBS_PROJECT directly, bypassing exSelect.
    """
    if project_config:
        # New/custom project: set HLSBS_PROJECT directly (no need to edit setup_env.sh).
        project_setup = f'export HLSBS_PROJECT={project_config}\n'
    else:
        project_setup = f'exSelect {example}\n'
    full_cmd = _SETUP_BASE + project_setup + command
    proc = subprocess.run(
        ['bash', '-c', full_cmd],
        capture_output=True, text=True,
        cwd=REPO_ROOT,
    )
    output = proc.stdout + proc.stderr

    # bld_sub.sh always exits 0 even on failure — scan for error keywords too.
    error_keywords = ('fatal error:', 'make: ***', ': error:', 'Error: ')
    keyword_hit = any(kw in output for kw in error_keywords)
    success = (proc.returncode == 0) and not keyword_hit

    # Trim very long output: keep first 4 000 and last 6 000 chars.
    max_len = 10_000
    if len(output) > max_len:
        keep = max_len // 2
        output = (
            output[:keep]
            + f'\n\n... [{len(output) - max_len} chars trimmed] ...\n\n'
            + output[-keep:]
        )

    return {
        'exit_code': proc.returncode,
        'output':    output,
        'success':   success,
    }


def read_file(path: str) -> dict:
    """Read a file; relative paths are resolved from the repo root."""
    if not os.path.isabs(path):
        path = os.path.join(REPO_ROOT, path)
    if not os.path.exists(path):
        return {'error': f'File not found: {path}'}
    try:
        with open(path) as fh:
            return {'path': path, 'content': fh.read()}
    except Exception as exc:
        return {'error': str(exc)}


def write_file(path: str, content: str) -> dict:
    """Write content to a file; relative paths resolve from the repo root.

    Only paths inside the repo root are allowed.
    """
    if not os.path.isabs(path):
        path = os.path.join(REPO_ROOT, path)
    # Safety: stay inside the repo.
    if not path.startswith(REPO_ROOT):
        return {'error': f'Refusing to write outside repo root: {path}'}
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as fh:
            fh.write(content)
        return {'path': path, 'bytes_written': len(content), 'success': True}
    except Exception as exc:
        return {'error': str(exc)}


_TOOL_HANDLERS = {
    'bash_exec':  bash_exec,
    'read_file':  read_file,
    'write_file': write_file,
}

# ── Tool schemas ───────────────────────────────────────────────────────────────

_TOOLS = [
    {
        'name': 'bash_exec',
        'description': (
            'Run a shell command with Vitis HLS 2025.1, hlsBs, and SNL already sourced. '
            'Use for: SnlBuildAcquirerAll, SnlBuildAdapter, hlsWs, hlsCfg, hlsRun, '
            'and the Python training script. '
            'exSelect is called automatically for the given example. '
            'IMPORTANT: bld_sub.sh always exits 0 even on failure. '
            'Always check the "success" field and scan "output" for errors.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'command': {
                    'type': 'string',
                    'description': 'Shell command to run. The HLS environment is pre-sourced.',
                },
                'example': {
                    'type': 'string',
                    'description': 'Registered example name to select via exSelect (ex0-ex5). Use this OR project_config, not both.',
                },
                'project_config': {
                    'type': 'string',
                    'description': 'Absolute path to the project config .py file for a NEW project directory not registered in setup_env.sh. Sets HLSBS_PROJECT directly. Example: /repo/firmware/agent/agent_ml_training0/project/CNN.py',
                },
            },
            'required': ['command'],
        },
    },
    {
        'name': 'read_file',
        'description': (
            'Read a file. Paths may be absolute or relative to the repo root. '
            'Use to inspect: Network.hh, project/MLP.py, '
            'products/cfg/2025.1/Network-f0.cfg, and workspace logs.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Absolute or repo-root-relative file path.',
                },
            },
            'required': ['path'],
        },
    },
    {
        'name': 'write_file',
        'description': (
            'Write content to a file (must be inside the repo). '
            'Use to update Network.hh when changing layer sizes or activations, '
            'project/MLP.py when changing FPGA part/clock/ntests, or the .cfg '
            'file when manual entries are missing.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'path': {
                    'type': 'string',
                    'description': 'Absolute or repo-root-relative file path to write.',
                },
                'content': {
                    'type': 'string',
                    'description': 'Full file content to write.',
                },
            },
            'required': ['path', 'content'],
        },
    },
]

# ── System prompt ──────────────────────────────────────────────────────────────

_SYSTEM = f"""\
You are an expert HLS pipeline agent for the SLAC S3DF cluster.  You drive the
SNL/hlsBs build system end-to-end: create new project directories, write
Network.hh and project config files from scratch, train Keras models, run
C-simulation, RTL synthesis, and Vivado IP packaging.

## Repository layout
Repo root : {REPO_ROOT}
Firmware  : {REPO_ROOT}/firmware/
SNL lib   : {REPO_ROOT}/firmware/submodules/snl/
Reference : {REPO_ROOT}/firmware/ex5/   (working MNIST MLP example)
Python    : {PYTHON_BIN}

---
## Pipeline stages (generic — adapt paths for each new project)

Phase 1 — Python training  (run from repo root)
  {PYTHON_BIN} firmware/<project>/train_<name>.py
  Must write to firmware/<project>/data/:
    <model>.keras        weights for SNL constants acquirer
    <name>_test.npy      test inputs,   shape (N, H, W, C)  float32
    <name>_golden.npy    expected preds, shape (N, classes)  float32

Phase 2 — HLS build  (bash_exec handles env sourcing)
  1. SnlBuildAcquirerAll                                      (once per snl checkout)
  2. SnlBuildAdapter firmware/<project>/include/Network.hh    (once per network)
  3. hlsWs  --create
  4. hlsCfg --create project/<Config>.py
  5. hlsRun --csim=m,r
  6. hlsRun --synthesis
  7. hlsRun --package
  8. hlsRun --ip   →   firmware/<project>/products/ip/2025.1/Network-f0.zip

---
## Supported SNL layer types

Only these three layer types (+ activations) are supported by the SNL library.

### Conv2D
```cpp
#include "snl/parameters/Conv2D-Parameters.hh"
#include "snl/activator/Relu.hh"

using Layer0 = snl::parameters::Conv2D
    <snl::LayerPosition::First,      // First / Middle / Last
     SrcStream,                      // input stream type
     NFILTERS, NROWS, NCOLS, Type,   // kernel:  filters, kernel_h, kernel_w, weight dtype
     STRIDE_R, STRIDE_C,             // stride:  rows, cols
     snl::Padding::Valid,            // Valid (no padding) or Same
     1, 1,                           // dilation: rows, cols  (usually 1,1)
     1,                              // groups  (usually 1)
     snl::activator::Relu<>,         // activator
     Type,                           // bias dtype
     snl::datatype::Auto,            // dst dtype  (Auto = same as input)
     PrintMin
     >;
```
Keras equivalent: `Conv2D(filters=NFILTERS, kernel_size=(NROWS,NCOLS), strides=(STRIDE_R,STRIDE_C), padding='valid', activation='relu')`

### MaxPooling2D
```cpp
#include "snl/parameters/MaxPooling2D-Parameters.hh"

using Layer1 = snl::parameters::MaxPooling2D
    <snl::LayerPosition::Middle,
     snl::SrcStream<Layer0>,   // previous layer's output stream
     POOL_R, POOL_C,           // pool size: rows, cols
     STRIDE_R, STRIDE_C,       // stride: rows, cols
     snl::Padding::Valid,
     snl::datatype::Auto,
     PrintMin
     >;
```
Keras equivalent: `MaxPooling2D(pool_size=(POOL_R,POOL_C), strides=(STRIDE_R,STRIDE_C), padding='valid')`

### Dense  (use after Flatten or as MLP layers)
```cpp
#include "snl/parameters/Dense2D-Parameters.hh"   // or Dense-Parameters.hh
#include "snl/activator/Relu.hh"
#include "snl/activator/Softmax.hh"

using Layer5 = snl::parameters::Dense
    <snl::LayerPosition::Middle,   // First / Middle / Last
     snl::SrcStream<Layer4>,       // previous layer
     true,                         // flatten input (true after Conv/Pool, false after Dense)
     OUTPUT_UNITS,                 // number of output neurons
     Type,                         // weight dtype
     snl::activator::Relu<>,       // activator  (Relu or Softmax)
     Type,                         // bias dtype
     snl::datatype::Auto,
     PrintMin
     >;
```
Keras equivalent: `Dense(OUTPUT_UNITS, activation='relu')` (set flatten=true after a Conv/Pool layer)
Last layer uses `snl::activator::Softmax<>` and `snl::LayerPosition::Last`.

### Activations available
- `snl::activator::Relu<>`     ↔  activation='relu'
- `snl::activator::Softmax<>`  ↔  activation='softmax'  (last layer only)

---
## How to generate Network.hh for a new project

### Step 1 — inspect the trained Keras model
Run this python snippet via bash_exec to get exact layer info:
```python
import keras, sys
m = keras.models.load_model('firmware/<project>/data/<model>.keras')
m.summary()
for i,l in enumerate(m.layers):
    cfg = l.get_config()
    print(f"Layer{{i}}: {{type(l).__name__}} {{cfg}}")
```

### Step 2 — map Keras layers → SNL types
| Keras layer         | SNL type                        |
|---------------------|---------------------------------|
| Conv2D              | snl::parameters::Conv2D         |
| MaxPooling2D        | snl::parameters::MaxPooling2D   |
| Dense               | snl::parameters::Dense          |
| Flatten             | set flatten=true on next Dense  |
| InputLayer          | defines SrcStream shape         |

### Step 3 — write Network.hh  (complete file template)
```cpp
#ifndef __NETWORK_HH__
#define __NETWORK_HH__

#include "snl/parameters/Conv2D-Parameters.hh"
#include "snl/parameters/MaxPooling2D-Parameters.hh"
#include "snl/parameters/Dense2D-Parameters.hh"
#include "snl/activator/Relu.hh"
#include "snl/activator/Softmax.hh"
#include "snl/support/Standard.hh"

namespace mynet {{

static constexpr auto PrtLo  = snl::printer::Level::Lo;
static constexpr auto PrtMed = snl::printer::Level::Med;
static constexpr auto PrtHi  = snl::printer::Level::Hi;
using PrintMin = snl::printer::Options<PrtLo, PrtLo, PrtMed>;

using Type      = float;
using SrcStream = snl::Stream<Type, snl::Shape<H, W, C>>;  // match input shape

// ... layer definitions ...

constexpr char const *Name() {{ return "MyNet"; }}
constexpr char const *File() {{ return __FILE__; }}
using MyNet = snl::Network<snl::NetworkName<Name, File>,
                            Layer0, Layer1, ..., LayerN>;
}} // namespace mynet

using SnlNetwork = mynet::MyNet;
#endif
```
The final `using SnlNetwork = ...` line is REQUIRED — it is what the SNL build system looks for.

---
## How to generate the project config file  (CNN.py / MLP.py)

Template (save as firmware/<project>/project/<Name>.py):
```python
import os

def get_project_root(project): return None
def get_products_root(project): return None
def get_workspace(project): return None

def get_products(project):
    snl     = project.include('$SNL_ROOT/project/SNL.py').module.Snl(project)
    Product = project.Product

    input     = snl.preserve(os.path.join(project.root, 'data', '<name>_test.npy'))
    constants = snl.preserve(os.path.join(project.root, 'data', '<model>.keras'))
    golden    = snl.preserve(os.path.join(project.root, 'data', '<name>_golden.npy'))

    csim_argv  = snl.argv(input=input, constants=constants, golden=golden, ntests=5)
    cosim_argv = snl.argv(input=input, constants=constants, golden=golden, ntests=5)

    fpgas        = [Product.Fpga('xcku115-flvb2104-2-i', '5', None, 'f0')]
    networks     = os.path.join(project.root, 'include', 'Network.hh')
    cfg_template = os.path.join(project.products_root,
                                'cfg', '{{vitis_version}}', '{{network_name}}-{{fpga_id}}.cfg')

    package_ip     = Product.Package.Ip(name='<project>-{{cfg_name}}', vendor='SLAC',
                                        version='V1.0.0', library='hls')
    package_output = Product.Package.Output(format='ip_catalog', syn='false')
    package        = Product.Package(ip=package_ip, output=package_output)
    vivado         = Product.Vivado(flow='syn', syn_dcp='1')

    return snl.create_product(networks=networks, fpgas=fpgas,
                              cfg_template=cfg_template, cmp_template='{{cfg_name}}',
                              csim_argv=csim_argv, cosim_argv=cosim_argv,
                              package=package, vivado=vivado)

def get_ip(project): return project.Ip()
```

---
## cfg file path formula  (if hlsCfg generates a broken cfg)

The cfg is at: firmware/<project>/products/cfg/2025.1/Network-f0.cfg
Count the directory depth from firmware/ to the cfg file.
  ex5    depth = 4  (ex5/products/cfg/2025.1/)  → use  ../../../../submodules/snl/...
  depth 5 project   → use  ../../../../../submodules/snl/...

For -DSNL_NETWORK always use the ABSOLUTE path to Network.hh to avoid ambiguity:
  -DSNL_NETWORK={REPO_ROOT}/firmware/<project>/include/Network.hh

Working cfg template (ex5 = depth 4; adjust ../ count for other depths):
```
part=xcku115-flvb2104-2-i

[hls]
clock=5
flow_target=vivado
package.ip.name=<project>-Network-f0
package.ip.vendor=SLAC
package.ip.library=hls
package.ip.version=V1.0.0
package.output.format=ip_catalog
package.output.syn=false
vivado.flow=syn
vivado.syn_dcp=1
syn.top=processNetwork
tb.file=<DEPTH>submodules/snl/src/snl/SnlTest.cc
tb.file=<DEPTH>submodules/snl/src/snl/adapter/common/Client-Adapter.cc
tb.file_cflags=<DEPTH>submodules/snl/src/snl/SnlTest.cc, -I <DEPTH>submodules/snl/include -DSNL_NETWORK=<ABS_PATH>/include/Network.hh
tb.file_cflags=<DEPTH>submodules/snl/src/snl/adapter/common/Client-Adapter.cc, -I <DEPTH>submodules/snl/include
syn.file=<DEPTH>submodules/snl/src/snl/SnlNetwork.cc
syn.file_cflags=<DEPTH>submodules/snl/src/snl/SnlNetwork.cc, -I <DEPTH>submodules/snl/include -DSNL_NETWORK=<ABS_PATH>/include/Network.hh
csim.ldflags=-Wl,-rpath=/usr/lib/x86_64-linux-gnu
csim.argv=--dfile=<ABS_DATA>/test.npy --cfile=<ABS_DATA>/<model>.keras --gfile=<ABS_DATA>/golden.npy --ntests=5
cosim.argv=--dfile=<ABS_DATA>/test.npy --cfile=<ABS_DATA>/<model>.keras --gfile=<ABS_DATA>/golden.npy --ntests=5
clock_uncertainty=0.2
```

---
## Known gotchas

### 1  bld_sub.sh always exits 0
SnlBuildAcquirerAll and SnlBuildAdapter exit 0 even on failure.
Always check the "success" field AND scan output for "fatal error:" / "make: ***".

### 2  csim pass criterion
  "  NErrors/NRead = 0/N"   (0 = PASS)
Per-row "Error" lines in layer tables are expected FP rounding — NOT failures.

### 3  Expected synthesis warnings (not errors)
  "II Violation … softmax_flush_norm_sum_loop" — normal for float Softmax
  "internal stream … default size can result in deadlock" — informational

### 4  New project directories — use project_config not example
setup_env.sh only registers ex0-ex5 for exSelect. For any new project directory
pass project_config to bash_exec with the absolute path to the project config .py file.
Example:
  bash_exec(command='hlsWs --create',
            project_config='{REPO_ROOT}/firmware/agent/agent_ml_training0/project/CNN.py')
This sets HLSBS_PROJECT directly, no changes to setup_env.sh needed.

### 5  SnlBuildAdapter must be re-run after any Network.hh change
Layer types, sizes, or activations changed → re-run SnlBuildAdapter.

### 6  SetSnlNetwork.hh missing
If SnlBuildAdapter fails with "fatal error: snl/support/SetSnlNetwork.hh":
  bash_exec: cp {REPO_ROOT}/../Abby_Latest_upgrade_V0/firmware/submodules/snl/include/snl/support/SetSnlNetwork.hh \\
                {REPO_ROOT}/firmware/submodules/snl/include/snl/support/

### 7  hlsBs commands are bash functions
hlsWs, hlsCfg, hlsRun, exSelect, SnlBuildAcquirerAll, SnlBuildAdapter are sourced
bash functions — not standalone executables. bash_exec sources the env for every call.

---
## Working style
1. Announce the stage you are about to run.
2. Run it with bash_exec.
3. Check success + scan output for errors using the gotchas above.
4. If a stage fails, read the relevant cfg or log with read_file, diagnose, fix with write_file.
5. After synthesis: report resource utilization (LUTs, FFs, DSPs, BRAMs) and timing (clock period met / worst negative slack).
6. Report each stage: name, PASS or FAIL, key output lines.
"""

# ── Agentic loop ───────────────────────────────────────────────────────────────

def run_agent(task: str, verbose: bool = False) -> None:
    client   = anthropic.Anthropic()
    messages = [{'role': 'user', 'content': task}]

    print(f"\n{'='*64}")
    print(f"[{AGENT_NAME}] Task: {task}")
    print(f"{'='*64}\n")

    for turn in range(1, 50):   # safety cap
        if verbose:
            print(f'[turn {turn}] → Claude claude-opus-4-7')

        response = client.messages.create(
            model      = 'us.anthropic.claude-opus-4-7',
            max_tokens = 16_384,
            thinking   = {'type': 'adaptive'},
            system     = [
                {
                    'type':          'text',
                    'text':          _SYSTEM,
                    'cache_control': {'type': 'ephemeral'},
                }
            ],
            tools    = _TOOLS,
            messages = messages,
        )

        # Append model response to history before any processing.
        messages.append({'role': 'assistant', 'content': response.content})

        # Print text blocks.
        for block in response.content:
            if block.type == 'text':
                print(block.text)

        if response.stop_reason == 'end_turn':
            print(f"\n{'='*64}")
            print('Agent finished.')
            return

        if response.stop_reason != 'tool_use':
            print(f'\n[warning] stop_reason={response.stop_reason!r}')
            return

        # Execute tool calls and collect results.
        tool_results = []
        for block in response.content:
            if block.type != 'tool_use':
                continue

            name   = block.name
            inputs = block.input
            print(f'\n[tool] {name}  args={json.dumps(inputs)[:200]}')

            handler = _TOOL_HANDLERS.get(name)
            if handler is None:
                result = {'error': f'Unknown tool: {name}'}
            else:
                try:
                    result = handler(**inputs)
                except Exception as exc:
                    result = {'error': str(exc)}

            # Console summary.
            if 'output' in result:
                lines   = result['output'].splitlines()
                preview = '\n'.join(lines[:25])
                if len(lines) > 25:
                    preview += f'\n... ({len(lines)-25} more lines)'
                print(f'[result] exit_code={result.get("exit_code")}  '
                      f'success={result.get("success")}\n{preview}')
            elif 'content' in result:
                print(f'[result] read {len(result["content"])} bytes from {result["path"]}')
            elif 'bytes_written' in result:
                print(f'[result] wrote {result["bytes_written"]} bytes to {result["path"]}')
            elif 'error' in result:
                print(f'[error] {result["error"]}')

            tool_results.append({
                'type':        'tool_result',
                'tool_use_id': block.id,
                'content':     json.dumps(result),
            })

        messages.append({'role': 'user', 'content': tool_results})

    print('[warning] Reached turn limit — stopping.')


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f'{AGENT_NAME} — drive SNL/hlsBs with Claude us.anthropic.claude-opus-4-7',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        'task', nargs='?',
        default=(
            'Run the ex5 pipeline: csim, synthesis, package, and IP generation. '
            'Report PASS or FAIL for each stage.'
        ),
        help='Task for the agent (default: full ex5 pipeline)',
    )
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print turn numbers and tool call details')
    args = parser.parse_args()

    if 'ANTHROPIC_API_KEY' not in os.environ:
        sys.exit(
            'Error: ANTHROPIC_API_KEY is not set.\n'
            'Export it before running:\n'
            '  export ANTHROPIC_API_KEY=sk-ant-...'
        )

    run_agent(args.task, verbose=args.verbose)


if __name__ == '__main__':
    main()
