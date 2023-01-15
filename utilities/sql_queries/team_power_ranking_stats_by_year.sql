WITH _stats as (
	SELECT 
	map.name,
	ntss.*
	FROM nfl_team_season_stats ntss, abbr_map map
	WHERE map.abbreviation = ntss.abbreviation
)
SELECT 
_stats.*, 
gen.games_played,
gen.wins,
gen.losses,
gen.win_percentage,
gen.points_for,
gen.points_against,
gen.points_difference,
gen.margin_of_victory,
gen.strength_of_schedule,
gen.simple_rating_system,
gen.offensive_simple_rating_system,
gen.defensive_simple_rating_system

FROM _stats, nfl_team_season_gen gen
WHERE _stats.name = gen.name
AND _stats.year = gen.year
AND _stats.year in {}
