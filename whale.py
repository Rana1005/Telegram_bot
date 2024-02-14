# from flask import Flask, jsonify
# import requests
# from bs4 import BeautifulSoup
# import re
# from flask import Flask, jsonify, request
# import threading
# from concurrent.futures import ThreadPoolExecutor
# import time

# app = Flask(__name__)

# @app.route('/get_whale', methods=['GET'])
# def get_tokens():
#     url = "https://etherscan.io/tokens"
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
#     }

#     response = requests.get(url, headers=headers)

#     if response.status_code == 200:
#         soup = BeautifulSoup(response.text, 'html.parser')

#         token_address = soup.find_all('a', class_='d-flex align-items-center gap-1 link-dark')

#         tokens_dict = {}

#         for link in token_address:
#             token_name = link.find('div', class_='hash-tag text-truncate fw-medium').text.strip()
            

#             print("for token ", token_name, '\n')            
#             raw_token_link = link['href']
#             token_link = raw_token_link.replace('/token/', '')

#             analytics_url = f'https://etherscan.io/token/generic-tokenholders2?m=light&a={token_link}'
#             analytics_response = requests.get(analytics_url, headers=headers)

#             if analytics_response.status_code == 200:
#                 analytics_soup = BeautifulSoup(analytics_response.text, 'html.parser')

#                 rows = analytics_soup.find_all('tr')[1:6]  
#                 holders_info = []
#                 for row in rows:
#                     cols = row.find_all('td')
#                     sr_no = cols[0].text.strip()
#                     holder = cols[1].text.strip()
                    
#                     holder_element = cols[1].find('a' ,class_="js-clipboard link-secondary")
#                     i_tag = holder_element.find('i', id=re.compile(r'linkIcon_addr_\d+'))
                    
#                     if str(sr_no) in i_tag['id']:
#                         address = holder_element['data-clipboard-text']
                    
#                     if holder.startswith('0') and '...' in holder:
#                             holder = address

                        
#                     quantity = cols[2].text.strip()
#                     percentage = cols[3].text.strip()
#                     value = cols[4].text.strip()

#                     holders_info.append({
#                         'sr_no': sr_no,
#                         'holder': holder,
#                         "address":address,
#                         'quantity': quantity,
#                         'percentage': percentage,
#                         'value': value
#                     })

#                 tokens_dict[token_name] = {
#                     'token_address': token_link,
#                     'holders_info': holders_info
#                 }

#         return jsonify(tokens_dict)

#     else:
#         return f"Failed to retrieve the webpage. Status code: {response.status_code}"
    
# lock = threading.Lock()

# @app.route('/api/hot_wallet/',methods=['GET'])
# def hot_wallet():
#     base_url = "https://etherscan.io/directory/Wallet/GUI_Wallets?q=&p="

#     wallet_list = []

#     for page_number in range(1, 4):  
#         url = base_url + str(page_number)
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
#         }
#         response = requests.get(url, headers=headers)
        
#         if response.status_code == 200:
#             soup = BeautifulSoup(response.text, 'html.parser')
            
#             wallet_elements = soup.find_all('a', class_='fs-5 link-dark')
            
#             for wallet_element in wallet_elements:
#                 wallet_name = wallet_element.text.strip()
#                 wallet_link = wallet_element['href']
                
#                 wallet_details = {'wallet_name': wallet_name, 'wallet_link': wallet_link}
#                 wallet_list.append(wallet_details)


#     return jsonify(wallet_list)

# @app.route('/api/cold_wallet/',methods=['GET'])
# def cold_wallet():
#     base_url = "https://etherscan.io/directory/Wallet/Hardware_Wallets"

#     wallet_list = []

    
#     url = base_url 
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
#     }
#     response = requests.get(url, headers=headers)
    
#     if response.status_code == 200:
#         soup = BeautifulSoup(response.text, 'html.parser')
        
#         wallet_elements = soup.find_all('a', class_='fs-5 link-dark')
        
#         for wallet_element in wallet_elements:
#             wallet_name = wallet_element.text.strip()
#             wallet_link = wallet_element['href']
            
#             wallet_details = {'wallet_name': wallet_name, 'wallet_link': wallet_link}
#             wallet_list.append(wallet_details)


#     return jsonify(wallet_list)

# if __name__ == '__main__':
#     app.run(debug=True)





import requests
from datetime import datetime, timedelta

# Replace 'YOUR_API_KEY' with your actual Etherscan API key
api_key = '6X94EQRQFE34M47APA48J6MUE13PVBHBRU'
wallet_address = '0xF977814e90dA44bFA03b6295A0616a897441aceC'

# Calculate the start and end timestamps for the last 30 days
end_timestamp = int(datetime.now().timestamp())
start_timestamp = int((datetime.now() - timedelta(days=30)).timestamp())

# Construct the API request to retrieve the transaction history for the last 30 days
url = f'https://api.etherscan.io/api?module=account&action=txlist&address={wallet_address}&startblock=0&endblock=99999999&sort=desc&apikey={api_key}&timestamp={start_timestamp}&endtimestamp={end_timestamp}'

# Make the API call
response = requests.get(url)

if response.status_code == 200:
    # Process the response and filter/count the transactions based on the specified types
    transactions = response.json()['result']
    print("Retrieved transactions:")

    # Initialize counters
    token_transfer_count = 0
    send_count = 0
    swap_count = 0

    # Filter transactions for the last 30 days
    transactions_last_30_days = [tx for tx in transactions if int(tx['timeStamp']) >= start_timestamp]

    # Categorize transactions and count
    for tx in transactions_last_30_days:
        input_data = tx.get('input', '0x')

        if input_data != '0x':
            token_transfer_count += 1
        elif tx['to'].lower() == wallet_address.lower() and input_data == '0x':
            send_count += 1
        elif 'Swa' in input_data.lower():
            swap_count += 1

    total_count = token_transfer_count + send_count + swap_count

    print("Token Transfer Count:", token_transfer_count)
    print("Send Count:", send_count)
    print("Swap Count:", swap_count)

    if total_count > 200:
        print(f"\nThe wallet address {wallet_address} is categorized as a Hot Wallet.")
    elif swap_count > 200:
        print(f"\nThe wallet address {wallet_address} is categorized as a Trading Wallet.")
    else:
        print(f"\nThe wallet address {wallet_address} is categorized as a Cold Wallet.")
else:
    print(f"Failed to retrieve transaction history. Status code: {response.status_code}")