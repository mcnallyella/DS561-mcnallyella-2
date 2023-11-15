from bs4 import BeautifulSoup
import apache_beam as beam
from apache_beam.io import fileio
from apache_beam.options.pipeline_options import PipelineOptions


# might want to set pipeline options
class MyOptions(PipelineOptions):
    @classmethod
    def _add_argparse_args(cls, parser):
      parser.add_argument('--input', default=None, help='Input file path or pattern')
      parser.add_argument('--output', default=None, help='Output file path')




def find_links(file):
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(file.read_utf8(), 'html.parser')

    # Find all <a> (anchor) tags in the parsed HTML
    anchor_tags = soup.find_all('a')

    # Extract and print the href attribute from each <a> tag
    hrefs = []
    for anchor_tag in anchor_tags:
        hrefs.append(anchor_tag.get('href'))

    page = file.metadata.path.split('/')[-1]

    return page, hrefs


# create pipeline
with beam.Pipeline() as p:
  beam_options = PipelineOptions()
  args = beam_options.view_as(MyOptions)
    
  #get links from files in bucket
  get_links = (p | 'MatchFiles' >> fileio.MatchFiles('gs://ds561hw2bucket/folder1/*.txt')
                | 'ReadMatches' >> fileio.ReadMatches()
                | 'FindLinks' >> beam.Map(find_links)
              )
  
  #map and count top 5 outgoing links
  outgoing_links = (get_links | 'CountLinks' >> beam.Map(lambda elem: (elem[0], len(elem[1]))))
  output = outgoing_links | 'Top5' >> beam.transforms.combiners.Top.Of(5, key=lambda x: x[1])
  output | 'Write' >> beam.io.WriteToText('gs://ds561hw2bucket/folder1/output.txt', file_name_suffix='.txt')

if __name__ == '__main__':
  p.run()