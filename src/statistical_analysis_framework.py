"""
Statistical Analysis Framework
Rigorous statistical testing for experimental results
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import wilcoxon, mannwhitneyu, friedmanchisquare
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class StatisticalAnalyzer:
    """
    Production-ready statistical analysis for CPP experiments
    """
    
    def __init__(self, results_df: pd.DataFrame, alpha: float = 0.05):
        """
        Args:
            results_df: DataFrame with experimental results
            alpha: Significance level (default 0.05 for 95% CI)
        """
        self.df = results_df
        self.alpha = alpha
        self.results = {}
    
    def pairwise_algorithm_comparison(self, metric: str = 'cost') -> pd.DataFrame:
        """
        Pairwise comparison of algorithms using Wilcoxon signed-rank test
        
        Args:
            metric: Metric to compare ('cost', 'runtime_seconds', 'gap_from_classical')
            
        Returns:
            DataFrame with p-values and effect sizes
        """
        print(f"\n📊 Pairwise Algorithm Comparison ({metric})")
        print("=" * 70)
        
        algorithms = self.df['algorithm'].unique()
        n_algorithms = len(algorithms)
        
        # Initialize results matrices
        p_values = np.zeros((n_algorithms, n_algorithms))
        effect_sizes = np.zeros((n_algorithms, n_algorithms))
        
        comparisons = []
        
        for i, algo1 in enumerate(algorithms):
            for j, algo2 in enumerate(algorithms):
                if i >= j:
                    continue
                
                # Get results for both algorithms on same instances
                df1 = self.df[self.df['algorithm'] == algo1]
                df2 = self.df[self.df['algorithm'] == algo2]
                
                # Match by instance_id
                merged = pd.merge(
                    df1[['instance_id', metric]],
                    df2[['instance_id', metric]],
                    on='instance_id',
                    suffixes=('_1', '_2')
                )
                
                if len(merged) < 5:  # Need at least 5 paired samples
                    continue
                
                values1 = merged[f'{metric}_1'].values
                values2 = merged[f'{metric}_2'].values
                
                # Wilcoxon signed-rank test (paired, non-parametric)
                try:
                    statistic, p_value = wilcoxon(values1, values2, alternative='two-sided')
                except Exception as e:
                    p_value = 1.0
                    statistic = 0
                
                # Cohen's d effect size
                diff = values1 - values2
                cohens_d = np.mean(diff) / np.std(diff) if np.std(diff) > 0 else 0
                
                p_values[i, j] = p_value
                p_values[j, i] = p_value
                effect_sizes[i, j] = cohens_d
                effect_sizes[j, i] = -cohens_d
                
                # Store comparison
                comparisons.append({
                    'algorithm_1': algo1,
                    'algorithm_2': algo2,
                    'n_instances': len(merged),
                    'p_value': p_value,
                    'p_value_bonferroni': min(p_value * (n_algorithms * (n_algorithms - 1) / 2), 1.0),
                    'cohens_d': cohens_d,
                    'effect_interpretation': self._interpret_cohens_d(cohens_d),
                    'significant': p_value < self.alpha,
                    'mean_diff': np.mean(diff),
                    'median_diff': np.median(diff)
                })
        
        # Create DataFrame
        comparisons_df = pd.DataFrame(comparisons)
        
        # Print summary
        print(f"\nTotal comparisons: {len(comparisons)}")
        print(f"Significant (α={self.alpha}): {comparisons_df['significant'].sum()}")
        print(f"\nTop 5 by effect size:\n")
        print(comparisons_df.nlargest(5, 'cohens_d')[
            ['algorithm_1', 'algorithm_2', 'cohens_d', 'p_value', 'significant']
        ])
        
        self.results['pairwise_comparisons'] = comparisons_df
        
        return comparisons_df
    
    def compute_confidence_intervals(self, metric: str = 'cost', 
                                    bootstrap_samples: int = 1000) -> pd.DataFrame:
        """
        Compute confidence intervals for each algorithm
        
        Args:
            metric: Metric to analyze
            bootstrap_samples: Number of bootstrap samples
            
        Returns:
            DataFrame with confidence intervals
        """
        print(f"\n📊 Confidence Intervals ({metric})")
        print("=" * 70)
        
        ci_results = []
        
        for algorithm in self.df['algorithm'].unique():
            data = self.df[self.df['algorithm'] == algorithm][metric].values
            
            if len(data) < 2:
                continue
            
            # Parametric CI (assume normal)
            mean = np.mean(data)
            sem = stats.sem(data)
            ci_parametric = stats.t.interval(
                1 - self.alpha,
                len(data) - 1,
                loc=mean,
                scale=sem
            )
            
            # Bootstrap CI (non-parametric)
            bootstrap_means = []
            for _ in range(bootstrap_samples):
                sample = np.random.choice(data, size=len(data), replace=True)
                bootstrap_means.append(np.mean(sample))
            
            ci_bootstrap = np.percentile(bootstrap_means, [self.alpha/2*100, (1-self.alpha/2)*100])
            
            ci_results.append({
                'algorithm': algorithm,
                'n': len(data),
                'mean': mean,
                'std': np.std(data),
                'median': np.median(data),
                'ci_lower_parametric': ci_parametric[0],
                'ci_upper_parametric': ci_parametric[1],
                'ci_lower_bootstrap': ci_bootstrap[0],
                'ci_upper_bootstrap': ci_bootstrap[1],
                'ci_width_parametric': ci_parametric[1] - ci_parametric[0],
                'ci_width_bootstrap': ci_bootstrap[1] - ci_bootstrap[0]
            })
        
        ci_df = pd.DataFrame(ci_results)
        
        print(ci_df[['algorithm', 'mean', 'ci_lower_bootstrap', 'ci_upper_bootstrap']])
        
        self.results['confidence_intervals'] = ci_df
        
        return ci_df
    
    def win_tie_loss_analysis(self, metric: str = 'cost') -> pd.DataFrame:
        """
        Win-Tie-Loss record for each algorithm pair
        
        Args:
            metric: Metric to compare (lower is better for cost)
            
        Returns:
            DataFrame with W-T-L records
        """
        print(f"\n📊 Win-Tie-Loss Analysis ({metric})")
        print("=" * 70)
        
        algorithms = self.df['algorithm'].unique()
        wtl_results = []
        
        for algo1 in algorithms:
            for algo2 in algorithms:
                if algo1 == algo2:
                    continue
                
                # Get paired results
                df1 = self.df[self.df['algorithm'] == algo1]
                df2 = self.df[self.df['algorithm'] == algo2]
                
                merged = pd.merge(
                    df1[['instance_id', metric]],
                    df2[['instance_id', metric]],
                    on='instance_id',
                    suffixes=('_1', '_2')
                )
                
                if len(merged) == 0:
                    continue
                
                # Count wins, ties, losses (lower is better)
                wins = (merged[f'{metric}_1'] < merged[f'{metric}_2']).sum()
                ties = (merged[f'{metric}_1'] == merged[f'{metric}_2']).sum()
                losses = (merged[f'{metric}_1'] > merged[f'{metric}_2']).sum()
                
                wtl_results.append({
                    'algorithm': algo1,
                    'vs_algorithm': algo2,
                    'wins': wins,
                    'ties': ties,
                    'losses': losses,
                    'total': len(merged),
                    'win_rate': wins / len(merged) if len(merged) > 0 else 0
                })
        
        wtl_df = pd.DataFrame(wtl_results)
        
        # Aggregate wins per algorithm
        total_wins = wtl_df.groupby('algorithm')['wins'].sum().sort_values(ascending=False)
        print("\nTotal wins by algorithm:")
        print(total_wins)
        
        self.results['win_tie_loss'] = wtl_df
        
        return wtl_df
    
    def performance_profiles(self, metric: str = 'gap_from_classical',
                            tau_values: List[float] = None) -> pd.DataFrame:
        """
        Generate performance profiles
        
        Shows what % of instances each algorithm solves within τ% of optimal
        
        Args:
            metric: Metric to use (gap from optimal/best)
            tau_values: Threshold values (default: [0, 5, 10, 20, 50, 100])
            
        Returns:
            DataFrame with performance profile
        """
        if tau_values is None:
            tau_values = [0, 5, 10, 20, 50, 100]
        
        print(f"\n📊 Performance Profiles ({metric})")
        print("=" * 70)
        
        algorithms = self.df['algorithm'].unique()
        profiles = []
        
        for algorithm in algorithms:
            algo_data = self.df[self.df['algorithm'] == algorithm]
            
            if metric not in algo_data.columns:
                continue
            
            gaps = algo_data[metric].dropna().values
            n_total = len(gaps)
            
            for tau in tau_values:
                # Count instances solved within tau% of optimal
                n_within_tau = (np.abs(gaps) <= tau).sum()
                pct_solved = n_within_tau / n_total * 100 if n_total > 0 else 0
                
                profiles.append({
                    'algorithm': algorithm,
                    'tau': tau,
                    'pct_instances_within_tau': pct_solved,
                    'n_within_tau': n_within_tau,
                    'n_total': n_total
                })
        
        profiles_df = pd.DataFrame(profiles)
        
        # Pivot for nice display
        pivot = profiles_df.pivot(index='algorithm', columns='tau', values='pct_instances_within_tau')
        print("\n% of instances solved within τ% of optimal:\n")
        print(pivot.round(1))
        
        self.results['performance_profiles'] = profiles_df
        
        return profiles_df
    
    def bonferroni_correction(self, comparisons_df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply Bonferroni correction for multiple testing
        
        Args:
            comparisons_df: DataFrame from pairwise_algorithm_comparison
            
        Returns:
            DataFrame with corrected p-values
        """
        n_comparisons = len(comparisons_df)
        corrected_alpha = self.alpha / n_comparisons
        
        comparisons_df['p_value_bonferroni'] = comparisons_df['p_value'] * n_comparisons
        comparisons_df['p_value_bonferroni'] = comparisons_df['p_value_bonferroni'].clip(upper=1.0)
        comparisons_df['significant_bonferroni'] = comparisons_df['p_value_bonferroni'] < self.alpha
        
        print(f"\n📊 Bonferroni Correction")
        print(f"   Original α: {self.alpha}")
        print(f"   Corrected α: {corrected_alpha:.6f}")
        print(f"   Significant after correction: {comparisons_df['significant_bonferroni'].sum()}/{n_comparisons}")
        
        return comparisons_df
    
    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size"""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"
    
    def generate_statistical_report(self, output_file: str = "statistical_analysis_report.md"):
        """Generate comprehensive statistical report"""
        
        report = []
        report.append("# Statistical Analysis Report\n\n")
        
        # Pairwise comparisons
        if 'pairwise_comparisons' in self.results:
            report.append("## Pairwise Algorithm Comparisons\n\n")
            df = self.results['pairwise_comparisons']
            
            # Significant comparisons
            sig = df[df['significant']]
            report.append(f"### Significant Differences (α={self.alpha})\n\n")
            
            if not sig.empty:
                for _, row in sig.iterrows():
                    report.append(
                        f"- **{row['algorithm_1']} vs {row['algorithm_2']}**: "
                        f"p={row['p_value']:.4f}, d={row['cohens_d']:.2f} ({row['effect_interpretation']})\n"
                    )
            else:
                report.append("No significant differences found.\n")
            
            report.append("\n")
        
        # Confidence intervals
        if 'confidence_intervals' in self.results:
            report.append("## Confidence Intervals (95%)\n\n")
            df = self.results['confidence_intervals']
            
            report.append("| Algorithm | Mean | 95% CI (Bootstrap) |\n")
            report.append("|-----------|------|--------------------|\n")
            
            for _, row in df.iterrows():
                report.append(
                    f"| {row['algorithm']} | {row['mean']:.2f} | "
                    f"[{row['ci_lower_bootstrap']:.2f}, {row['ci_upper_bootstrap']:.2f}] |\n"
                )
            
            report.append("\n")
        
        # Win-Tie-Loss
        if 'win_tie_loss' in self.results:
            report.append("## Win-Tie-Loss Records\n\n")
            df = self.results['win_tie_loss']
            
            total_wins = df.groupby('algorithm')['wins'].sum().sort_values(ascending=False)
            
            report.append("### Total Wins\n\n")
            for algo, wins in total_wins.items():
                report.append(f"- {algo}: {wins} wins\n")
            
            report.append("\n")
        
        # Performance profiles
        if 'performance_profiles' in self.results:
            report.append("## Performance Profiles\n\n")
            df = self.results['performance_profiles']
            
            pivot = df.pivot(index='algorithm', columns='tau', values='pct_instances_within_tau')
            report.append(pivot.to_markdown())
            report.append("\n\n")
        
        # Save report
        with open(output_file, 'w') as f:
            f.writelines(report)
        
        print(f"\n✅ Statistical report saved: {output_file}")
        
        return "".join(report)
    
    def save_all_results(self, output_dir: str = "statistical_results"):
        """Save all statistical results to CSV files"""
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        for name, df in self.results.items():
            if isinstance(df, pd.DataFrame):
                filename = output_path / f"{name}.csv"
                df.to_csv(filename, index=False)
                print(f"✓ Saved: {filename}")


def analyze_experimental_results(results_csv: str = "experimental_results/all_results.csv"):
    """
    Complete statistical analysis of experimental results
    
    Args:
        results_csv: Path to experimental results CSV
    """
    print("=" * 70)
    print("STATISTICAL ANALYSIS")
    print("=" * 70)
    
    # Load results
    df = pd.DataFrame(pd.read_csv(results_csv))
    print(f"\nLoaded {len(df)} results from {results_csv}")
    
    # Initialize analyzer
    analyzer = StatisticalAnalyzer(df, alpha=0.05)
    
    # Run analyses
    print("\n" + "=" * 70)
    print("1. Pairwise Comparisons")
    print("=" * 70)
    comparisons = analyzer.pairwise_algorithm_comparison(metric='cost')
    comparisons_corrected = analyzer.bonferroni_correction(comparisons)
    
    print("\n" + "=" * 70)
    print("2. Confidence Intervals")
    print("=" * 70)
    ci = analyzer.compute_confidence_intervals(metric='cost')
    
    print("\n" + "=" * 70)
    print("3. Win-Tie-Loss Analysis")
    print("=" * 70)
    wtl = analyzer.win_tie_loss_analysis(metric='cost')
    
    print("\n" + "=" * 70)
    print("4. Performance Profiles")
    print("=" * 70)
    profiles = analyzer.performance_profiles(metric='gap_from_classical')
    
    # Generate report
    print("\n" + "=" * 70)
    print("5. Generate Report")
    print("=" * 70)
    analyzer.generate_statistical_report("statistical_analysis_report.md")
    
    # Save all results
    analyzer.save_all_results("statistical_results")
    
    print("\n✅ Statistical analysis complete!")
    
    return analyzer


if __name__ == "__main__":
    # Example: Analyze experimental results
    # analyzer = analyze_experimental_results("experimental_results/all_results.csv")
    
    print("Statistical analysis module loaded.")
    print("Usage: analyzer = analyze_experimental_results('path/to/results.csv')")
