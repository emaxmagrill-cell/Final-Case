"""Fantasy scoring calculations module"""

import pandas as pd
from src.config import FANTASY_SCORING


def calculate_player_fantasy_points(player_stats: dict) -> float:
    """
    Calculate fantasy points for a single player based on their stats.
    
    Args:
        player_stats: Dictionary containing player statistics
        (pass_td, pass_int, pass_yards, rush_td, rush_yards, rec_td, rec_yards, reception, fumble_lost)
    
    Returns:
        Total fantasy points as float
    """
    points = 0.0
    
    # Passing stats
    points += player_stats.get('pass_td', 0) * FANTASY_SCORING['pass_td']
    points += player_stats.get('pass_int', 0) * FANTASY_SCORING['pass_int']
    points += player_stats.get('pass_yards', 0) * FANTASY_SCORING['pass_yards']
    
    # Rushing stats
    points += player_stats.get('rush_td', 0) * FANTASY_SCORING['rush_td']
    points += player_stats.get('rush_yards', 0) * FANTASY_SCORING['rush_yards']
    
    # Receiving stats
    points += player_stats.get('rec_td', 0) * FANTASY_SCORING['rec_td']
    points += player_stats.get('rec_yards', 0) * FANTASY_SCORING['rec_yards']
    points += player_stats.get('reception', 0) * FANTASY_SCORING['reception']
    
    # Fumbles
    points += player_stats.get('fumble_lost', 0) * FANTASY_SCORING['fumble_lost']
    
    return round(points, 2)


def calculate_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate fantasy points for all players and create a leaderboard.
    
    Args:
        df: DataFrame with player statistics
    
    Returns:
        Sorted leaderboard DataFrame with fantasy points
    """
    if df.empty:
        return pd.DataFrame()
    
    leaderboard = df.copy()
    
    # Define columns we need for scoring, fill missing ones with 0
    scoring_columns = [
        'pass_td', 'pass_int', 'pass_yards',
        'rush_td', 'rush_yards',
        'rec_td', 'rec_yards', 'reception',
        'fumble_lost'
    ]
    
    for col in scoring_columns:
        if col not in leaderboard.columns:
            leaderboard[col] = 0
        leaderboard[col] = leaderboard[col].fillna(0)
    
    # Calculate fantasy points for each player
    leaderboard['fantasy_points'] = leaderboard.apply(
        lambda row: calculate_player_fantasy_points(row.to_dict()),
        axis=1
    )
    
    # Sort by fantasy points descending
    leaderboard = leaderboard.sort_values('fantasy_points', ascending=False).reset_index(drop=True)
    leaderboard['rank'] = range(1, len(leaderboard) + 1)
    
    return leaderboard


def get_top_players(leaderboard: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Get top N players from leaderboard.
    
    Args:
        leaderboard: Full leaderboard DataFrame
        n: Number of top players to return
    
    Returns:
        Top N players
    """
    return leaderboard.head(n)


def filter_by_position(leaderboard: pd.DataFrame, position: str) -> pd.DataFrame:
    """
    Filter leaderboard by player position.
    
    Args:
        leaderboard: Full leaderboard DataFrame
        position: Player position (QB, RB, WR/TE, etc.)
    
    Returns:
        Filtered leaderboard
    """
    if 'position' not in leaderboard.columns:
        return leaderboard
    
    # Normalize position string (strip whitespace, handle case)
    position = position.strip()
    
    # Filter by exact position match
    filtered = leaderboard[leaderboard['position'] == position].copy().reset_index(drop=True)
    
    return filtered
