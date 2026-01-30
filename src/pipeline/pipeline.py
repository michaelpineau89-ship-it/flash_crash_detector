import argparse
import json
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

# ---------------------------------------------------------
# 1. PARSING: Turn Pub/Sub bytes into a Dictionary
# ---------------------------------------------------------
class ParseJson(beam.DoFn):
    def process(self, element):
        try:
            # Pub/Sub messages come in as bytes
            yield json.loads(element.decode('utf-8'))
        except Exception as e:
            logging.error(f"Could not parse JSON: {e}")

# ---------------------------------------------------------
# 2. ANALYSIS: The "Business Logic"
# (For now, we just pass it through, but this is where math goes)
# ---------------------------------------------------------
class DetectCrash(beam.DoFn):
    def process(self, element):
        # TODO: Add complex windowing/stateful logic here.
        # For now, we just flag everything so we can see data flowing.
        element['processing_status'] = 'processed'
        yield element

# ---------------------------------------------------------
# 3. THE PIPELINE
# ---------------------------------------------------------
def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_subscription', required=True, help='Pub/Sub Subscription')
    parser.add_argument('--output_table', required=True, help='BigQuery Table: project:dataset.table')
    
    known_args, pipeline_args = parser.parse_known_args(argv)
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(StandardOptions).streaming = True

    with beam.Pipeline(options=pipeline_options) as p:
        (
            p
            | "ReadFromPubSub" >> beam.io.ReadFromPubSub(subscription=known_args.input_subscription)
            | "ParseJSON" >> beam.ParDo(ParseJson())
            | "DetectCrash" >> beam.ParDo(DetectCrash())
            | "WriteToBigQuery" >> beam.io.WriteToBigQuery(
                known_args.output_table,
                schema="symbol:STRING, price:FLOAT, timestamp:STRING, processing_status:STRING",
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
            )
        )

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()