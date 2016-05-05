# vim: set et ts=4 sw=4 fileencoding=utf-8:
'''
tests.test_yalp_grok
====================
'''
import os
import unittest

from yalp_grok import grok_match


class TestOnePattern(unittest.TestCase):
    ''' Test a single patter match '''

    def test_int_match(self):
        text = '1024'
        pat = '%{INT:test_int}'
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match['test_int'], '1024')

    def test_number_match(self):
        text = '1024'
        pat = '%{NUMBER:test_num}'
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match['test_num'], '1024')

    def test_word_match(self):
        text = 'garyelephant '
        pat = '%{WORD:name} '
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match['name'], text.strip())

    def test_ip_match(self):
        text = '192.168.1.1'
        pat = '%{IP:ip}'
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match['ip'], text.strip())

    def test_host_match(self):
        text = 'github.com'
        pat = '%{HOST:website}'
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match['website'], text.strip())

    def test_timestamp_iso8601_match(self):
        text = '1989-11-04 05:33:02+0800'
        pat = '%{TIMESTAMP_ISO8601:ts}'
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match['ts'], text.strip())

    def test_missing_variable_name(self):
        '''
        test_missing_variable_name

        You get empty dict because variable name is not set,
        compare "%{WORD}" and "%{WORD:variable_name}"
        '''
        text = 'github'
        pat = '%{WORD}'
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match, {})

    def test_no_match(self):
        text = 'github'
        pat = '%{NUMBER:test_num}'
        match = grok_match(text, pat)
        self.assertIsNone(match)


class TestMutiplePatterns(unittest.TestCase):
    '''
    Test matching more complex patters
    '''

    def test_multiple_patterns(self):
        text = 'gary 25 "never quit"'
        pat = '%{WORD:name} %{INT:age} %{QUOTEDSTRING:motto}'
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match['name'], 'gary')
        self.assertEqual(match['age'], '25')
        self.assertEqual(match['motto'], '"never quit"')

    def test_missing_variable_names(self):
        text = 'gary 25 "never quit"'
        pat = '%{WORD} %{INT} %{QUOTEDSTRING}'
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match, {})

    def test_not_match(self):
        #"male" is not INT
        text = 'gary male "never quit"'
        pat = '%{WORD:name} %{INT:age} %{QUOTEDSTRING:motto}'
        match = grok_match(text, pat)
        self.assertIsNone(match)

    def test_qs(self):
        text = 'gary "25" "never quit" "blah"'
        pat = '%{WORD:name} "%{INT:age}" %{QS:motto} %{QS:blah}'
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match['name'], 'gary')
        self.assertEqual(match['age'], '25')
        self.assertEqual(match['motto'], '"never quit"')

    def test_nginx_log_match(self):
        text = (
            'edge.v.iask.com.edge.sinastorage.com 14.18.243.65 6.032s - [21/Jul/2014:16:00:02 +0800]'
            ' "GET /edge.v.iask.com/125880034.hlv HTTP/1.0" 200 70528990 "-"'
            ' "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36"'
        )
        pat = (
            '%{HOST:host} %{IP:client_ip} %{NUMBER:delay}s - \[%{HTTPDATE:time_stamp}\]'
            ' "%{WORD:verb} %{URIPATHPARAM:uri_path} HTTP/%{NUMBER:http_ver}" %{INT:http_status} %{INT:bytes} %{QS:referrer}'
            ' %{QS:agent}'
        )
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match['host'], 'edge.v.iask.com.edge.sinastorage.com')
        self.assertEqual(match['client_ip'], '14.18.243.65')
        self.assertEqual(match['delay'], '6.032')
        self.assertEqual(match['time_stamp'], '21/Jul/2014:16:00:02 +0800')
        self.assertEqual(match['verb'], 'GET')
        self.assertEqual(match['uri_path'], '/edge.v.iask.com/125880034.hlv')
        self.assertEqual(match['http_ver'], '1.0')
        self.assertEqual(match['http_status'], '200')
        self.assertEqual(match['bytes'], '70528990')
        self.assertEqual(match['referrer'], '"-"')
        self.assertEqual(match['agent'], '"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36"')

    def test_compound_matches(self):
        text = (
            '127.0.0.1 - - [15/Sep/2015:13:41:35 -0400] "GET /index.html '
            'HTTP/1.1" 502 352 "-" '
            '"Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0"'
        )
        pat = '%{COMBINEDAPACHELOG}'
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match['clientip'], '127.0.0.1')
        self.assertEqual(match['ident'], '-')
        self.assertEqual(match['auth'], '-')
        self.assertEqual(match['timestamp'], '15/Sep/2015:13:41:35 -0400')
        self.assertEqual(match['verb'], 'GET')
        self.assertEqual(match['request'], '/index.html')
        self.assertEqual(match['httpversion'], '1.1')
        self.assertEqual(match['response'], '502')
        self.assertEqual(match['bytes'], '352')
        self.assertEqual(match['referrer'], '"-"')
        self.assertEqual(match['agent'], '"Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0"')


class TestCustomPatterns(unittest.TestCase):
    '''
    Test custom patterns
    '''
    def test_custom_patterns(self):
        custom_pats = {'ID' : '%{WORD}-%{INT}'}
        text = 'Beijing-1104,gary 25 "never quit"'
        pat = '%{ID:user_id},%{WORD:name} %{INT:age} %{QUOTEDSTRING:motto}'
        match = grok_match(text, pat, custom_patterns=custom_pats)
        self.assertIsNotNone(match)
        self.assertEqual(match['user_id'], 'Beijing-1104')
        self.assertEqual(match['name'], 'gary')
        self.assertEqual(match['age'], '25')
        self.assertEqual(match['motto'], '"never quit"')

    def test_custom_pat_files(self):
        pats_dir = os.path.join(os.path.dirname(__file__), 'test_patterns')
        text = 'Beijing-1104,gary 25 "never quit"'
        pat = '%{ID:user_id},%{WORD:name} %{INT:age} %{QUOTEDSTRING:motto}'
        match = grok_match(text, pat, custom_patterns_dir=pats_dir)
        self.assertIsNotNone(match)
        self.assertEqual(match['user_id'], 'Beijing-1104')
        self.assertEqual(match['name'], 'gary')
        self.assertEqual(match['age'], '25')
        self.assertEqual(match['motto'], '"never quit"')


class TestAutoMap(unittest.TestCase):
    '''
    Test type casting with auto generated type map
    '''
    def test_nginx_log_match(self):
        text = (
            'edge.v.iask.com.edge.sinastorage.com 14.18.243.65 6.032s - [21/Jul/2014:16:00:02 +0800]'
            ' "GET /edge.v.iask.com/125880034.hlv HTTP/1.0" 200 70528990 "-"'
            ' "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36"'
        )
        pat = (
            '%{HOST:host} %{IP:client_ip} %{NUMBER:delay}s - \[%{HTTPDATE:time_stamp}\]'
            ' "%{WORD:verb} %{URIPATHPARAM:uri_path} HTTP/%{NUMBER:http_ver}" %{INT:http_status} %{INT:bytes} %{QS:referrer}'
            ' %{QS:agent}'
        )
        match = grok_match(text, pat, auto_map=True)
        self.assertIsNotNone(match)
        self.assertEqual(match['host'], 'edge.v.iask.com.edge.sinastorage.com')
        self.assertEqual(match['client_ip'], '14.18.243.65')
        self.assertEqual(match['delay'], 6.032)
        self.assertEqual(match['time_stamp'], '21/Jul/2014:16:00:02 +0800')
        self.assertEqual(match['verb'], 'GET')
        self.assertEqual(match['uri_path'], '/edge.v.iask.com/125880034.hlv')
        self.assertEqual(match['http_ver'], 1.0)
        self.assertEqual(match['http_status'], 200)
        self.assertEqual(match['bytes'], 70528990)
        self.assertEqual(match['referrer'], '"-"')
        self.assertEqual(match['agent'],
                         '"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36"')

    def test_compound_matches(self):
        text = (
            '127.0.0.1 - - [15/Sep/2015:13:41:35 -0400] "GET /index.html '
            'HTTP/1.1" 502 352 "-" '
            '"Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0"'
        )
        pat = '%{COMBINEDAPACHELOG}'
        match = grok_match(text, pat, auto_map=True)
        self.assertIsNotNone(match)
        self.assertEqual(match['clientip'], '127.0.0.1')
        self.assertEqual(match['ident'], '-')
        self.assertEqual(match['auth'], '-')
        self.assertEqual(match['timestamp'], '15/Sep/2015:13:41:35 -0400')
        self.assertEqual(match['verb'], 'GET')
        self.assertEqual(match['request'], '/index.html')
        self.assertEqual(match['httpversion'], 1.1)
        self.assertEqual(match['response'], 502)
        self.assertEqual(match['bytes'], 352)
        self.assertEqual(match['referrer'], '"-"')
        self.assertEqual(match['agent'], '"Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0"')

    def test_non_neg_int_match(self):
        text = '3245521'
        pat = '%{NONNEGINT:test_int}'
        match = grok_match(text, pat, auto_map=True)
        self.assertIsNotNone(match)
        self.assertEqual(match['test_int'], 3245521)

    def test_syslog_match(self):
        text = (
            '2016-03-25T05:55:32 <3245521.83838> host kernel: [1858.738417]  [<ffffffff811e6c31>] SyS_ioctl+0x81/0xa0'
        )
        pat = '%{SYSLOGLINE}'
        match = grok_match(text, pat, auto_map=True)
        self.assertEqual(match['facility'], 3245521)
        self.assertEqual(match['pid'], None)
        self.assertEqual(match['priority'], 83838)


class TestDefinedType(unittest.TestCase):
    def test_syslog_match(self):
        pats_dir = os.path.join(os.path.dirname(__file__), 'test_patterns')
        text = (
            '2016-03-25T05:55:32 <3245521.83838> host kernel: [1858.738417]  [<ffffffff811e6c31>] SyS_ioctl+0x81/0xa0'
        )
        pat = '%{TYPEDSYSLOGLINE}'
        match = grok_match(text, pat, custom_patterns_dir=pats_dir)
        self.assertEqual(match['facility'], 3245521)
        self.assertEqual(match['pid'], None)
        self.assertEqual(match['priority'], 83838)

    def test_non_neg_int_match(self):
        text = '3245521'
        pat = '%{NONNEGINT:test_int:int}'
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match['test_int'], 3245521)

    def test_conversion_failure(self):
        text = 'not_a_int'
        pat = '%{WORD:test_str:int}'
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match['test_str'], 'not_a_int')

    def test_compound_matches(self):
        pats_dir = os.path.join(os.path.dirname(__file__), 'test_patterns')
        text = (
            '127.0.0.1 - - [15/Sep/2015:13:41:35 -0400] "GET /index.html '
            'HTTP/1.1" 502 352 "-" '
            '"Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0"'
        )
        pat = '%{TYPEDCOMBINEDAPACHELOG}'
        match = grok_match(text, pat, custom_patterns_dir=pats_dir)
        self.assertIsNotNone(match)
        self.assertEqual(match['clientip'], '127.0.0.1')
        self.assertEqual(match['ident'], '-')
        self.assertEqual(match['auth'], '-')
        self.assertEqual(match['timestamp'], '15/Sep/2015:13:41:35 -0400')
        self.assertEqual(match['verb'], 'GET')
        self.assertEqual(match['request'], '/index.html')
        self.assertEqual(match['httpversion'], 1.1)
        self.assertEqual(match['response'], 502)
        self.assertEqual(match['bytes'], 352)
        self.assertEqual(match['referrer'], '"-"')
        self.assertEqual(match['agent'], '"Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0"')

    def test_nginx_log_match(self):
        text = (
            'edge.v.iask.com.edge.sinastorage.com 14.18.243.65 6.032s - [21/Jul/2014:16:00:02 +0800]'
            ' "GET /edge.v.iask.com/125880034.hlv HTTP/1.0" 200 70528990 "-"'
            ' "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36"'
        )
        pat = (
            '%{HOST:host} %{IP:client_ip} %{NUMBER:delay:float}s - \[%{HTTPDATE:time_stamp}\]'
            ' "%{WORD:verb} %{URIPATHPARAM:uri_path} HTTP/%{NUMBER:http_ver:float}" %{INT:http_status:int} %{INT:bytes:int} %{QS:referrer}'
            ' %{QS:agent}'
        )
        match = grok_match(text, pat)
        self.assertIsNotNone(match)
        self.assertEqual(match['host'], 'edge.v.iask.com.edge.sinastorage.com')
        self.assertEqual(match['client_ip'], '14.18.243.65')
        self.assertEqual(match['delay'], 6.032)
        self.assertEqual(match['time_stamp'], '21/Jul/2014:16:00:02 +0800')
        self.assertEqual(match['verb'], 'GET')
        self.assertEqual(match['uri_path'], '/edge.v.iask.com/125880034.hlv')
        self.assertEqual(match['http_ver'], 1.0)
        self.assertEqual(match['http_status'], 200)
        self.assertEqual(match['bytes'], 70528990)
        self.assertEqual(match['referrer'], '"-"')
        self.assertEqual(match['agent'],
                         '"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36"')
