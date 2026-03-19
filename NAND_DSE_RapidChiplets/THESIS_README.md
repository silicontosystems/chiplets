# Master Thesis: Architecture and Rapid Design Space Exploration of Chiplet-Based NAND Storage Subsystems

## Author

**Antony Amburose** (2024OVL1077)  
M.Tech (Executive), Continuing Education Program  
Indian Institute of Technology Jammu  
Supervisor: **Dr. Kankat Ghosh**, Assistant Professor, Dept. of Electrical Engineering  
February 2026

---

## Abstract

The increasing demand for high-performance and scalable storage in modern computing systems has motivated the exploration of chiplet-based architectures beyond traditional compute and memory subsystems. While chipletization has been widely adopted in processors and high-bandwidth memory systems, its application to NAND-based storage architectures remains relatively unexplored.

This thesis investigates the architectural implications of chiplet-based partitioning in UFS/NVMe storage subsystems — where the controller and NAND arrays are implemented as separate dies interconnected through a high-speed die-to-die interface (UCIe). Inspired by the RapidChiplet analytical modeling methodology, the work develops a **scalable modeling framework** that represents the controller and NAND chiplets as nodes in a parameterized interconnect graph $G = (V, E)$.

The framework provides:

- **Analytical latency proxy models** capturing serialization delay, arbitration effects, and link saturation behavior — without cycle-accurate simulation
- **Throughput bottleneck analysis** identifying the limiting resource (controller, link, or NAND) at each operating point
- **M/M/1 queueing model** with tail latency (P99, P99.9) estimation
- **Scalability efficiency metric** $\eta = T_{measured} / (N \cdot B_{NAND})$ to quantify diminishing returns
- **Three topology variants**: Star, Multi-Port Controller, and Hierarchical
- **Automated Design Space Exploration (DSE)** across chiplet count, link bandwidth, request size, and load factor — producing 12 publication-quality analysis plots

### RapidChiplet Reproduction

This work also reproduces and validates the results from the foundational RapidChiplet paper (Hofmeier et al., 2024):

- **Evaluation** of proxy model accuracy across 4 topologies × 9 network scales × 4 traffic patterns (576 experiments)
- **Case study** exploring 65,536 Sparse Hamming Graph (SHG) parametrizations on a 10×10 chiplet grid
- **Key result**: ~2.4% latency error at ~954× speedup over BookSim2 cycle-level simulation

---

## Table of Contents

1. [Background](#background)
2. [NAND Storage Chiplet Framework](#nand-storage-chiplet-framework)
3. [Mathematical Models](#mathematical-models)
4. [Topology Variants](#topology-variants)
5. [Design Space Exploration](#design-space-exploration)
6. [Key Results](#key-results)
7. [RapidChiplet Reproduction](#rapidchiplet-reproduction)
8. [Repository Structure](#repository-structure)
9. [Environment Setup](#environment-setup)
10. [Running the NAND Chiplet DSE](#running-the-nand-chiplet-dse)
11. [Running the RapidChiplet Reproduction](#running-the-rapidchiplet-reproduction)
12. [Challenges and Fixes](#challenges-and-fixes)
13. [References](#references)

---

## Background

### The Chiplet Paradigm

Modern high-performance processors face fundamental limits in monolithic die scaling — increasing defect rates, rising fabrication costs, and reticle size constraints. **Chiplet-based architectures** decompose a large SoC into smaller, independently manufactured dies (chiplets) that are assembled on a shared package substrate using advanced packaging technologies (2.5D interposers, silicon bridges, UCIe die-to-die interfaces).

Key advantages include:
- **Improved yield**: Smaller dies have exponentially higher manufacturing yield
- **Heterogeneous integration**: Mixing chiplets fabricated on different technology nodes
- **Design reuse**: Standardized chiplet IPs can be composed into different products
- **Scalable architecture**: Through modular replication

While chipletization has been widely adopted in processors (AMD EPYC, Intel Ponte Vecchio) and HBM systems, **NAND-based storage subsystems remain largely monolithic** — integrating controller and NAND arrays in tightly coupled single-die designs.

### The Storage Chiplet Opportunity

Conventional UFS/NVMe storage subsystems integrate the Flash Translation Layer (FTL) controller, channel controllers, and NAND interfaces within a single die. Transitioning to chiplet-based storage — where the controller and NAND arrays are separate chiplets connected via UCIe — introduces new architectural trade-offs:

- **Serialization delay** across die-to-die links
- **Arbitration contention** under high parallelism
- **Link bandwidth saturation** limiting scalability
- **Tail latency degradation** near saturation
- **Scalability efficiency** that departs from linear

There is currently no generalized analytical framework for modeling these effects. This thesis fills that gap.

---

## NAND Storage Chiplet Framework

### Architectural Abstraction (Chapter 3)

The chiplet-based storage system is modeled as a graph:

$$G = (V, E)$$

where:
- $V = \{C, N_1, N_2, \ldots, N_k\}$ — controller chiplet $C$ and $k$ NAND chiplets
- $E$ = set of die-to-die interconnect links, each characterized by bandwidth $B_e$ and propagation latency $L_e$

### Monolithic Baseline (Eq. 3.4)

$$L_{total} = L_{ctrl} + L_{NAND}$$

No die-to-die overhead. This serves as the comparison baseline.

### Chiplet-Based Architecture (Eq. 3.5–3.7)

$$L_{total} = L_{ctrl} + L_{link}^{fwd} + L_{NAND} + L_{link}^{ret}$$

where each link delay includes:

$$L_{link} = L_{serial} + L_{prop} + L_{arb}$$

---

## Mathematical Models

### Link Serialization Delay (Eq. 4.1)

$$L_{serial} = \frac{S}{B_{link}}$$

where $S$ is the request size (bytes) and $B_{link}$ is the link bandwidth (GB/s).

### Arbitration Delay (Eq. 4.2)

$$L_{arb} \approx \frac{(M - 1) \cdot S}{B_{link}}$$

where $M$ is the number of concurrent requests competing for the link.

### Total Latency (Eq. 4.6)

$$L_{total} = L_{ctrl} + 2 \cdot \left(\frac{S}{B_{link}} + L_{prop} + L_{arb}\right) + L_{NAND}$$

The factor of 2 accounts for both forward (command) and return (data) paths.

### Throughput Bottleneck (Eq. 4.7)

$$T = \min(B_{ctrl},\ B_{link},\ N \cdot B_{NAND})$$

### Scalability Efficiency (Eq. 4.8)

$$\eta = \frac{T_{measured}}{N \cdot B_{NAND}}$$

$\eta = 1$ indicates perfect linear scaling; $\eta < 1$ indicates a link-limited or controller-limited regime.

### Saturation Boundary (Eq. 6.2)

$$N^* = \frac{B_{link}}{B_{NAND}}$$

Beyond $N^*$, additional NAND chiplets provide no throughput benefit.

### M/M/1 Queueing Model (Eq. 4.9–4.11)

Queue waiting time: $W_q = \frac{\lambda}{\mu(\mu - \lambda)}$

Total response time: $W_{total} = W_q + \frac{1}{\mu}$

Per-chiplet arrival rate under load splitting: $\lambda_i = \frac{\lambda}{N}$

P99 tail latency: $t_{99} = \frac{-\ln(0.01 / \rho)}{\mu(1 - \rho)}$

---

## Topology Variants

### Star Topology (Section 5.1)

```
Controller ─── NAND_1
    ├─── NAND_2
    ├─── NAND_3
    └─── NAND_N
```

- **Single hop** — lowest latency per request
- All $N$ chiplets share the controller link bandwidth
- $T = \min(B_{ctrl}, B_{link}, N \cdot B_{NAND})$
- **Bottleneck**: Controller becomes limiting as $N$ grows

### Multi-Port Controller (Section 5.2)

- Controller with $P$ independent ports, each serving $N/P$ chiplets
- $T = \min(B_{ctrl}, P \cdot B_{link}, N \cdot B_{NAND})$ — Eq. 5.5
- **Advantage**: Higher aggregate bandwidth, reduced per-port contention
- **Tradeoff**: Increased controller area and PHY overhead

### Hierarchical Topology (Section 5.3)

```
Controller ─── Aggregator_1 ─── NAND_1, ..., NAND_{N/K}
    ├─── Aggregator_2 ─── ...
    └─── Aggregator_K ─── NAND_{N-N/K+1}, ..., NAND_N
```

- **Two hops**: Controller → Aggregator → NAND
- $L_{total} = L_{ctrl} + 2 L_{link1} + L_{agg} + 2 L_{link2} + L_{NAND}$ — Eq. 5.7
- **Advantage**: Improved fan-out scalability for large $N$
- **Tradeoff**: Higher latency due to extra hop and aggregation processing

---

## Design Space Exploration

### Parameters (Chapter 6)

| Parameter | Symbol | Default | Range |
|---|---|---|---|
| NAND chiplet count | $N$ | — | 1–32 |
| Link bandwidth | $B_{link}$ | 32 GB/s | 4–128 GB/s |
| Request size | $S$ | 16 KB | 4–32 KB |
| NAND read latency | $t_R$ | 50 μs | — |
| NAND program latency | $t_{PROG}$ | 500 μs | — |
| Controller latency | $L_{ctrl}$ | 3 μs | — |
| Controller bandwidth | $B_{ctrl}$ | 32 GB/s | — |
| NAND per-chiplet BW | $B_{NAND}$ | 2.4 GB/s | — |
| Link propagation | $L_{prop}$ | 2 ns | — |
| Controller ports | $P$ | 4 | — |
| Aggregators | $K$ | 4 | — |

### Generated Plots (12 total)

| Plot | Thesis Chapter | Description |
|---|---|---|
| `latency_breakdown.pdf` | Ch. 3 | Monolithic vs chiplet latency component breakdown |
| `latency_vs_chiplet_count.pdf` | Ch. 5 | Average latency vs $N$ for all topologies |
| `throughput_vs_chiplet_count.pdf` | Ch. 5 | Throughput vs $N$ with ideal linear reference |
| `scalability_efficiency.pdf` | Ch. 5 | $\eta$ vs $N$ for all topologies |
| `link_utilization.pdf` | Ch. 5 | Link utilization vs $N$ |
| `topology_comparison_panel.pdf` | Ch. 5 | 4-panel comprehensive topology comparison |
| `queueing_response_time.pdf` | Ch. 4 | M/M/1 response time vs load factor |
| `tail_latency_vs_load.pdf` | Ch. 4 | P99 and P99.9 tail latency vs $\rho$ |
| `bandwidth_impact.pdf` | Ch. 6 | Latency/throughput at varying $B_{link}$ |
| `request_size_impact.pdf` | Ch. 6 | Impact of request size $S$ on latency |
| `saturation_boundary.pdf` | Ch. 6 | $N^*$ boundary: NAND-limited vs link-limited |
| `dse_heatmaps.pdf` | Ch. 6 | 2D heatmaps: latency, throughput, efficiency |

---

## Key Results

### NAND Chiplet DSE Findings

The DSE framework completes in **under 1 second**, evaluating hundreds of configurations analytically — compared to hours/days for cycle-accurate simulation.

**Default configuration**: UCIe link at 32 GB/s, NAND chiplets at 2.4 GB/s (ONFI 5.1), 16 KB page reads.

| Finding | Value |
|---|---|
| Monolithic baseline latency | 53.0 μs |
| Star latency at N=1 | 54.0 μs (+1.9% overhead) |
| Star latency at N=32 | 85.8 μs (+61.8% overhead) |
| Saturation boundary N* | 13.3 chiplets |
| Scalability η at N=32 (Star) | 41.7% |
| η drops below 80% at | N = 20 |
| P99 tail latency at ρ=0.9 | 2,250 μs (4.5× average) |

**Topology comparison at N=32**:

| Topology | Latency (μs) | Throughput (GB/s) | η |
|---|---|---|---|
| Star | 85.8 | 32.0 | 41.7% |
| Multi-Port (P=4) | 61.2 | 32.0 | 41.7% |
| Hierarchical (K=4) | 66.3 | 32.0 | 41.7% |
| Monolithic (baseline) | 53.0 | — | — |

**Key architectural insights** (matching thesis expected results, Chapter 7):

1. **Chiplet count scaling is not linear** — link contention grows with N due to arbitration delay
2. **Beyond N*=13 chiplets, the link saturates** — additional NAND chiplets provide no throughput improvement
3. **Multi-Port topology reduces latency** — distributing traffic across P ports reduces per-port contention from M=N to M=N/P
4. **Hierarchical topology trades latency for scalability** — extra hop adds ~5 μs but enables better fan-out for large N
5. **Tail latency degrades sharply near saturation** — P99 is 4.5× average at ρ=0.9

### RapidChiplet Paper Reproduction Results

| Metric | Value |
|---|---|
| Average Latency Error | ~2.4% |
| Average Latency Speedup | ~954× over BookSim2 |
| Average Throughput Error | ~24.7% |
| Average Throughput Speedup | ~43,136× over BookSim2 |
| Case study SHG configs | 65,536 (6,816 unique Pareto-optimal points) |

---

## Repository Structure

```
rapidchiplet/
│
├── ── NAND Chiplet DSE (Thesis contribution) ──────────────
├── run_nand_dse.py                # Main DSE runner script
├── nand_chiplet_dse/              # NAND storage chiplet framework
│   ├── __init__.py                # Package metadata
│   ├── config.py                  # Default parameters (NAND/UCIe specs)
│   ├── models.py                  # Analytical models (Ch. 3–4)
│   ├── topologies.py              # Star, Multi-Port, Hierarchical (Ch. 5)
│   ├── dse.py                     # Design space exploration engine (Ch. 6)
│   └── plots.py                   # 12 publication-quality plot generators
│
├── ── RapidChiplet Toolchain (Reproduced) ─────────────────
├── rapidchiplet.py                # Core RapidChiplet engine
├── run_experiment.py              # Automated DSE runner
├── reproduce_paper_results.py     # Paper reproduction script
├── case_study.py                  # SHG topology case study
├── create_paper_plots.py          # Paper figure generation (patched)
├── booksim_wrapper.py             # BookSim2 integration
├── helpers.py                     # Shared utilities
├── visualizer.py                  # Chip design visualization
├── generate_*.py                  # Input generators
│
├── booksim2/src/                  # BookSim2 simulator (built)
├── netrace/                       # Netrace trace export tool
├── experiments/                   # Experiment configurations
├── inputs/                        # Input specification files
├── results/                       # All experiment results
│   └── nand_dse/                  # NAND DSE results (JSON)
├── plots/                         # Generated evaluation plots
│   └── nand_dse/                  # 12 NAND DSE plots (PDF)
└── images/                        # Design visualizations
```

---

## Environment Setup

### Prerequisites

- **Operating System**: Windows 10/11 (tested), Linux (supported)
- **Python**: 3.10+ (tested with Python 3.11.15)
- **C/C++ Compiler**: GCC with C++11 support (for BookSim2 build only)

### Conda Environment

```bash
conda create -n rapidchiplet python=3.11 -y
conda activate rapidchiplet
pip install -r requirements.txt
```

### Build Tools (Windows, for RapidChiplet reproduction only)

```bash
conda install -c msys2 m2w64-gcc m2w64-toolchain make m2-bison m2-flex -y
cd booksim2/src && make && cd ../..
cd netrace && gcc export_trace.c netrace.c -o export_trace && cd ..
```

---

## Running the NAND Chiplet DSE

```bash
python run_nand_dse.py
```

This runs in **under 1 second** and produces:
- 12 PDF plots in `plots/nand_dse/`
- Full results JSON in `results/nand_dse/nand_dse_results.json`
- Console summary of key findings

### Custom Configuration

```bash
python run_nand_dse.py --config my_config.json
```

Override any parameter (e.g., link bandwidth, NAND timing, chiplet counts).

### Regenerate Plots Only

```bash
python run_nand_dse.py --plots-only
```

---

## Running the RapidChiplet Reproduction

```bash
python reproduce_paper_results.py
```

> **Note**: Runtime ~1 day (BookSim2 simulations dominate). Run as background process on Windows:
> ```powershell
> Start-Process python -ArgumentList "reproduce_paper_results.py" `
>     -RedirectStandardOutput reproduce_output.log `
>     -RedirectStandardError reproduce_error.log -NoNewWindow
> ```

## Challenges and Fixes

### 1. Windows Build Environment

**Problem**: The upstream toolchain assumes a Linux environment. Building BookSim2 on Windows required specific adaptations.

**Solution**: 
- Installed MinGW-w64 via Conda (`m2w64-gcc`, `m2w64-toolchain`)
- Added `-std=c++11` flag to `booksim2/src/Makefile` for C++11 template support
- Manually downloaded `nlohmann/json.hpp` header (not included in repository)

### 2. Missing Input File

**Problem**: `reproduce_paper_results.py` references `inputs/designs/example_design.json`, which is not included in the repository.

**Solution**: Created the design file manually, pointing to the existing example input files (chiplets, placement, topology, packaging, routing table, technology, traffic, booksim config).

### 3. NaN/Inf Crash in Plot Generation

**Problem**: After all 560 experiments completed successfully, the evaluation plot generation (`create_paper_plots.py`) crashed with:
```
ValueError: Axis limits cannot be NaN or Inf
```

**Root cause**: RapidChiplet's proxy calculations for small networks (2×2, 3×3) run so fast that the measured `time_taken` is `0.0` seconds. Computing speedup ratios (BookSim runtime ÷ proxy runtime) produces `Inf`, which propagates through `min()`/`max()` into matplotlib axis limits.

**Fix**: Modified `create_paper_plots.py` to:
1. Filter `NaN`/`Inf` values before computing `min()`/`max()` limits
2. Guard `set_ylim()` calls against non-finite limit values
3. Applied the fix to both `create_evaluation_plot()` and `create_extended_evaluation_plot()`

```python
# Before (crashes on Inf values):
limits[k][0] = min(limits[k][0], min(metric))

# After (filters non-finite values):
finite_vals = [v for v in metric if not (math.isnan(v) or math.isinf(v))]
if finite_vals:
    limits[k][0] = min(limits[k][0], min(finite_vals))
```

### 4. Long-Running Process Management

**Problem**: Running `reproduce_paper_results.py` interactively in a terminal risks interruption (accidental Ctrl+C, terminal timeout, session disconnection).

**Solution**: Used Windows `Start-Process` with output redirection to run the ~20-hour BookSim2 simulation phase as a detached background process:
```powershell
Start-Process -FilePath "python.exe" -ArgumentList "reproduce_paper_results.py" `
    -RedirectStandardOutput "reproduce_output.log" `
    -RedirectStandardError "reproduce_error.log" `
    -NoNewWindow
```

---

## References

[1] **UCIe Consortium**, "Universal Chiplet Interconnect Express (UCIe) Specification," Version 1.0, 2023.

[2] **Hofmeier, P., Di Girolamo, S., Renggli, C., & Hoefler, T.** (2024). *RapidChiplet: A Toolchain for Rapid Design Space Exploration of Chiplet Architectures.* arXiv:2311.06081v2. [https://arxiv.org/abs/2311.06081](https://arxiv.org/abs/2311.06081)

[3] **Clark, M.** (2020). *AMD Chiplet Architecture in Modern Processors.* IEEE Micro, 40(2), pp. 28–37.

[4] **Jiang, N., Becker, D.U., et al.** (2013). *A Detailed and Flexible Cycle-Accurate Network-on-Chip Simulator.* IEEE ISPASS 2013, pp. 86–96.

[5] **NVM Express**, "NVM Express Base Specification," Revision 2.0, 2021.

[6] **JEDEC**, "Universal Flash Storage (UFS) Specification," JESD220F, 2023.

[7] **Tavakkol, A., et al.** (2018). *MQSim: A Framework for Enabling Realistic Studies of Modern Multi-Queue SSD Devices.* USENIX FAST 2018.

[8] **Kleinrock, L.** (1975). *Queueing Systems, Volume I: Theory.* Wiley-Interscience.

[9] **Hestness, J., Grot, B., & Keckler, S.W.** (2010). *Netrace: Dependency-Driven Trace-Based Network-on-Chip Simulation.* NoCArc 2010, pp. 31–36.

---

## License

This work builds upon the RapidChiplet toolchain by Hofmeier et al. (SPCL, ETH Zürich). See the original repository for licensing terms: [https://github.com/spcl/rapidchiplet](https://github.com/spcl/rapidchiplet).
