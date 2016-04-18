import re, requests
from urlparse import urlparse
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor


CODE_INCLUDE_TAG = re.compile(r'\[!\[[\w ]+\]\(https:\/\/www.mbed.com\/embed\/[\w?=:/.-]+\)\]\([\w:/.-]+\)')
V2_IMPORT_URL = 'https://developer.mbed.org/compiler/#import:'
V3_IMPORT_URL = 'https://mbed.com/ide/open/?url='


class CodeInclusionPreprocessor(Preprocessor):
    def build_import_button(self, url, extra_style='', button_text='Import into mbed IDE'):
        return '<a href=%s style="float:right; color:white;%s" class="button" target="_blank">%s</a>' % (url, extra_style, button_text)

    def get_v2_button(self, url, extra_style=''):
        return self.build_import_button(url, extra_style=extra_style, button_text='Import into mbed v2 IDE')

    def get_v3_button(self, url, extra_style=''):
        return self.build_import_button(url, extra_style=extra_style, button_text='Import into mbed v3 IDE')

    def get_import_url(self, url):
        parsed_url = urlparse(url)
        if 'github.com' in parsed_url.netloc:
            import_path = 'https://github.com'
            for p in parsed_url.path.split('/')[:3]:
                if p:
                    import_path += '/' + p
            return V3_IMPORT_URL + import_path
        elif 'developer.mbed' in parsed_url.netloc:
            import_path = ''
            for p in parsed_url.path.split('/')[:5]:
                if p:
                    import_path += '/' + p
            return V2_IMPORT_URL + import_path
        return ''

    def get_source_url(self, url):
        parsed_url = urlparse(url)
        if 'github.com' in parsed_url.netloc:
            source_url = 'https://raw.githubusercontent.com/'
            github_user = parsed_url.path.split('/')[1]
            github_repo = parsed_url.path.split('/')[2]
            file_path = ''
            for loc in parsed_url.path.split('/')[4:]:
                file_path += '/' + loc
            source_url += github_user + '/' + github_repo + file_path
            return source_url
        elif 'developer.mbed' in parsed_url.netloc:
            path = parsed_url.path.split('/')
            path[5] = 'raw-file'
            file_path = ''
            for p in path:
                if p:
                    file_path += '/' + p
            source_url = 'https://developer.mbed.org' + file_path
            return source_url

    def build_code_block(self, lines, url):
        filename = url.split('/')[-1]
        import_url = self.get_import_url(url)
        code_header = '<div class="code-header"><a href=%s><i class="fa fa-file-code-o"></i> <b>%s</b></a>' % (url, filename)
        if import_url:
            code_header += '<a href=%s style="float:right; color:white;" class="button" target="_blank">Import into mbed IDE</a>' % import_url
        code_header += '</div>'
        code_block = [
            '<div class="code-include-block">',
            code_header,
            '```'
        ]
        code_string = ''
        for line in lines:
            code_string += line
        code_block += [code_string, '```', '</div>']
        return code_block

    def run(self, lines):
        new_lines = []
        prev_line = ''
        for line in lines:
            m = CODE_INCLUDE_TAG.match(line)
            if m:
                urls = re.findall(r'\([\w:/.?=-]+\)', m.group())
                source_url = urls[1][1:-1]
                raw_source_url = self.get_source_url(source_url)
                response = requests.get(raw_source_url)
                if response.status_code == requests.codes.ok:
                    code_block = self.build_code_block(response.text.splitlines(True), source_url)
                    if not prev_line: # There is a bug in the way the code block renders if the preceding line is an empty string, so to fix this add a line with a space before the code block...
                        code_block = ['&nbsp;'] + code_block
                    new_lines += code_block
            else:
                new_lines.append(line)
            prev_line = line
        return new_lines

class Inclusion(Extension):
    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('code_inclusion', CodeInclusionPreprocessor(md), '>normalize_whitespace')

def makeExtension(*args, **kwargs):
    return Inclusion(*args, **kwargs)
