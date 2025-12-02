"""Data fetching module for NFL player statistics using nflverse API"""

import pandas as pd
import nflreadpy as nfl
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_player_stats(season: int, week: int = None) -> pd.DataFrame:
    """
    Fetch player statistics from nflverse API using nflreadpy.
    
    Args:
        season: NFL season year
        week: Specific week (1-18), or None for all weeks
    
    Returns:
        DataFrame with player statistics (converted to pandas)
    """
    try:
        logger.info(f"Fetching player stats for season {season}, week {week}")
        
        # Fetch play-by-play data using nflreadpy
        # load_pbp() returns a Polars DataFrame, convert to pandas
        pbp = nfl.load_pbp(seasons=[season])
        
        if pbp is None or len(pbp) == 0:
            logger.warning(f"No data available for season {season}")
            return pd.DataFrame()
        
        # Convert Polars DataFrame to pandas
        df = pbp.to_pandas()
        
        # CRITICAL: Verify season filter is working
        if 'season' in df.columns:
            # Ensure all rows are from the requested season
            df = df[df['season'] == season].copy()
            logger.info(f"After season filter: {len(df)} plays from season {season}")
        else:
            logger.warning("'season' column not found in data - season filtering may not work correctly")
        
        # Filter by week if specified
        if week:
            if 'week' in df.columns:
                df = df[df['week'] == week].copy()
                logger.info(f"After week filter: {len(df)} plays from week {week}")
            else:
                logger.warning("'week' column not found in data")
        
        # Log data validation
        if not df.empty:
            if 'season' in df.columns:
                unique_seasons = df['season'].unique()
                logger.info(f"Data contains seasons: {unique_seasons}")
                # CRITICAL: Verify ALL data is from requested season
                if len(unique_seasons) > 1 or (len(unique_seasons) == 1 and unique_seasons[0] != season):
                    logger.error(f"ERROR: Data contains wrong seasons! Expected {season}, got {unique_seasons}")
                    # Force filter again to be safe
                    df = df[df['season'] == season].copy()
                    logger.info(f"Re-filtered to season {season}: {len(df)} plays")
                else:
                    logger.info(f"✓ Verified: All {len(df)} plays are from season {season}")
            if 'week' in df.columns:
                unique_weeks = sorted(df['week'].unique())
                logger.info(f"Data contains weeks: {unique_weeks}")
                if week:
                    # Verify week filter worked
                    if len(unique_weeks) > 1 or (len(unique_weeks) == 1 and unique_weeks[0] != week):
                        logger.error(f"ERROR: Data contains wrong weeks! Expected {week}, got {unique_weeks}")
                    else:
                        logger.info(f"✓ Verified: All plays are from week {week}")
        
        return df
    
    except Exception as e:
        logger.error(f"Error fetching player stats: {e}")
        return pd.DataFrame()


def fetch_player_details(season: int = 2024) -> pd.DataFrame:
    """
    Fetch player roster information.
    
    Args:
        season: NFL season year (default: 2024)
    
    Returns:
        DataFrame with player details (converted to pandas)
    """
    try:
        logger.info(f"Fetching player roster for season {season}")
        # load_rosters returns roster data for specified seasons
        rosters = nfl.load_rosters(seasons=[season])
        if rosters is not None and len(rosters) > 0:
            return rosters.to_pandas()
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching player roster: {e}")
        return pd.DataFrame()


def get_available_seasons() -> list:
    """
    Get list of available seasons from nflverse data.
    
    Returns:
        List of season years available
    """
    try:
        # nflverse data typically spans from 1999 to current year
        current_year = datetime.now().year
        # Return available seasons, defaulting to a reasonable range
        available_seasons = list(range(1999, current_year + 1))
        logger.info(f"Available seasons: {available_seasons[0]}-{available_seasons[-1]}")
        return available_seasons
    except Exception as e:
        logger.error(f"Error getting available seasons: {e}")
        # Fallback to default range
        current_year = datetime.now().year
        return list(range(1999, current_year + 1))


def aggregate_player_stats(pbp_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate play-by-play data into player statistics.
    Handles nflreadpy data format with proper column handling.
    Combines passing and rushing stats for QBs.
    
    Args:
        pbp_df: Play-by-play DataFrame from nflreadpy
    
    Returns:
        Aggregated player statistics
    """
    try:
        if pbp_df.empty:
            logger.warning("Empty DataFrame provided to aggregate_player_stats")
            return pd.DataFrame()
        
        # Initialize a dictionary to store all player stats
        player_stats_dict = {}
        
        # Passing stats - QBs
        # Only count passing yards from actual pass attempts, not from rushing plays
        if 'passer_player_name' in pbp_df.columns:
            # Filter to only rows with a passer (actual pass attempts)
            passer_df = pbp_df[pbp_df['passer_player_name'].notna()].copy()
            if not passer_df.empty:
                # CRITICAL: Ensure we only count passing yards from pass plays
                # Filter out any rows where passing_yards might be incorrectly set on non-pass plays
                # Only use rows where there's actually a pass attempt
                
                # Additional safety: if play_type exists, filter to only pass plays
                if 'play_type' in passer_df.columns:
                    passer_df = passer_df[passer_df['play_type'].isin(['pass', 'qb_kneel', 'qb_spike'])].copy()
                    logger.info(f"After play_type filter for passes: {len(passer_df)} pass plays")
                
                # Ensure rushing_yards is 0 for pass plays (safety check)
                if 'rushing_yards' in passer_df.columns:
                    passer_df['rushing_yards'] = passer_df['rushing_yards'].fillna(0)
                    # Verify no rushing yards in pass plays
                    rush_yards_in_pass = passer_df['rushing_yards'].sum()
                    if rush_yards_in_pass > 0:
                        logger.warning(f"Found {rush_yards_in_pass} rushing yards in pass plays - this should be 0")
                
                passer_df['pass_touchdown'] = passer_df['pass_touchdown'].fillna(0)
                passer_df['interception'] = passer_df['interception'].fillna(0)
                # Only count passing_yards where it's actually a pass (not a rush)
                passer_df['passing_yards'] = passer_df['passing_yards'].fillna(0)
                
                passer_stats = passer_df.groupby('passer_player_name').agg({
                    'pass_touchdown': 'sum',
                    'interception': 'sum',
                    'passing_yards': 'sum',  # ONLY passing yards from pass attempts
                }).reset_index()
                
                for _, row in passer_stats.iterrows():
                    player_name = row['passer_player_name']
                    if player_name not in player_stats_dict:
                        player_stats_dict[player_name] = {
                            'player_name': player_name,
                            'position': 'QB',
                            'pass_td': 0, 'pass_int': 0, 'pass_yards': 0,
                            'rush_td': 0, 'rush_yards': 0,
                            'rec_td': 0, 'rec_yards': 0, 'reception': 0
                        }
                    # Only set passing stats - don't add to existing, just set (in case player appears multiple times)
                    player_stats_dict[player_name]['pass_td'] = row['pass_touchdown']
                    player_stats_dict[player_name]['pass_int'] = row['interception']
                    # Ensure passing_yards is only from passing plays, not total yards
                    player_stats_dict[player_name]['pass_yards'] = row['passing_yards']
                    player_stats_dict[player_name]['position'] = 'QB'  # Set as QB if they pass
                
                logger.info(f"Found {len(passer_stats)} players with passing stats")
        
        # Rushing stats - Can include QBs, RBs, etc.
        # Only count rushing yards from actual rush attempts, separate from passing yards
        if 'rusher_player_name' in pbp_df.columns:
            # Filter to only rows with a rusher (actual rush attempts)
            rush_df = pbp_df[pbp_df['rusher_player_name'].notna()].copy()
            if not rush_df.empty:
                # CRITICAL: Ensure we only count rushing yards from rush plays
                # Additional safety: if play_type exists, filter to only rush plays
                if 'play_type' in rush_df.columns:
                    rush_df = rush_df[rush_df['play_type'].isin(['run', 'qb_kneel'])].copy()
                    logger.info(f"After play_type filter for rushes: {len(rush_df)} rush plays")
                
                # Ensure passing_yards is 0 for rush plays (safety check)
                if 'passing_yards' in rush_df.columns:
                    rush_df['passing_yards'] = rush_df['passing_yards'].fillna(0)
                    # Verify no passing yards in rush plays
                    pass_yards_in_rush = rush_df['passing_yards'].sum()
                    if pass_yards_in_rush > 0:
                        logger.warning(f"Found {pass_yards_in_rush} passing yards in rush plays - this should be 0")
                
                # Fill NaN values with 0 before aggregation
                rush_df['rushing_yards'] = rush_df['rushing_yards'].fillna(0)
                rush_df['rush_touchdown'] = rush_df['rush_touchdown'].fillna(0)
                
                rusher_stats = rush_df.groupby('rusher_player_name').agg({
                    'rushing_yards': 'sum',  # ONLY rushing yards from rush attempts
                    'rush_touchdown': 'sum',
                }).reset_index()
                
                for _, row in rusher_stats.iterrows():
                    player_name = row['rusher_player_name']
                    if player_name not in player_stats_dict:
                        player_stats_dict[player_name] = {
                            'player_name': player_name,
                            'position': 'RB',  # Default to RB if no passing stats yet
                            'pass_td': 0, 'pass_int': 0, 'pass_yards': 0,
                            'rush_td': 0, 'rush_yards': 0,
                            'rec_td': 0, 'rec_yards': 0, 'reception': 0
                        }
                    # Only set/add rushing stats - don't touch passing stats
                    # If player already exists (e.g., as a QB), add rushing stats but keep pass_yards separate
                    player_stats_dict[player_name]['rush_td'] = row['rush_touchdown']
                    player_stats_dict[player_name]['rush_yards'] = row['rushing_yards']
                    # IMPORTANT: If they already have passing stats (are a QB), keep position as QB
                    # Don't change QB to RB just because they also rush
                    # Only set to RB if they don't have passing stats
                    if player_stats_dict[player_name].get('pass_yards', 0) == 0 and player_stats_dict[player_name].get('pass_td', 0) == 0:
                        # Only set to RB if they have no passing stats
                        if player_stats_dict[player_name]['position'] != 'QB':
                            player_stats_dict[player_name]['position'] = 'RB'
                
                logger.info(f"Found {len(rusher_stats)} players with rushing stats")
        
        # Receiving stats - WRs/TEs
        if 'receiver_player_name' in pbp_df.columns:
            rec_df = pbp_df[pbp_df['receiver_player_name'].notna()].copy()
            if not rec_df.empty:
                # Fill NaN values with 0 before aggregation
                rec_df['receiving_yards'] = rec_df['receiving_yards'].fillna(0)
                rec_df['touchdown'] = rec_df['touchdown'].fillna(0)
                # complete_pass is a binary indicator (0 or 1) - represents receptions
                # Each reception = 1 point in PPR scoring
                rec_df['complete_pass'] = rec_df['complete_pass'].fillna(0)
                
                receiver_stats = rec_df.groupby('receiver_player_name').agg({
                    'complete_pass': 'sum',  # Total receptions (1 point each in PPR)
                    'receiving_yards': 'sum',
                    'touchdown': 'sum',  # Receiving TDs (from the general touchdown field)
                }).reset_index()
                
                for _, row in receiver_stats.iterrows():
                    player_name = row['receiver_player_name']
                    if player_name not in player_stats_dict:
                        player_stats_dict[player_name] = {
                            'player_name': player_name,
                            'position': 'WR/TE',  # Default to WR/TE if no other stats
                            'pass_td': 0, 'pass_int': 0, 'pass_yards': 0,
                            'rush_td': 0, 'rush_yards': 0,
                            'rec_td': 0, 'rec_yards': 0,
                            'reception': 0  # Total receptions (1 point each)
                        }
                    # Store total receptions - each reception = 1 point in PPR scoring
                    player_stats_dict[player_name]['reception'] = int(row['complete_pass'])
                    player_stats_dict[player_name]['rec_yards'] = row['receiving_yards']
                    player_stats_dict[player_name]['rec_td'] = row['touchdown']
                    # Only set position to WR/TE if they don't have passing or rushing stats
                    if (player_stats_dict[player_name]['position'] != 'QB' and 
                        player_stats_dict[player_name]['position'] != 'RB'):
                        player_stats_dict[player_name]['position'] = 'WR/TE'
                
                logger.info(f"Found {len(receiver_stats)} players with receiving stats")
        
        # Convert dictionary to DataFrame
        if player_stats_dict:
            all_stats = pd.DataFrame(list(player_stats_dict.values()))
            all_stats = all_stats.fillna(0)
            logger.info(f"Aggregated stats for {len(all_stats)} total players")
            logger.info(f"QBs with rushing stats: {len(all_stats[(all_stats['position'] == 'QB') & (all_stats['rush_yards'] > 0)])}")
            
            # Validation: Ensure passing yards and rushing yards are separate
            # Check a sample QB to verify stats are correctly separated
            qb_with_rush = all_stats[(all_stats['position'] == 'QB') & (all_stats['rush_yards'] > 0)]
            if not qb_with_rush.empty:
                sample_qb = qb_with_rush.iloc[0]
                logger.info(f"Sample QB stats - {sample_qb['player_name']}: Pass Yards={sample_qb['pass_yards']:.0f}, Rush Yards={sample_qb['rush_yards']:.0f} (separate)")
            
            # Additional validation: Check for any players with suspiciously high total yards
            # (pass_yards + rush_yards should not equal total_yards if they're being mixed)
            all_stats['total_yards_check'] = all_stats['pass_yards'] + all_stats['rush_yards']
            logger.info(f"Validation: Stats aggregated from {len(pbp_df)} total plays")
            if 'season' in pbp_df.columns:
                logger.info(f"Data season range: {pbp_df['season'].min()} to {pbp_df['season'].max()}")
            if 'week' in pbp_df.columns:
                logger.info(f"Data week range: {pbp_df['week'].min()} to {pbp_df['week'].max()}")
            
            return all_stats
        else:
            logger.warning("No player stats could be aggregated from the data")
            return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Error aggregating player stats: {e}", exc_info=True)
        return pd.DataFrame()


def fetch_team_stats(season: int, stat_type: str = 'game') -> pd.DataFrame:
    """
    Fetch team-level statistics using nflreadpy.
    
    Args:
        season: NFL season year
        stat_type: Type of stats ('game' or 'season')
    
    Returns:
        Team statistics DataFrame (converted to pandas)
    """
    try:
        logger.info(f"Fetching team {stat_type} stats for season {season}")
        
        if stat_type == 'season':
            # Get season-level stats
            team_stats = nfl.load_team_stats(seasons=[season], stat_type='season')
        else:
            # Get game-level stats (default)
            team_stats = nfl.load_team_stats(seasons=[season], stat_type='game')
        
        if team_stats is not None and len(team_stats) > 0:
            return team_stats.to_pandas()
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching team stats: {e}")
        return pd.DataFrame()


def fetch_schedule(season: int) -> pd.DataFrame:
    """
    Fetch NFL game schedule using nflreadpy.
    
    Args:
        season: NFL season year
    
    Returns:
        Schedule DataFrame with game information (converted to pandas)
    """
    try:
        logger.info(f"Fetching schedule for season {season}")
        
        schedule = nfl.load_schedules(seasons=[season])
        
        if schedule is not None and len(schedule) > 0:
            return schedule.to_pandas()
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching schedule: {e}")
        return pd.DataFrame()


def fetch_player_ids() -> pd.DataFrame:
    """
    Fetch player ID mapping from nflverse.
    Useful for cross-referencing with other data sources.
    
    Returns:
        Player ID mapping DataFrame (converted to pandas)
    """
    try:
        logger.info("Fetching player ID mappings")
        
        player_ids = nfl.load_ff_playerids()
        
        if player_ids is not None and len(player_ids) > 0:
            return player_ids.to_pandas()
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching player IDs: {e}")
        return pd.DataFrame()


def get_nflreadpy_config() -> dict:
    """
    Get current nflreadpy configuration.
    
    Returns:
        Dictionary with nflreadpy settings
    """
    try:
        from nflreadpy.config import get_config
        config = get_config()
        return {
            'cache_mode': getattr(config, 'cache_mode', 'unknown'),
            'cache_duration': getattr(config, 'cache_duration', 'unknown'),
            'timeout': getattr(config, 'timeout', 'unknown'),
        }
    except Exception as e:
        logger.warning(f"Could not retrieve nflreadpy config: {e}")
        return {}
