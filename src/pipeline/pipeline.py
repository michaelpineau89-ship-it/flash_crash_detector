import os
import json
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions,SetupOptions
from apache_beam.transforms.window import FixedWindows

# 1. Parse the JSON and extract the price and timestamp
class ParseTradeData(beam.DoFn):
    def process(self, element):
        try:
            # Pub/Sub messages come in as bytes, so we decode them
            message = element.decode('utf-8')
            trade = json.loads(message)
            
            price = float(trade['p'])
            
            # Binance uses milliseconds ('T'), Beam needs seconds
            timestamp_sec = trade['T'] / 1000.0 
            
            # We yield a tuple: (ticker, price)
            yield beam.window.TimestampedValue((trade['s'], price), timestamp_sec)
        except Exception as e:
            logging.error(f"Error parsing message: {e}")

class CalculateWindowStats(beam.DoFn):
    # The 'window' parameter lets us grab the exact start/end time of the 1-minute bucket
    def process(self, element, window=beam.DoFn.WindowParam):
        ticker, prices = element
        
        # Convert the iterable of prices into a list
        price_list = list(prices)
        if not price_list:
            return
            
        avg_price = sum(price_list) / len(price_list)
        max_price = max(price_list)
        min_price = min(price_list)
        
        # Calculate the drop percentage from the highest price to the lowest price in this minute
        drop_pct = ((max_price - min_price) / max_price) * 100
        
        # We will define a "Flash Crash" as a drop of more than 0.25% in a single minute
        is_crash = drop_pct > 0.25 
        
        yield {
            'ticker': ticker,
            'window_start': window.start.to_utc_datetime().isoformat(),
            'window_end': window.end.to_utc_datetime().isoformat(),
            'trade_count': len(price_list),
            'avg_price': round(avg_price, 2),
            'max_price': round(max_price, 2),
            'min_price': round(min_price, 2),
            'drop_pct': round(drop_pct, 4),
            'flash_crash_detected': is_crash
        }


def run():
    PROJECT_ID = os.environ.get("PROJECT_ID", "mike-personal-portfolio")
    SUBSCRIPTION_ID = os.environ.get("SUBSCRIPTION_ID", "crypto-ticks-sub")
    SCHEMA = '''
    ticker:STRING, 
    window_start:STRING, 
    window_end:STRING, 
    trade_count:INTEGER, 
    avg_price:FLOAT, 
    max_price:FLOAT, 
    min_price:FLOAT, 
    drop_pct:FLOAT, 
    flash_crash_detected:BOOLEAN'''
    subscription_path = f"projects/{PROJECT_ID}/subscriptions/{SUBSCRIPTION_ID}"

    # Set up Beam pipeline options for streaming
    options = PipelineOptions()
    options.view_as(StandardOptions).streaming = True

    with beam.Pipeline(options=options) as p:
        (
            p 
            # 1. Read directly from your Pub/Sub subscription
            | "ReadFromPubSub" >> beam.io.ReadFromPubSub(subscription=subscription_path)
            
            # 2. Parse the JSON and attach the correct timestamp
            | "ParseJSON" >> beam.ParDo(ParseTradeData())
            
            # 3. Group the data into 1-minute fixed windows
            | "WindowIntoMinutes" >> beam.WindowInto(FixedWindows(60))
            
            # This bundles all ('BTCUSDT', price) tuples into ('BTCUSDT', [price1, price2, ...])
            | "GroupByKey" >> beam.GroupByKey()
            
            # Pass the bundled list to our math function
            | "CalculateStats" >> beam.ParDo(CalculateWindowStats())
            | "WriteToBigQuery" >> beam.io.WriteToBigQuery(
                table = f"{PROJECT_ID}:flash_crash_data.aggregated_stats",
                schema = SCHEMA,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
            )
        )

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    print("🚀 Starting local Dataflow pipeline...")

    options = PipelineOptions()
    options.view_as(StandardOptions).streaming = True

    options.view_as(SetupOptions).save_main_session = True
    
    run()