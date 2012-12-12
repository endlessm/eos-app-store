import unittest
from add_shortcuts_module.name_format_util import NameFormatUtil

class TestNameFormatUtil(unittest.TestCase):
    
    def setUp(self):
        self.test_object = NameFormatUtil()
    
    def test_url_to_name(self):
        test_cases = [
            ['TestName', 'TestName'],
            ['Test Name', 'Test Name'],
            ['test name', 'Test Name'],
            
            # minimal domains
            ['test.com', 'Test'],
            ['test.com/', 'Test'],
            
            # sub-domains without a leading protocol
            ['www.name.test.com', 'Test Name'],
            ['www.test.com/name', 'Test Name'],
            ['www.test.com/name.html', 'Test Name'],
            ['www.test.com/name/extra', 'Test Name'],
            ['blogs.lancenet.com', 'Lancenet Blogs'],
            
            # domains with a leading protocol
            ['https://test.com', 'Test'],
            ['http://test.com', 'Test'],
            ['http://test.com/', 'Test'],
            
            # sub-domains with a leading protocol
            ['http://www.telegraph.co.uk/news/', 'Telegraph News'],
            ['http://www.esporte.gov.br', 'Esporte'],
            ['http://vagas.infojobs.com.br', 'Infojobs Vagas'],
            ['http://blogs.lancenet.com.br', 'Lancenet Blogs'],
            ['http://blogs.lancenet.ly', 'Lancenet Blogs'],
            ['http://blogs.ly', 'Blogs'],
            ['http://foo.dev.twitter.com', 'Twitter Dev Foo'],
            
            # sub-domains with a leading protocol and multiple directories
            ['http://www.saude.rj.gov.br/upas-24-horas/5629-upa-24h-rio-de-janeiro.html', 'Rj Saude Upas 24 Horas'],
            ['http://www.saude.rj.gov.br/upas_24_horas/5629_upa_24h_rio_de_janeiro.html', 'Rj Saude Upas 24 Horas'],
            ['http://www.saude.rj.gov.br/upas_24_horas/5629_upa.24h.rio.de_janeiro.html', 'Rj Saude Upas 24 Horas'],
            ['http://blogs.lancenet.com.br/gritodanacao', 'Lancenet Blogs Gritodanacao'],
            
            # sub-domains with file in first directory
            ['http://www.saude.rj.gov.br/5629_upa.24h.rio.de_janeiro.html', 'Rj Saude 5629 Upa 24h Rio De Janeiro']
        ]
        
        idx = 0
        for test_case in test_cases:
            value = self.test_object.format(test_case[0])
            self.assertEqual(value, test_case[1], 
                             "Test index "+repr(idx)+" failed (expecting: "+test_case[1]+" received: "+value+")")
            idx = idx + 1
