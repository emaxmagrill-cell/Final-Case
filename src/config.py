"""Configuration for Fantasy Football Leaderboard App"""

# Fantasy Scoring Settings (PPR - Points Per Reception)
FANTASY_SCORING = {
    "pass_td": 6,           # Points per passing TD
    "pass_int": -2,         # Points per interception thrown
    "pass_yards": 0.04,     # Points per passing yard (1 point per 25 yards)
    "rush_td": 6,           # Points per rushing TD
    "rush_yards": 0.1,      # Points per rushing yard (1 point per 10 yards)
    "rec_td": 6,            # Points per receiving TD
    "rec_yards": 0.1,       # Points per receiving yard (1 point per 10 yards)
    "reception": 1,         # Points per reception (PPR)
    "fumble_lost": -2,      # Points per fumble lost
}

# App Configuration
APP_TITLE = "🏈 Fantasy Football Leaderboard"
APP_DESCRIPTION = "Real-time fantasy football scoring powered by NFL data"

# Season settings
CURRENT_SEASON = 2024
WEEKS_IN_SEASON = 18
