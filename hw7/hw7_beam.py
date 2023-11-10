import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.io.fileio import MatchFiles, ReadMatches




options = PipelineOptions(
    runner='DataflowRunner',  # Change to DataflowRunner to run on GCP
    project='cloudcomputing-398719',
    job_name='html-link-counter',
    region='us-east1',
    staging_location='gs://small-bucket-hw7/staging',
    temp_location='gs://small-bucket-hw7/temp',
    requirements_file='requirements.txt'
)

class ExtractLinksFn(beam.DoFn):
    def process(self, element):
        from bs4 import BeautifulSoup

        file_name, file_contents = element
        soup = BeautifulSoup(file_contents, 'html.parser')

        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href']
            yield file_name, (link, 1)

input_files_path = 'gs://ayang903-hw2-bucket/files/*.html'


with beam.Pipeline(options=options) as p:
    files = (p | MatchFiles(input_files_path)
                | ReadMatches()
                | beam.Map(lambda file: (file.metadata.path.split('/')[-1], file.read_utf8())))
    # useful link: https://stackoverflow.com/questions/58083186/using-matchfiles-in-apache-beam-pipeline-to-get-file-name-and-parse-json-in-py
            #  | 'PrintFileContents' >> beam.Map(print))


    # Extract links
    # becomes a PCollection of tuples like ('0.html', ('4617.html', 1)) ---> (current_file, (outgoing_link, 1))
    links = (files
             | 'ExtractLinks' >> beam.ParDo(ExtractLinksFn()))

    # count outgoing links
    outgoing_links_count = (
        links 
        | 'ExtractOutgoingLinks' >> beam.Map(lambda x: (x[0], x[1][1]))
        | 'CountOutgoingLinks' >> beam.CombinePerKey(sum)
        | 'Top5Outgoing' >> beam.combiners.Top.Of(5, key=lambda x: x[1])
        | 'FlattenResults' >> beam.FlatMap(lambda x: x)
        | 'FormatOutgoing' >> beam.Map(lambda x: f"{x[0]}: {x[1]}")
        | 'WriteTopOutgoingToFile' >> beam.io.WriteToText('gs://small-bucket-hw7/output/top_outgoing', file_name_suffix='.txt')
        # | 'PrintLinks' >> beam.Map(print)
    )

    #count incoming links
    incoming_links_count = (
        links 
        | 'ExtractIncomingLinks' >> beam.Map(lambda x: (x[1][0], x[1][1]))
        | 'CountIncomingLinks' >> beam.CombinePerKey(sum)
        | 'Top5Incoming' >> beam.combiners.Top.Of(5, key=lambda x: x[1])
        | 'FlattenResults2' >> beam.FlatMap(lambda x: x)
        | 'FormatIncoming' >> beam.Map(lambda x: f"{x[0]}: {x[1]}")
        | 'WriteTopIncomingToFile' >> beam.io.WriteToText('gs://small-bucket-hw7/output/top_incoming', file_name_suffix='.txt')
        # | 'PrintLinks2' >> beam.Map(print)
    )
    