"""
Complete Figures for Paper
All results: Classical, Greedy, CPP-LC, ML/RL, Real Data
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 10

def generate_complete_figures():
    """Generate all figures for paper"""
    
    df = pd.read_csv("results_final_complete/all_results.csv")
    output_dir = Path("figures_complete")
    output_dir.mkdir(exist_ok=True)
    
    print("="*70)
    print("GENERATING COMPLETE FIGURES")
    print("="*70)
    
    # Figure 1: Overall Algorithm Comparison
    print("\n📊 Figure 1: Algorithm Comparison...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    sns.boxplot(data=df, x='algorithm', y='cost', ax=ax1)
    ax1.set_xlabel('Algorithm')
    ax1.set_ylabel('Solution Cost')
    ax1.set_title('Solution Quality Comparison')
    ax1.grid(True, alpha=0.3, axis='y')
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
    
    # Optimality gap
    gap_data = df[df['gap_from_classical'].notna()]
    sns.boxplot(data=gap_data, x='algorithm', y='gap_from_classical', ax=ax2)
    ax2.set_xlabel('Algorithm')
    ax2.set_ylabel('Optimality Gap (%)')
    ax2.set_title('Optimality Gap Distribution')
    ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    ax2.grid(True, alpha=0.3, axis='y')
    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    fig.savefig(output_dir / "fig1_algorithm_comparison.pdf")
    fig.savefig(output_dir / "fig1_algorithm_comparison.png", dpi=300)
    plt.close()
    print("   ✓ Saved")
    
    # Figure 2: CPP-LC Cost Increase
    print("\n📊 Figure 2: CPP-LC Cost Increase...")
    cpp_lc = df[df['algorithm'] == 'cpp_lc_fast']
    
    if not cpp_lc.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.hist(cpp_lc['gap_from_classical'], bins=20, alpha=0.7, 
               color='steelblue', edgecolor='black')
        
        mean_gap = cpp_lc['gap_from_classical'].mean()
        ax.axvline(x=mean_gap, color='red', linestyle='--', linewidth=2,
                   label=f'Mean: {mean_gap:.1f}%')
        
        ax.set_xlabel('Cost Increase vs. Classical CPP (%)')
        ax.set_ylabel('Frequency')
        ax.set_title('CPP-LC: Load-Dependent Cost Impact')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        fig.savefig(output_dir / "fig2_cpp_lc_impact.pdf")
        fig.savefig(output_dir / "fig2_cpp_lc_impact.png", dpi=300)
        plt.close()
        print("   ✓ Saved")
    else:
        print("   ⚠️  No CPP-LC data")
    
    # Figure 3: Learning Performance  
    print("\n📊 Figure 3: ML/RL Performance...")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    algorithms = ['classical_cpp', 'greedy', 'ml_learning']
    data_for_plot = df[df['algorithm'].isin(algorithms)]
    
    sns.violinplot(data=data_for_plot, x='algorithm', y='cost', ax=ax)
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Solution Cost')
    ax.set_title('Learning-Based vs. Classical Approaches')
    ax.grid(True, alpha=0.3, axis='y')
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    fig.savefig(output_dir / "fig3_ml_performance.pdf")
    fig.savefig(output_dir / "fig3_ml_performance.png", dpi=300)
    plt.close()
    print("   ✓ Saved")
    
    # Figure 4: Real-World Validation (London)
    print("\n📊 Figure 4: Real-World Validation...")
    
    real_data = df[df['network_family'] == 'osm_real']
    synthetic_data = df[df['network_family'] != 'osm_real']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Compare performance on real vs synthetic
    comparison_data = []
    for algo in df['algorithm'].unique():
        real_algo = real_data[real_data['algorithm'] == algo]
        synth_algo = synthetic_data[synthetic_data['algorithm'] == algo]
        
        if not real_algo.empty:
            comparison_data.append({
                'Algorithm': algo,
                'Data': 'Real (London)',
                'Gap': real_algo['gap_from_classical'].mean()
            })
        
        if not synth_algo.empty:
            comparison_data.append({
                'Algorithm': algo,
                'Data': 'Synthetic',
                'Gap': synth_algo['gap_from_classical'].mean()
            })
    
    if comparison_data:
        comp_df = pd.DataFrame(comparison_data)
        comp_pivot = comp_df.pivot(index='Algorithm', columns='Data', values='Gap')
        
        comp_pivot.plot(kind='bar', ax=ax, width=0.7)
        ax.set_xlabel('Algorithm')
        ax.set_ylabel('Mean Optimality Gap (%)')
        ax.set_title('Performance: Real-World vs. Synthetic Networks')
        ax.legend(title='Network Type')
        ax.grid(True, alpha=0.3, axis='y')
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        fig.savefig(output_dir / "fig4_real_vs_synthetic.pdf")
        fig.savefig(output_dir / "fig4_real_vs_synthetic.png", dpi=300)
        plt.close()
        print("   ✓ Saved")
    else:
        print("   ⚠️  No real data for comparison")
    
    # Figure 5: Comprehensive Summary
    print("\n📊 Figure 5: Comprehensive Summary...")
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Top-left: Cost by algorithm
    ax = axes[0, 0]
    df.groupby('algorithm')['cost'].mean().plot(kind='bar', ax=ax, color='steelblue')
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Mean Cost')
    ax.set_title('(a) Mean Solution Cost')
    ax.grid(True, alpha=0.3, axis='y')
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    # Top-right: Runtime
    ax = axes[0, 1]
    df.groupby('algorithm')['runtime_seconds'].mean().plot(kind='bar', ax=ax, color='coral')
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Mean Runtime (s)')
    ax.set_title('(b) Computational Efficiency')
    ax.grid(True, alpha=0.3, axis='y')
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    # Bottom-left: Gap distribution
    ax = axes[1, 0]
    gap_by_algo = df[df['gap_from_classical'].notna()].groupby('algorithm')['gap_from_classical'].mean()
    gap_by_algo.plot(kind='bar', ax=ax, color='green', alpha=0.7)
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Mean Gap (%)')
    ax.set_title('(c) Optimality Gap')
    ax.axhline(y=0, color='red', linestyle='--')
    ax.grid(True, alpha=0.3, axis='y')
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    # Bottom-right: Instance count
    ax = axes[1, 1]
    df['algorithm'].value_counts().plot(kind='bar', ax=ax, color='purple', alpha=0.7)
    ax.set_xlabel('Algorithm')
    ax.set_ylabel('Number of Instances')
    ax.set_title('(d) Coverage')
    ax.grid(True, alpha=0.3, axis='y')
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    fig.savefig(output_dir / "fig5_comprehensive_summary.pdf")
    fig.savefig(output_dir / "fig5_comprehensive_summary.png", dpi=300)
    plt.close()
    print("   ✓ Saved")
    
    print("\n" + "="*70)
    print("✅ ALL FIGURES GENERATED")
    print("="*70)
    print(f"\nOutput: {output_dir}/")
    print("\nFiles:")
    for f in sorted(output_dir.glob("*.pdf")):
        print(f"  - {f.name}")
    
    # Print key statistics for paper
    print("\n" + "="*70)
    print("KEY STATISTICS FOR PAPER")
    print("="*70)
    
    print(f"\nTotal experiments: {len(df)}")
    print(f"Algorithms tested: {df['algorithm'].nunique()}")
    print(f"Unique instances: {df['instance_id'].nunique()}")
    
    print("\nOptimality gaps:")
    for algo in df['algorithm'].unique():
        gap = df[df['algorithm'] == algo]['gap_from_classical'].mean()
        if not np.isnan(gap):
            print(f"  {algo}: {gap:.1f}%")
    
    # CPP-LC finding
    cpp_lc = df[df['algorithm'] == 'cpp_lc_fast']
    if not cpp_lc.empty:
        print(f"\n🔥 CPP-LC KEY FINDING:")
        print(f"   Load-dependent costs increase tour cost by {cpp_lc['gap_from_classical'].mean():.1f}%")
    
    # Real data
    real = df[df['network_family'] == 'osm_real']
    if not real.empty:
        print(f"\n🌍 REAL-WORLD VALIDATION:")
        print(f"   Tested on London street network ({real.iloc[0]['num_nodes']} nodes)")


if __name__ == "__main__":
    generate_complete_figures()
