import pytest
import math

from server.utils.root_solver import (
    find_monotonic_increasing_bounds,
    false_position_method,
    bisection_method,
    secant_method,
)


def mi_root_func(x):
    """
    A monotonically increasing root function, root at ~0.865
    """
    return x**3 - math.cos(x)


@pytest.mark.parametrize("root_func, guess, root", [
    (mi_root_func, 1, 0.865),
    (mi_root_func, 0.5, 0.865),
    (mi_root_func, 0.865, 0.865),
    (mi_root_func, 1.5, 0.865),
])
def test_find_monotonic_increasing_bounds(root_func, guess, root):
    x_lower, y_lower, x_upper, y_upper = find_monotonic_increasing_bounds(root_func, guess)

    assert x_lower <= root
    assert x_upper >= root


@pytest.mark.parametrize("alg, root_func,"
                         "x_lower, y_lower, x_upper, y_upper,"
                         "max_error, iterations,"
                         "expected_x, allowed_error", [
    (false_position_method, mi_root_func, 0.8333, -0.0937, 1, 0.4596, 1e-10, 10, 0.8654740330821183, 1e-6),
    (false_position_method, mi_root_func, 0.8, -0.09, 1, 0.4, 1e-10, 10, 0.8654740330821183, 1e-6),
    (false_position_method, mi_root_func, 0.8333, -0.0937, 1, 0.4596, 1e-10, 2, 0.8654740330821183, 1e-2),
    (secant_method, mi_root_func, 0.8333, -0.0937, 1, 0.4596, 1e-10, 10, 0.8654740330821183, 1e-6),
    (secant_method, mi_root_func, 0.8, -0.09, 1, 0.4, 1e-10, 10, 0.8654740330821183, 1e-6),
    (secant_method, mi_root_func, 0.8333, -0.0937, 1, 0.4596, 1e-10, 3, 0.8654740330821183, 1e-2),
    # Double default max iterations
    (bisection_method, mi_root_func, 0.8333, -0.0937, 1, 0.4596, 1e-10, 20, 0.8654740330821183, 1e-6),
    (bisection_method, mi_root_func, 0.8, -0.09, 1, 0.4, 1e-10, 20, 0.8654740330821183, 1e-6),
    (bisection_method, mi_root_func, 0.8333, -0.0937, 1, 0.4596, 1e-10, 6, 0.8654740330821183, 1e-2),
])
def test_root_finder(alg, root_func,
                     x_lower, y_lower, x_upper, y_upper,
                     max_error, iterations,
                     expected_x, allowed_error):

    new_x, new_y = alg(
        root_func, x_lower, y_lower, x_upper, y_upper, max_error, iterations
    )

    assert abs(new_x - expected_x) < allowed_error
    assert abs(new_y) < allowed_error
