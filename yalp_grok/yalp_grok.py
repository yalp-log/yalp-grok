# vim: set et ts=4 sw=4 fileencoding=utf-8:
'''
yalp_grok.yalp_grok
===================
'''
import os
import copy
from collections import namedtuple
import regex as re


Pattern = namedtuple('Pattern', 'name regex_str')

DEFAULT_PATTERNS_DIRS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'patterns'),
]


def grok_match(text, pattern, custom_patterns=None, custom_patterns_dir=None):
    '''
    Search for pattern in text.

    If text is matched with pattern, return variable names specified
    (%{pattern:variable name}) in pattern and their corresponding
    values. If not matched, return None. custom patterns can be passed
    in by custom_patterns(pattern name, pattern regular expression pair)
    or custom_patterns_dir.
    '''
    return grok_search(text, compile_pattern(pattern,
                                             custom_patterns,
                                             custom_patterns_dir))


def compile_pattern(pattern, custom_patterns=None, custom_patterns_dir=None):
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
    while True:
        # replace %{pattern_name:custom_name} with regex and regex group name
        py_regex_pattern = re.sub(
            r'%{(\w+):(\w+)}',
            lambda m: "(?P<{}>{})".format(m.group(2),
                                          all_patterns[m.group(1)].regex_str),
            py_regex_pattern,
        )
        # replace %{pattern_name} with regex
        py_regex_pattern = re.sub(
            r'%{(\w+)}',
            lambda m: "({})".format(all_patterns[m.group(1)].regex_str),
            py_regex_pattern,
        )
        if re.search(r'%{\w+(:\w+)?}', py_regex_pattern) is None:
            break

    return py_regex_pattern


def grok_search(text, pattern):
    '''
    Search for pattern in text.

    Return dictionary with named fields in pattern as keys, or None if
    no match found.
    '''
    match_obj = re.search(pattern, text)
    return match_obj.groupdict() if match_obj is not None else None


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


PREDEFINED_PATTERNS = _reload_patterns(DEFAULT_PATTERNS_DIRS)
