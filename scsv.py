# simple csv - wrapper around csvreader which makes asserting headers a little easier

from jpy.asrt import *
import csv, codecs

class CSV(object):
    def __init__(self, filename, delimiter=',', file_codec = None):
        self.filename = filename
        self.delimiter = delimiter
        self.file_codec = file_codec

        self.reader = None
        self.headers = None

        self.generator = self.__get_next_line__()
        self.dict_generator = self.__get_next_line_as_dict__()

    def _open(self):
        if self.file_codec != None:
            return open(self.filename, 'r')
        else:
            return codecs.open(self.filename, 'r', self.file_codec)

    def __get_next_line_as_dict__(self):
        # load these first
        headers = self.get_headers()

        for line in self.get_next_line():
            asrt_eq(len(line), len(headers))
            
            d = {}

            for i in range(0, len(headers)):
                d[headers[i]] = line[i]

            yield d

    def __get_next_line__(self):
        with self._open() as self.f:
            self.reader = csv.reader(self.f, delimiter=self.delimiter)

            for line in self.reader:
                yield line

    def get_headers(self):
        if self.headers == None:
            i = 0
            parts = next(self.generator)
            self.headers = parts

        return self.headers

    def assert_headers(self, headers):
        asrt_eq(self.get_headers(), headers)

    def get_next_line_as_dict(self):
        return self.dict_generator

    def get_next_line(self):
        return self.generator

    def close(self):
        if self.f != None:
            self.f.close()

class CSVWriter(object):
    # writes CSV data
    # dest should be a file-like object
    def __init__(self, dest, delimiter=','):
        self.dest = dest
        self.writer = csv.writer(dest, delimiter=delimiter)

        self.headers = None

    def write_headers(self, headers):
        if type(headers) is not list: raise ValueError('aah not a list!')
        self.headers = headers
        self.write(headers)

    # write a list of fields as CSV-delimited data
    def write(self, data = ['']):
        if type(data) in [str, str]: 
            data = [data]

        elif type(data) is dict:
            self._write_dict(data)

        elif type(data) is not list: 
            raise ValueError('aah not a list!')

        else:
            #data = [x.encode('utf-8') for x in data]
            self.writer.writerow(data)

    def _write_dict(self, d):
        if not self.headers: raise ValueError('writing dicts only supported if write_headers() has been called')

        data = []
        for h in self.headers:
            data.append(d[h])

        self.write(data)

    def write_columns(self, columns):
        longest_column = 0
        for c in columns:
            longest_column = max(longest_column, len(c))

        lines = ['']*longest_column

        for c in columns:
            line_number = 0
            for line in c:
                lines[line_number] += line
                line_number += 1

        for line in lines:
            self.write(line)

class CSVCombiner(object):
    def __init__(self, outfile):
        self.outfile = outfile
        self.headers = None

    def combine(self, filename): 
        csvw = CSVWriter(self.outfile)
        csv = CSV(filename)
        
        these_headers = csv.get_headers()

        if self.headers is None:
                self.headers = these_headers
                csvw.write(self.headers)

        asrt_eq(self.headers, these_headers, 'file ' + filename + ' does not have matching headers')

        for parts in csv.get_next_line():
                csvw.write(parts)
