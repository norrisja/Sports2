

def ML_implied_prob(ml):
    """ Given a money line, returns an implied probability. """

    if not isinstance(ml, int):
        ml = int(ml)

    if ml >= 100:
        impl_prob = (100 / (ml + 100)) # x100 to make a percent not decimal
    elif ml <= -100:
        impl_prob = (abs(ml) / (abs(ml) + 100))

    return impl_prob


def spread_implied_prob(spread):
    ''' Given a spread, will find the implied probability. '''
    if spread in ['PK', 'Pick']:
        spread = 0

    impl_prob = -0.0303 * float(spread) + 0.5 # https://medium.com/the-intelligent-sports-wagerer/what-point-spreads-can-teach-you-about-implied-win-probabilities-a8bb3623d2c5
    #### TODO create my own formula by regressing spread against win percentage specific to each sport
    #### TODO make sure that this formula works for all sports, it was originally made for football

    impl_prob = max(min(impl_prob, .9999), 0.0001)

    return impl_prob

def flip_sign(number):
    if number == 'PK':
        return 'PK'
    elif number > 0:
        return -number
    else:
        return abs(number)

def spread_from_power_ratings(power_ratings_df, home_team, away_team):
    """ Takes a dataframe containing power ratings and takes two teams to generate a spread for the matchup. """

    power_ratings_df[['power_rating']].sort_values('power_rating')

    # Calculates the spread assuming team1 is home
    spread = power_ratings_df.at[home_team, 'power_rating'] - power_ratings_df.at[away_team, 'power_rating'] + 2.1 # minus 2.1 for homefield advantage; want to make this dyanamic in the future for different stadiums

    spread = round((spread * 2), 0) / 2  #'PK' if round((spread * 2), 0) / 2 == 0 else round((spread * 2), 0) / 2 # Round to the nearest .5; PK for even spread

    # if the spread we're left with is positive, the home team is favored, so we should flip the sign
    home_spread = flip_sign(spread)
    away_spread = spread
    # elif spread < 0:
    #     home_spread = flip_sign(spread)
    #     away_spread = spread

    return {home_team: home_spread,
            away_team: away_spread}
