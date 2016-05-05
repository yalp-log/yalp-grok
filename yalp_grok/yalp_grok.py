# vim: set et ts=4 sw=4 fileencoding=utf-8:
'''
yalp_grok.yalp_grok
===================
'''
import os
import sys
import copy
from collections import namedtuple
import regex as re


DEFAULT_PATTERNS_DIRS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'patterns')
]

# Attributes used to determine type on groupdict post processing
# Just covering floats and ints
INT = ('INT', 'POSINT', 'NONNEGINT')
FLOAT = ('BASE10NUM')
TYPES = {'int': INT, 'float': FLOAT}

# GROK pattern/format data abstracted from logic
NAMED_PATTERN = {
    'pattern': r'%{(\w+):(\w+)(:\w+)?}',
    'format': '(?P<{key}>{regex})'
}

UNNAMED_PATTERN = {'pattern': r'%{(\w+)}', 'format': '({regex})'}
PATTERN_FORMATS = (UNNAMED_PATTERN, NAMED_PATTERN)

# Magic pattern for capturing named grok keys in various states
# of expansion to identify final grok key of named attributes
NAMED_KEY_PATTERN = re.compile(
    r'(?:%{(?P<grok>\w+):(?P<key>\w+)(?::(?P<type>\w+))?}'
    r'|\(\?P<(?P<key>\w+)>(?:%{(?P<grok>\w+)}'
    r'|\(\?:%{(?P<grok>\w+)}\))\))'
)

Pattern = namedtuple('Pattern', 'name regex_str')


def grok_match(text, pattern, custom_patterns=None,
               custom_patterns_dir=None, auto_map=False):
    '''
    Search for pattern in text.

    If text is matched with pattern, return variable names specified
    (%{pattern:variable name}) in pattern and their corresponding
    values. If not matched, return None. custom patterns can be passed
    in by custom_patterns(pattern name, pattern regular expression pair)
    or custom_patterns_dir.

    Data type conversion supported. For example %{NUMBER:num:int} which
    converts the num semantic from a string to an integer. Currently the
    only supported conversions are int and float.

    If auto_map set to True then GROK key will be used to auto determine
    data type conversion. For example %{NUMBER:num} which converts the
    num semantic from a string to a float. A data type defined in grok
    pattern will take precedence over auto determined type.

    If type conversion fails then value left as a string.
    '''
    return grok_search(text, compile_pattern(
        pattern, custom_patterns, custom_patterns_dir, auto_map=auto_map))


def compile_pattern(pattern, custom_patterns=None,
                    custom_patterns_dir=None, auto_map=False):
    '''
    Compile pattern before use for better performance when matching.

    Returns a regex string that can be passed as a pattern to
    grok_search() for matching. Custom patterns can be passed in by
    custom_patterns(pattern name, pattern regular expression pair) or
    custom_patterns_dir, and will then be used in addition to the
    built-in ones.
    '''
    all_patterns = copy.deepcopy(PREDEFINED_PATTERNS)

    custom_pats = {}

    if custom_patterns_dir is not None:
        custom_pats = _reload_patterns([custom_patterns_dir])

    if custom_patterns:
        for pat_name, regex_str in custom_patterns.items():
            custom_pats[pat_name] = Pattern(pat_name, regex_str)

    all_patterns.update(custom_pats)
    py_regex_pattern = pattern
    type_map = _map_types(py_regex_pattern, auto_map)

    while True:

        # replace %{pattern_name:custom_name} with regex and regex group name
        # replace %{pattern_name} with regex
        py_regex_pattern, type_map_temp = _sub_pattern_name(
            py_regex_pattern, all_patterns, type_map, auto_map)
        type_map.update(type_map_temp)

        if re.search(r'%{\w+(:\w+)?}', py_regex_pattern) is None:
            break

    return re.compile(py_regex_pattern), type_map


def grok_search(text, pattern):
    '''
    Search for pattern in text.

    Return dictionary with named fields in pattern as keys, or None if
    no match found.
    '''
    match_obj = pattern[0].search(text)

    if match_obj is not None:
        match_dict = match_obj.groupdict()
        return _apply_map(match_dict, pattern[1])
    return None


def _reload_patterns(patterns_dirs):
    '''
    Load patters from all files in a directory.
    '''
    all_patterns = {}
    for dir_ in patterns_dirs:
        for pat_file in os.listdir(dir_):
            patterns = _load_patterns_from_file(os.path.join(dir_, pat_file))
            all_patterns.update(patterns)

    return all_patterns


def _load_patterns_from_file(pat_file):
    '''
    Load patterns from a text file.
    '''
    patterns = {}
    with open(pat_file, 'r') as pfh:
        for line in pfh:
            line = line.strip()
            if line == '' or line.startswith('#'):
                continue

            sep = line.find(' ')
            pat_name = line[:sep]
            regex_str = line[sep:].strip()
            pat = Pattern(pat_name, regex_str)
            patterns[pat.name] = pat

    return patterns


def _sub_pattern_name(py_regex_pattern, all_patterns, type_map, auto_map):
    '''
    Expand grok pattern with regex substitution
    '''
    for pattern_format in PATTERN_FORMATS:
        pattern = pattern_format['pattern']
        py_regex_pattern = re.sub(
            pattern, lambda match, pat_format=pattern_format:
            _format_pattern_name(
                match, pat_format, all_patterns),
            py_regex_pattern)
        type_map.update(_map_types(py_regex_pattern, auto_map, type_map))

    return py_regex_pattern, type_map


def _format_pattern_name(match, pattern_format, all_patterns):
    '''
    Generate a new pattern based on capture results

    Expand keys with regex using generic string format
    '''
    return pattern_format['format'].format(
        key=_get_group_key(match),
        regex=all_patterns[match.group(1)].regex_str
    )


def _get_group_key(match):
    '''
    Return None on IndexError

    Return None if no more than 1 index in group
    Probably a better way to do this...
    '''
    try:
        return match.group(2)
    except IndexError:
        return None


def _map_types(py_regex_pattern, auto_map, type_map=None):
    '''
    Generate type map against regex pattern

    Follow conditions in correct order to assign data type for a named
    Grok key. For now this will only affect Grok keys listed in INT and
    FLOAT variables in order to assign int or float primitive types to
    attribute names using matching Grok keys. A defined type using ES
    Grok type semantic takes precedence.
    '''
    if not type_map:
        type_map = {}

    named_grok_keys = NAMED_KEY_PATTERN.findall(py_regex_pattern)
    for grok_key, name, defined_type in named_grok_keys:
        if auto_map:
            detected_type = _type_match(grok_key)
            if detected_type and name not in type_map.keys():
                type_map[name] = detected_type

        if defined_type in TYPES.keys():
            type_map[name] = defined_type

    return type_map


def _type_match(grok_key):
    '''
    Attempt to match grok key with types associated with it
    '''
    for type_item, grok_keys in TYPES.items():
        if grok_key in grok_keys:
            return type_item
    return None


def _apply_map(match_dict, type_map):
    '''
    Apply generated type map to regex group dict

    Cast values of any attribute names inside map to their identified
    type.
    '''
    if type_map:
        for name, detected_type in type_map.items():
            try:
                match_dict[name] = _convert(match_dict[name], detected_type)
            except ValueError:
                if sys.version_info[0] < 3:
                    sys.exc_clear()
    return match_dict


def _convert(value, detected_type):
    '''
    Attempts conversion if value is not None.
    '''
    if value:
        if detected_type == 'int':
            return int(value)
        if detected_type == 'float':
            return float(value)
    return value


PREDEFINED_PATTERNS = _reload_patterns(DEFAULT_PATTERNS_DIRS)
