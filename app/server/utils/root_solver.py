def find_monotonic_increasing_bounds(root_func, initial_guess):
    """
    finds bounds for the root of a function given an initial_guess
    """
    bound_expansion_rate = 1.2

    x_upper = x_lower = initial_guess
    y_upper = y_lower = root_func(initial_guess)

    # Find a lower bound guess that is results in a conversion less than the desired amount
    print("Finding lower bound")
    lower_iterations = 0
    while y_lower >= 0:
        print(f'Iteration: {lower_iterations}')
        lower_iterations += 1
        x_lower = x_lower / bound_expansion_rate
        y_lower = root_func(x_lower)

    # Find an bound guess that is results in a conversion greater than the desired amount
    print("Finding upper bound")
    upper_iterations = 0
    while y_upper <= 0:
        print(f'Iteration: {upper_iterations}')
        upper_iterations += 1
        x_upper = x_upper * bound_expansion_rate

        y_upper = root_func(x_upper)

    return x_lower, y_lower, x_upper, y_upper


def secant_method(root_func,
                   x0, y0,
                   x1, y1,
                   max_error, max_iterations=6):
    xs = [x0, x1] + max_iterations * [None]  # allocate x's vector
    ys = [y0, y1] + max_iterations * [None]  # allocate y's vector

    xi1 = x1
    yi1 = y1

    for i, x in enumerate(xs):

        print(f'Iteration: {i}')

        if abs(yi1) < max_error:
            continue

        if i < max_iterations:
            xi = xs[i]
            yi = ys[i]
            xi1 = xs[i + 1]
            yi1 = ys[i + 1] or root_func(xi1)

            xi2 = xi1 - yi1 * (xi1 - xi) / (yi1 - yi)

            xs[i + 2] = xi2 if xi2 >= 0 else 0

    return xi1, yi1

def false_position_method(root_func,
                          x_lower, y_lower,
                          x_upper, y_upper,
                          max_error, max_iterations=6):

    new_x = x_upper
    new_y = y_upper

    iterations = 0
    while abs(new_y) > max_error and iterations < max_iterations:

        print(f'Iteration: {iterations}')
        print(f'Error: {abs(new_y)}')
        iterations += 1

        gradient = (y_upper - y_lower) / (x_upper - x_lower)

        new_x = -1 * y_upper / gradient + x_upper
        new_y = root_func(new_x)

        if new_y > 0:
            x_upper = new_x
            y_upper = new_y
        else:
            x_lower = new_x
            y_lower = new_y

    return new_x, new_y


def bisection_method(root_func, x_lower, x_upper, max_error, max_iterations=6):
    new_x = (x_upper + x_lower) / 2
    new_y = root_func(new_x)

    iterations = 0
    while abs(new_y) > max_error and iterations < max_iterations:

        print(f'Iteration: {iterations}')
        print(f'Error: {abs(new_y)}')
        iterations += 1

        if new_y > 0:
            x_upper = new_x
        else:
            x_lower = new_x

        new_x = (x_upper + x_lower) / 2
        new_y = root_func(new_x)

    return new_x, new_y
