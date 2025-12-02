"""
Flask-based Fantasy Football Leaderboard Web Application
Designed for deployment on Azure App Service
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import json
from datetime import datetime
import logging
import os
from io import BytesIO

from src.config import APP_TITLE, APP_DESCRIPTION, CURRENT_SEASON, FANTASY_SCORING
from src.data_fetcher import (
    fetch_player_stats, fetch_player_details, get_available_seasons,
    aggregate_player_stats, fetch_team_stats, fetch_schedule, 
    fetch_player_ids, get_nflreadpy_config
)
from src.scoring import calculate_leaderboard, get_top_players, filter_by_position

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Initialize Flask app
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache for data
_cache = {
    'leaderboard': None,
    'season': None,
    'week': None,
    'timestamp': None
}

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html', 
                         title=APP_TITLE,
                         description=APP_DESCRIPTION,
                         seasons=get_available_seasons())


@app.route('/api/leaderboard', methods=['GET'])
def api_leaderboard():
    """
    API endpoint to fetch leaderboard data
    Query parameters:
        - season: int (default: current season)
        - week: int or None (default: all weeks)
        - top_n: int (default: 25)
        - position: str (comma-separated: QB, RB, WR/TE)
    """
    try:
        season = request.args.get('season', CURRENT_SEASON, type=int)
        week = request.args.get('week', None)
        if week:
            week = int(week)
        top_n = request.args.get('top_n', 25, type=int)
        position_filter = request.args.get('position', '')
        
        logger.info(f"Fetching leaderboard: season={season}, week={week}, top_n={top_n}")
        
        # Fetch and process data
        pbp_df = fetch_player_stats(season, week)
        if pbp_df.empty:
            return jsonify({'error': 'No data available for selected parameters'}), 404
        
        # CRITICAL: Verify data is from correct season
        if 'season' in pbp_df.columns:
            unique_seasons = pbp_df['season'].unique()
            if len(unique_seasons) > 1 or (len(unique_seasons) == 1 and unique_seasons[0] != season):
                logger.error(f"Data validation failed: Expected season {season}, got {unique_seasons}")
                return jsonify({'error': f'Data validation error: Stats not from season {season}'}), 500
            logger.info(f"✓ Data validated: All stats from season {season}")
        
        player_stats = aggregate_player_stats(pbp_df)
        if player_stats.empty:
            return jsonify({'error': 'No player statistics available'}), 404
        
        leaderboard = calculate_leaderboard(player_stats)
        
        # Log position distribution before filtering
        if 'position' in leaderboard.columns:
            position_counts = leaderboard['position'].value_counts()
            logger.info(f"Position distribution before filtering: {position_counts.to_dict()}")
        
        # Apply position filter
        if position_filter:
            positions = [p.strip() for p in position_filter.split(',')]
            logger.info(f"Filtering by positions: {positions}")
            filtered_boards = []
            for pos in positions:
                filtered = filter_by_position(leaderboard, pos)
                logger.info(f"Position '{pos}': found {len(filtered)} players")
                if not filtered.empty:
                    filtered_boards.append(filtered)
            
            if filtered_boards:
                leaderboard = pd.concat(filtered_boards, ignore_index=True)
                leaderboard = leaderboard.sort_values('fantasy_points', ascending=False).reset_index(drop=True)
                logger.info(f"After filtering: {len(leaderboard)} players total")
            else:
                logger.warning(f"No players found for positions: {positions}")
                leaderboard = pd.DataFrame()  # Return empty if no matches
        
        # Get top players
        top_leaderboard = leaderboard.head(top_n)
        
        # Prepare response
        # Verify season in metadata
        verified_season = season
        if 'season' in pbp_df.columns:
            verified_season = int(pbp_df['season'].iloc[0]) if not pbp_df.empty else season
        
        response = {
            'success': True,
            'metadata': {
                'season': verified_season,
                'week': week,
                'total_players': len(leaderboard),
                'top_score': float(leaderboard['fantasy_points'].iloc[0]) if not leaderboard.empty else 0,
                'average_score': float(leaderboard['fantasy_points'].mean()) if not leaderboard.empty else 0,
                'timestamp': datetime.now().isoformat(),
                'data_verified': True,  # Confirms stats are from the selected season
                'data_source': f'nflreadpy season {verified_season}' + (f' week {week}' if week else ' (all weeks)')
            },
            'leaderboard': top_leaderboard.to_dict('records'),
            'full_leaderboard_count': len(leaderboard)
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats/<int:season>/<int:week>')
def api_player_stats(season, week):
    """
    API endpoint to get individual player statistics
    """
    try:
        pbp_df = fetch_player_stats(season, week)
        if pbp_df.empty:
            return jsonify({'error': 'No data available'}), 404
        
        player_stats = aggregate_player_stats(pbp_df)
        leaderboard = calculate_leaderboard(player_stats)
        
        return jsonify({
            'success': True,
            'stats': leaderboard.to_dict('records')
        })
    
    except Exception as e:
        logger.error(f"Error fetching player stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/download-csv', methods=['GET'])
def api_download_csv():
    """
    Download leaderboard as CSV
    """
    try:
        season = request.args.get('season', CURRENT_SEASON, type=int)
        week = request.args.get('week', None)
        if week:
            week = int(week)
        
        pbp_df = fetch_player_stats(season, week)
        if pbp_df.empty:
            return jsonify({'error': 'No data available'}), 404
        
        player_stats = aggregate_player_stats(pbp_df)
        leaderboard = calculate_leaderboard(player_stats)
        
        # Create CSV in memory
        csv_buffer = BytesIO()
        leaderboard.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        filename = f"fantasy_leaderboard_{season}_w{week or 'all'}.csv"
        
        return send_file(
            csv_buffer,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Error downloading CSV: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/seasons', methods=['GET'])
def api_seasons():
    """Get available seasons"""
    return jsonify({
        'seasons': get_available_seasons(),
        'current': CURRENT_SEASON
    })


@app.route('/api/scoring', methods=['GET'])
def api_scoring():
    """Get scoring rules"""
    return jsonify({
        'scoring_system': 'PPR (Points Per Reception)',
        'rules': FANTASY_SCORING
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for Azure monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'app': APP_TITLE,
        'nflreadpy_config': get_nflreadpy_config()
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.route('/api/team-stats', methods=['GET'])
def api_team_stats():
    """
    Get team-level statistics from nflreadpy
    Query parameters:
        - season: int (default: current season)
        - stat_type: str (default: 'game', options: 'game' or 'season')
    """
    try:
        season = request.args.get('season', CURRENT_SEASON, type=int)
        stat_type = request.args.get('stat_type', 'game', type=str)
        
        logger.info(f"Fetching team stats: season={season}, stat_type={stat_type}")
        
        team_stats = fetch_team_stats(season, stat_type)
        if team_stats.empty:
            return jsonify({'error': 'No team stats available'}), 404
        
        return jsonify({
            'success': True,
            'season': season,
            'stat_type': stat_type,
            'stats': team_stats.to_dict('records')
        })
    
    except Exception as e:
        logger.error(f"Error fetching team stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/schedule', methods=['GET'])
def api_schedule():
    """
    Get NFL game schedule from nflreadpy
    Query parameters:
        - season: int (default: current season)
    """
    try:
        season = request.args.get('season', CURRENT_SEASON, type=int)
        
        logger.info(f"Fetching schedule for season {season}")
        
        schedule = fetch_schedule(season)
        if schedule.empty:
            return jsonify({'error': 'No schedule available'}), 404
        
        return jsonify({
            'success': True,
            'season': season,
            'games_count': len(schedule),
            'schedule': schedule.to_dict('records')
        })
    
    except Exception as e:
        logger.error(f"Error fetching schedule: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/player-ids', methods=['GET'])
def api_player_ids():
    """
    Get player ID mappings for cross-referencing
    """
    try:
        logger.info("Fetching player ID mappings")
        
        player_ids = fetch_player_ids()
        if player_ids.empty:
            return jsonify({'error': 'No player IDs available'}), 404
        
        return jsonify({
            'success': True,
            'total_players': len(player_ids),
            'player_ids': player_ids.head(100).to_dict('records')  # Return first 100 for API response
        })
    
    except Exception as e:
        logger.error(f"Error fetching player IDs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/nflreadpy-status', methods=['GET'])
def nflreadpy_status():
    """
    Get nflreadpy configuration and status information
    """
    try:
        config = get_nflreadpy_config()
        return jsonify({
            'status': 'active',
            'version': '0.11.0',  # Current nflreadpy version from requirements
            'configuration': config,
            'data_sources': [
                'play-by-play',
                'player statistics',
                'team statistics',
                'schedules',
                'rosters',
                'player IDs',
                'fantasy football data'
            ]
        })
    
    except Exception as e:
        logger.error(f"Error getting nflreadpy status: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 0))  # 0 = auto-select available port
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
