#!/usr/bin/env python3
"""
NAND Chiplet DSE — Main Runner Script

Master Thesis: Architecture and Rapid Design Space Exploration of
               Chiplet-Based NAND Storage Subsystems

Author:  Antony Amburose (2024OVL1077)
Supervisor: Dr. Kankat Ghosh
Institute: IIT Jammu, CEP Department

Usage:
    python run_nand_dse.py                        # Run with default config
    python run_nand_dse.py --config my_config.json # Custom config
    python run_nand_dse.py --plots-only            # Regenerate plots from saved results

This script:
  1. Runs the complete Design Space Exploration across all parameter combinations
  2. Generates all publication-quality plots for the thesis
  3. Prints a summary of key findings

Produces 12 plots in plots/nand_dse/:
  - latency_breakdown.pdf          (Chapter 3: Monolithic vs Chiplet)
  - latency_vs_chiplet_count.pdf   (Chapter 5: Topology comparison)
  - throughput_vs_chiplet_count.pdf (Chapter 5: Throughput scaling)
  - scalability_efficiency.pdf     (Chapter 5: η vs N)
  - link_utilization.pdf           (Chapter 5: Link saturation)
  - queueing_response_time.pdf     (Chapter 4: M/M/1 analysis)
  - tail_latency_vs_load.pdf       (Chapter 4: P99 tail latency)
  - bandwidth_impact.pdf           (Chapter 6: B_link sweep)
  - request_size_impact.pdf        (Chapter 6: Request size sweep)
  - saturation_boundary.pdf        (Chapter 6: N* boundary)
  - dse_heatmaps.pdf               (Chapter 6: 2D design space)
  - topology_comparison_panel.pdf  (Chapter 5: Comprehensive 4-panel)
"""

import sys
import os
import json
import argparse
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nand_chiplet_dse.config import get_config, load_config, save_config
from nand_chiplet_dse.dse import run_full_dse
from nand_chiplet_dse.plots import generate_all_plots
from nand_chiplet_dse import models
from nand_chiplet_dse.topologies import ALL_TOPOLOGIES


def print_banner():
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║    NAND Chiplet DSE — Chiplet-Based NAND Storage Subsystems    ║")
    print("║                                                                ║")
    print("║    Master Thesis: Antony Amburose (2024OVL1077)                ║")
    print("║    IIT Jammu — CEP Department                                  ║")
    print("║    Supervisor: Dr. Kankat Ghosh                                ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()


def print_config_summary(config):
    """Print a formatted summary of the active configuration."""
    print("─" * 50)
    print("  Configuration Summary")
    print("─" * 50)
    print(f"  Controller latency:    {config['ctrl_latency_us']} μs")
    print(f"  Controller bandwidth:  {config['ctrl_bw_gbps']} GB/s")
    print(f"  NAND read latency:     {config['nand_read_latency_us']} μs")
    print(f"  NAND program latency:  {config['nand_prog_latency_us']} μs")
    print(f"  NAND per-chiplet BW:   {config['nand_bw_gbps']} GB/s")
    print(f"  Link bandwidth:        {config['link_bw_gbps']} GB/s")
    print(f"  Link propagation:      {config['link_prop_us']*1e3:.1f} ns")
    print(f"  Request size:          {config['request_size_bytes']//1024} KB")
    print(f"  Controller ports (P):  {config['num_ports']}")
    print(f"  Aggregators (K):       {config['num_aggregators']}")
    print(f"  Chiplet counts:        {config['chiplet_counts']}")
    print(f"  Link BW range:         {config['link_bw_range_gbps']} GB/s")
    n_star = models.saturation_chiplet_count(config["link_bw_gbps"], config["nand_bw_gbps"])
    print(f"  Saturation N*:         {n_star:.1f} chiplets")
    print("─" * 50)


def print_results_summary(results):
    """Print key findings from the DSE."""
    config = results["config"]
    topo = results["topology_sweep"]

    print()
    print("═" * 60)
    print("  KEY FINDINGS")
    print("═" * 60)

    # Monolithic baseline
    mono_lat = models.total_latency_monolithic_us(
        config["ctrl_latency_us"], config["nand_read_latency_us"]
    )
    print(f"\n  Monolithic baseline latency: {mono_lat:.1f} μs")

    # Per-topology summary
    for t in ALL_TOPOLOGIES:
        d = topo[t.name]
        # Find N where scalability drops below 80%
        n_80 = None
        for i, eta in enumerate(d["scalability"]):
            if eta < 0.8:
                n_80 = d["N"][i]
                break

        lat_N1 = d["latency_us"][0]
        lat_Nmax = d["latency_us"][-1]
        tp_Nmax = d["throughput_gbps"][-1]
        eta_Nmax = d["scalability"][-1]
        overhead_N1 = (lat_N1 - mono_lat) / mono_lat * 100

        print(f"\n  ── {t.name} Topology ──")
        print(f"    Latency at N=1:            {lat_N1:.2f} μs  (+{overhead_N1:.1f}% overhead)")
        print(f"    Latency at N={d['N'][-1]}:           {lat_Nmax:.2f} μs")
        print(f"    Max throughput (N={d['N'][-1]}):     {tp_Nmax:.1f} GB/s")
        print(f"    Scalability η at N={d['N'][-1]}:     {eta_Nmax:.2%}")
        if n_80:
            print(f"    η drops below 80% at:      N = {n_80}")

    # Saturation
    n_star = models.saturation_chiplet_count(config["link_bw_gbps"], config["nand_bw_gbps"])
    print(f"\n  ── Saturation Boundary ──")
    print(f"    N* = B_link / B_NAND = {config['link_bw_gbps']}/{config['nand_bw_gbps']} = {n_star:.1f}")
    print(f"    Beyond N={int(n_star)}, adding chiplets gives NO throughput benefit (star)")

    # Queueing
    q = results["queueing_analysis"]["single_server"]
    idx_90 = next(i for i, r in enumerate(q["load_factors"]) if r >= 0.9)
    print(f"\n  ── Queueing (M/M/1 at ρ=0.9) ──")
    print(f"    Average response:  {q['response_time_us'][idx_90]:.1f} μs")
    print(f"    P99 tail latency:  {q['p99_latency_us'][idx_90]:.1f} μs")
    print(f"    Ratio P99/avg:     {q['p99_latency_us'][idx_90]/q['response_time_us'][idx_90]:.1f}x")

    print()
    print(f"  DSE runtime: {results['runtime_seconds']:.2f} seconds")
    print(f"  (Equivalent cycle-accurate simulation would take ~hours/days)")
    print("═" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="NAND Chiplet DSE — Design Space Exploration"
    )
    parser.add_argument(
        "--config", "-c", type=str, default=None,
        help="Path to custom config JSON file (overrides defaults)"
    )
    parser.add_argument(
        "--output-dir", "-o", type=str, default="results/nand_dse",
        help="Output directory for results (default: results/nand_dse)"
    )
    parser.add_argument(
        "--plot-dir", "-p", type=str, default="plots/nand_dse",
        help="Output directory for plots (default: plots/nand_dse)"
    )
    parser.add_argument(
        "--plots-only", action="store_true",
        help="Only regenerate plots from existing results"
    )
    parser.add_argument(
        "--no-plots", action="store_true",
        help="Skip plot generation"
    )
    args = parser.parse_args()

    print_banner()

    # Load config
    if args.config:
        config = load_config(args.config)
        print(f"  Loaded config from: {args.config}")
    else:
        config = get_config()
        print("  Using default configuration")

    print_config_summary(config)

    if args.plots_only:
        # Load existing results
        results_file = os.path.join(args.output_dir, "nand_dse_results.json")
        if not os.path.exists(results_file):
            print(f"ERROR: No results file found at {results_file}")
            print("Run the DSE first without --plots-only")
            sys.exit(1)
        with open(results_file, "r") as f:
            results = json.load(f)
        print(f"\n  Loaded results from: {results_file}")
        generate_all_plots(results, args.plot_dir)
    else:
        # Run full DSE
        results = run_full_dse(config, args.output_dir, verbose=True)

        # Print summary
        print_results_summary(results)

        # Generate plots
        if not args.no_plots:
            generate_all_plots(results, args.plot_dir)

        # Save config for reproducibility
        save_config(config, os.path.join(args.output_dir, "config_used.json"))

    print("\nDone!")


if __name__ == "__main__":
    main()
