# vim: set et ts=4 sw=4 fileencoding=utf-8:
'''
yalp_grok.exceptions
====================

Exceptions for grok
'''


class GrokError(Exception):
    ''' Catch-all for Grok related exceptions '''


class PatternNotFound(GrokError):
    ''' Cannot find pattern '''
