import os
import pandas as pd
import re
from lxml import etree
import random
import time


class ParsedXMLFile:
    def __init__(self, path, loinc_codes):
        self.path = path
        try:
            self.tree = etree.parse(path)
        except etree.XMLSyntaxError:
            p = etree.XMLParser(huge_tree=True)
            self.tree = etree.parse(path, parser=p)
        self.root = self.tree.getroot()
        self.namespace = {'ns': get_ns(self.root)}
        self.loinc_codes = loinc_codes

    def analyze(self):
        company_id, company_ext, company_name = self.find_company_info()

        result = {'name': self.find_drug_name(),
                  'ID': self.find_drug_code(),
                  'set_id': self.find_set_id(),
                  'company_id': company_id,
                  'company_ext': company_ext,
                  'company_name': company_name}

        result.update(self.find_loinc_codes())
        # print(result)
        # pd.DataFrame(result, index=[0]).to_csv('test.csv', index=False)

        return result

    def find_company_info(self):
        org_element = self.root.find('.//ns:representedOrganization', self.namespace)
        id_element = org_element.find('./ns:id', self.namespace)
        company_id = None
        company_ext = None
        company_name = org_element.find('./ns:name', self.namespace).text

        if id_element is not None:
            attributes = id_element.attrib
            if 'root' in attributes:
                company_id = attributes['root']
            if 'extension' in attributes:
                company_ext = attributes['extension']

        return company_id, company_ext, company_name

    def find_drug_name(self):
        return self.root.find('./ns:component//ns:manufacturedProduct//ns:name', self.namespace).text.strip()

    def find_drug_code(self):
        return self.root.find('ns:id', self.namespace).attrib['root']

    def find_set_id(self):
        return self.root.find('ns:setId', self.namespace).attrib['root']

    def find_loinc_codes(self):
        code_content = {}
        for code in self.loinc_codes:
            section = self.root.findall('.//ns:code[@code="{}"]...'.format(code), self.namespace)
            if len(section) > 1:
                print(self.path)
            elif len(section) == 0:
                continue
            section = section[0]

            # content = []
            # components = section.findall('./ns:component', self.namespace)
            # for component in components:
            #     text = component.xpath('normalize-space(.)')
            #     content.append(text.replace('\n', ' '))

            # code_content[code] = ' '.join(content)

            text = clean_text(section.xpath('normalize-space(.)'))
            code_content[code] = text

        return code_content


def parse_files(directory, sample=1.0):
    files = os.listdir(directory)
    results = []
    loinc_codes_df = pd.read_excel('data/LOINC_codes/DrugLabels_ResultsTemplate.xlsx')
    loinc_codes_df = loinc_codes_df[loinc_codes_df['highlight'] == 1]
    loinc_codes = loinc_codes_df['LOINC Code'].values
    for file in files:
        if file.endswith('.xml'):
            if random.random() < sample:
                print(file)
                parsed_xml = ParsedXMLFile(os.path.join(directory, file), loinc_codes)
                results.append(parsed_xml.analyze())

    pd.DataFrame(results).to_excel('results.xlsx', index=False, na_rep='NA')


# a function to retrieve namespace string
def get_ns(element):
    m = re.match('{.*}', element.tag)
    return m.group(0)[1:-1] if m else ''


def clean_text(text):
    text = text.replace(u'\n', u' ').replace(u'\xa0', u' ').replace(u'\u2022', '').replace('·', '').replace('()', '').strip()

    # return " ".join(text.split())
    return text


def main():
    directory = 'FDA_drug_xml_files'
    # tree = ET.parse(os.path.join(directory, 'e26005ef-77f0-4393-a2dc-b5fe460cead8.xml'))
    # root = tree.getroot()
    # print(find_drug_name(root))
    start = time.time()
    parse_files(directory, sample=1)
    print(time.time() - start)


if __name__ == '__main__':
    main()
