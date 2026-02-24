import pandas as pd
import networkx as nx
from typing import List, Dict, Any
from datetime import datetime, timedelta

class MetricsEngine:
    def __init__(self):
        pass
        
    def calculate_bus_factor(self, commits: List[Dict[str, Any]]) -> dict:
        """
        Calculate the bus factor (minimum number of developers that hold >50% of the commits).
        """
        if not commits:
            return {"bus_factor": 0, "total_contributors": 0, "top_contributors": []}
            
        # Create a DataFrame
        df = pd.DataFrame(commits)
        
        # In a real scenario we'd use 'author' or user ID. Let's assume author is provided.
        if "author" not in df.columns:
            return {"bus_factor": 0, "total_contributors": 0, "top_contributors": []}
            
        author_counts = df['author'].value_counts()
        total_commits = len(commits)
        
        cumulative = 0
        bus_factor = 0
        top_contributors = []
        
        for author, count in author_counts.items():
            bus_factor += 1
            cumulative += count
            pct = (count / total_commits) * 100
            top_contributors.append({
                "author": author, 
                "commits": int(count),
                "ownership_pct": round(pct, 1)
            })
            if cumulative > total_commits * 0.5:
                break
                
        return {
            "bus_factor": bus_factor,
            "total_contributors": len(author_counts),
            "top_contributors": top_contributors
        }
    
    def calculate_activity_decay(self, commits: List[Dict[str, Any]]) -> dict:
        """
        Calculate if the project activity is decaying over the last 12 months.
        """
        if not commits:
            return {"decay_score": 1.0, "is_stagnant": True}
            
        df = pd.DataFrame(commits)
        if "date" not in df.columns:
            return {"decay_score": 1.0, "is_stagnant": True}
            
        df['date'] = pd.to_datetime(df['date'])
        
        # Group by month
        df['month'] = df['date'].dt.to_period('M')
        monthly_commits = df.groupby('month').size().reset_index(name='count')
        
        if len(monthly_commits) < 2:
            return {"decay_score": 0.0, "is_stagnant": False, "activity_trend": {}}
            
        # Monthly trend for chart
        trend_data = dict(zip(monthly_commits['month'].astype(str), monthly_commits['count']))
            
        # Simple trend using first vs second half comparison
        mid_idx = len(monthly_commits) // 2
        first_half_avg = monthly_commits.iloc[:mid_idx]['count'].mean()
        second_half_avg = monthly_commits.iloc[mid_idx:]['count'].mean()
        
        decay_score = 0.0
        if first_half_avg > 0:
            decay_ratio = second_half_avg / first_half_avg
            if decay_ratio < 0.5:
                decay_score = 0.8  # High decay
            elif decay_ratio < 0.8:
                decay_score = 0.5  # Moderate decay
                
        return {
            "decay_score": decay_score,
            "is_stagnant": decay_score >= 0.8,
            "activity_trend": trend_data
        }
