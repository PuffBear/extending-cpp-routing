"""
Fast Plotting - Essential Figures Only
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# High-quality settings
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 10

def generate_fast_figures(results_csv="experimental_results_fast/all_results.csv"):
    """Generate essential figures"""
    
    df = pd.read_csv(results_csv)
    output_dir = Path("figures_fast")
    output_dir.mkdir(exist_ok=True)
    
    print("="*70)
    print("GENERATING FIGURES")
    print("="*70)
    
    # Figure 1: Algorithm Comparison
    print("\n📊 Figure 1: Algorithm Comparison (boxplot)...")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sns.boxplot(data=df, x='algorithm', y='cost', ax=ax, palette='Set2')
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Solution Cost')
    ax.set_title('Algorithm Performance Comparison')
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    fig.savefig(output_dir / "fig1_algorithm_comparison.pdf")
    fig.savefig(output_dir / "fig1_algorithm_comparison.png", dp=300)
    plt.close(fig)
    print("   ✓ Saved")
    
    # Figure 2: Runtime vs Quality
    print("\n📊 Figure 2: Runtime vs Quality...")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for algo in df['algorithm'].unique():
        algo_data = df[df['algorithm'] == algo]
        ax.scatter(algo_data['runtime_seconds'], algo_data['cost'], 
                  s=100, alpha=0.6, label=algo)
    
    ax.set_xlabel('Runtime (seconds)')
    ax.set_ylabel('Solution Cost')
    ax.set_title('Runtime vs. Solution Quality Tradeoff')
    ax.set_xscale('log')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    fig.savefig(output_dir / "fig2_runtime_vs_quality.pdf")
    fig.savefig(output_dir / "fig2_runtime_vs_quality.png", dpi=300)
    plt.close(fig)
    print("   ✓ Saved")
    
    # Figure 3: Performance by Network Type
    print("\n📊 Figure 3: Performance by Network Family...")
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Group by network family and algorithm
    data_pivot = df.pivot_table(
        values='cost',
        index='network_family',
        columns='algorithm',
        aggfunc='mean'
    )
    
    data_pivot.plot(kind='bar', ax=ax, width=0.8)
    ax.set_xlabel('Network Family')
    ax.set_ylabel('Mean Cost')
    ax.set_title('Algorithm Performance by Network Topology')
    ax.legend(title='Algorithm')
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    fig.savefig(output_dir / "fig3_network_family.pdf")
    fig.savefig(output_dir / "fig3_network_family.png", dpi=300)
    plt.close(fig)
    print("   ✓ Saved")
    
    #Figure 4: Scalability
    print("\n📊 Figure 4: Scalability Analysis...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Runtime vs nodes
    ax = axes[0]
    for algo in df['algorithm'].unique():
        algo_data = df[df['algorithm'] == algo]
        grouped = algo_data.groupby('num_nodes').agg({
            'runtime_seconds': 'mean'
        }).reset_index()
        
        if len(grouped) >= 2:
            ax.plot(grouped['num_nodes'], grouped['runtime_seconds'], 
                   marker='o', label=algo, linewidth=2)
    
    ax.set_xlabel('Number of Nodes')
    ax.set_ylabel('Runtime (seconds)')
    ax.set_title('Scalability: Runtime vs. Graph Size')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Cost vs nodes
    ax = axes[1]
    for algo in df['algorithm'].unique():
        algo_data = df[df['algorithm'] == algo]
        grouped = algo_data.groupby('num_nodes').agg({
            'cost': 'mean'
        }).reset_index()
        
        if len(grouped) >= 2:
            ax.plot(grouped['num_nodes'], grouped['cost'], 
                   marker='s', label=algo, linewidth=2)
    
    ax.set_xlabel('Number of Nodes')
    ax.set_ylabel('Solution Cost')
    ax.set_title('Solution Quality vs. Graph Size')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    fig.savefig(output_dir / "fig4_scalability.pdf")
    fig.savefig(output_dir / "fig4_scalability.png", dpi=300)
    plt.close(fig)
    print("   ✓ Saved")
    
    print("\n" + "="*70)
    print("✅ ALL FIGURES GENERATED")
    print("="*70)
    print(f"\nSaved to: {output_dir}/")
    print("\nFiles:")
    for f in sorted(output_dir.glob("*.pdf")):
        print(f"  - {f.name}")


if __name__ == "__main__":
    generate_fast_figures()
