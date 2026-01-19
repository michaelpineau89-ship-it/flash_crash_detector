import requests
import sys
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_alpha_vantage(api_key, symbol="IBM"):
    """
    Core logic to fetch data from Alpha Vantage.
    Returns: (bool, dict) -> (Success/Fail, Response Data or Error)
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
    sanitized_url = url.split('&apikey')[0] + "&apikey=***"
    
    logging.info(f"📡 Attempting connection to: {sanitized_url}")

    try:
        response = requests.get(url, timeout=10)
        
        # 1. HTTP Protocol Check
        if response.status_code != 200:
            logging.error(f"❌ HTTP Error: {response.status_code}")
            return False, {"error": f"HTTP {response.status_code}"}
            
        data = response.json()
        
        # 2. API Logic Check
        if "Global Quote" in data:
            quote = data["Global Quote"]
            logging.info(f"✅ SUCCESS: {symbol} Price: ${quote.get('05. price', 'N/A')}")
            return True, data
            
        elif "Note" in data:
            logging.warning(f"⚠️  Rate Limit Reached: {data['Note']}")
            return True, data # Still counts as network success
            
        else:
            logging.error(f"❌ API Error: Unexpected response structure: {data}")
            return False, data

    except requests.exceptions.ConnectionError:
        logging.critical("❌ NETWORK FAILURE: DNS or Firewall blocking connection.")
        return False, {"error": "ConnectionError"}
        
    except Exception as e:
        logging.error(f"❌ UNKNOWN ERROR: {e}")
        return False, {"error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smoke Test for Alpha Vantage API Connectivity")
    parser.add_argument("--api_key", required=True, help="Your Alpha Vantage API Key")
    args = parser.parse_args()
    
    success, _ = check_alpha_vantage(args.api_key)
    
    if not success:
        sys.exit(1)