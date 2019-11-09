# See http://meissereconomics.com/assets/abfe-lesson5-bancor.pdf


def bonding_curve_reserve_to_tokens(initial_supply, initial_reserve, reserve_ratio_ppm, reserve):
    reserve_ratio = reserve_ratio_ppm/1e6

    return initial_supply*((1 + reserve / initial_reserve) ** reserve_ratio - 1)


def bonding_curve_tokens_to_reserve(initial_supply, initial_reserve, reserve_ratio_ppm, tokens):
    reserve_ratio = reserve_ratio_ppm/1e6

    return initial_reserve*((1 + tokens / initial_supply) ** (1 / reserve_ratio) - 1)


def bonding_curve_token1_to_token2(t1_supply, t2_supply,
                                   converter1_reserve, converter2_reserve,
                                   converter1_rr_ppm, converter2_rr_ppm,
                                   token1):

    intermediate_reserve = bonding_curve_tokens_to_reserve(
        t1_supply, converter1_reserve, converter1_rr_ppm, token1
    )

    return bonding_curve_reserve_to_tokens(t2_supply, converter2_reserve, converter2_rr_ppm, intermediate_reserve)

