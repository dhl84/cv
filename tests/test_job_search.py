import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = next(p for p in (ROOT/'scripts/jobprep.py', ROOT/'workbench/scripts/jobprep.py') if p.exists())
spec = importlib.util.spec_from_file_location('jobprep', SOURCE)
j = importlib.util.module_from_spec(spec)
spec.loader.exec_module(j)


class SearchTests(unittest.TestCase):
    def test_ddg_redirects_and_distinct_query_ids(self):
        page = '''<a href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fjob%3Fid%3D1">Finance role</a>
        <a href="/l/?uddg=https%3A%2F%2Fexample.com%2Fjob%3Fid%3D2">Other role</a>
        <a href="https://duckduckgo.com/about">About</a>'''
        with patch.object(j, '_get', return_value=page):
            self.assertEqual([h[1] for h in j.ddg_search('test', 5)],
                             ['https://example.com/job?id=1', 'https://example.com/job?id=2'])

    def test_irrelevant_provider_does_not_stop_fallback(self):
        good = ('Senior Finance Manager - Brands', 'https://jobs.marksandspencer.com/job/123', 'Marks and Spencer')
        site = dict(j.employer_site('M&S Brands'), roles={})
        with patch.object(j, 'employer_site', return_value=site), \
             patch.object(j, 'ollama_web_search', return_value=[('M', 'https://example.com', '')]), \
             patch.object(j, 'ddg_search', return_value=[good]):
            hits, attempts, _ = j.find_jobs('M&S Brands', 'Senior Finance Manager', 1)
        self.assertEqual(hits, [good])
        self.assertEqual(attempts[0]['accepted'], 0)

    def test_wrong_employer_rejected(self):
        wrong = [('Strategy & Operations Manager', 'https://example.com/job', 'Other company')]
        with patch.object(j, 'employer_site', return_value=dict(j.employer_site('NALA'), roles={})), \
             patch.object(j, 'ollama_web_search', return_value=wrong), \
             patch.object(j, 'ddg_search', return_value=[]), \
             patch.object(j, 'bing_rss_search', return_value=[]), \
             patch.object(j, 'mojeek_search', return_value=[]):
            self.assertEqual(j.find_jobs('NALA', 'Strategy & Operations Manager')[0], [])

    def test_aggregator_exact_title_rejected(self):
        site = dict(j.employer_site('NALA'), roles={})
        bad = [('NALA Strategy & Operations Manager', 'https://startup.jobs/nala/123', 'NALA')]
        with patch.object(j, 'employer_site', return_value=site), \
             patch.object(j, 'ollama_web_search', return_value=bad), \
             patch.object(j, 'ddg_search', return_value=[]), \
             patch.object(j, 'bing_rss_search', return_value=[]), \
             patch.object(j, 'mojeek_search', return_value=[]):
            self.assertEqual(j.find_jobs('NALA', 'Strategy & Operations Manager')[0], [])

    def test_ats_tenant_and_domain_boundaries(self):
        site = j.employer_site('NALA')
        self.assertTrue(j.official_url('https://apply.workable.com/nalamoney/j/123/', site))
        for url in ['https://apply.workable.com/other/j/123/',
                    'https://apply.workable.com/nalamoney-fake/j/123/',
                    'https://apply.workable.com.evil.com/nalamoney/j/123/',
                    'https://apply.workable.com/nalamoney/../other/',
                    'https://apply.workable.com/nalamoney/%2e%2e/other/']:
            self.assertFalse(j.official_url(url, site), url)

    def test_unknown_employer_fails_closed(self):
        with patch.object(j, 'ollama_web_search') as provider:
            self.assertEqual(j.find_jobs('Unknown Company', 'Finance Manager')[0], [])
            provider.assert_not_called()

    def test_confirmed_link_and_careers_fallback(self):
        self.assertEqual(j.find_jobs('elasticStage', 'Finance Operations and Strategy Manager')[0][0][1],
                         'https://apply.workable.com/elasticstage/j/5BE05B35AD/')
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(j, 'find_jobs', return_value=([], [], [])):
            result = j.save_job_links('Aga Khan Foundation', 'Head of Finance & Administration', folder)
            self.assertIn('https://akf.org/careers/', result)
            self.assertIn('not an exact role match', result)

    def test_failed_fetch_keeps_url_and_existing_ad(self):
        with tempfile.TemporaryDirectory() as folder:
            ad = Path(folder)/'job-ad.md'
            ad.write_text('My pasted advert')
            with patch.object(j, '_get', side_effect=TimeoutError('timeout')):
                result = j.import_job_url('https://example.com/job', folder)
            self.assertIn('paste', result)
            self.assertEqual(ad.read_text(), 'My pasted advert')
            self.assertIn('https://example.com/job', (Path(folder)/'job-source.url').read_text())

if __name__ == '__main__':
    unittest.main()

