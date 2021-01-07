# Lowercase (params ignored)
def lower(value, params):
    return value.lower()

# Uppercase (params ignoredv)
def upper(value, params):
    return value.upper()

# Strips everything in the included list out of the value
# E.g. value = 'hello', params = ['h', 'l'] 
# Return: 'eo'
def strip(value, params):
    for param in params:
        value = value.strip(param)
    return value

# Replaces first parameter with second parameter
def replace(value, params):
    return value.replace(params[0], params[1])

cleaning_functions = {
    'lower': lower,
    'upper': upper,
    'strip': strip,
    'replace': replace,
}

# Looks up the cleaning steps specified in steps (see `cleaning_steps` column in /models/custom_attribute.py)
# Then executes the cleaning steps and returns the final value
def clean_value(steps, value):
    for step in steps:
        function_name, *function_args = step
        if len(function_args):
            function_args = function_args.pop()
        if function_name not in cleaning_functions:
            raise Exception(f'{function_name} not a valid sanitization function. Please chooose one of {cleaning_functions.keys()}')
        value = cleaning_functions[function_name](value, function_args)
    return value
