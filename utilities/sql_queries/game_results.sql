
SELECT
season
, week
, posteam
, defteam
, home_team
, away_team
, game_date
, away_score
, home_score
, result
, total
, spread_line

FROM weekly_stats
WHERE season in {}