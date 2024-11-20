# checks TOKEN_CONTRACT_ADDRESS balance in WALLET_ADDRESS and if nonzero, sends to RECIPIENT_ADDRESS
# NOTE: this file is not audited. Anyone with access to `secrets.env` will have full control over `WALLET_ADDRESS` (via the private key), exercise caution
# replace all <<< >>> to configure script

from dotenv import load_dotenv
import os
from web3 import Web3

#### requirements.txt
#python-dotenv
#web3

#### secrets.env
#PRIVATE_KEY=<<<insert private key>>>

#### run_script.bat (Windows)
#@echo off
#REM Navigate to the folder containing the Python script
#cd /d C:\path\to\script_folder
#
#REM Check if the virtual environment folder exists; create it if not
#if not exist venv (
#   echo Creating virtual environment...
#   python -m venv venv
#)
#
#REM Activate the virtual environment
#call venv\Scripts\activate
#
#REM Install dependencies
#pip install -r requirements.txt
#
#REM Run the Python script
#python send_all_tokens.py
#
#REM Keep the window open after execution
#pause

# if command line, first create local python environment with `python -m venv venv` and install dependencies

# config
load_dotenv(dotenv_path="secrets.env")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URL = "<<<rpc url>>>" 
WALLET_ADDRESS = "<<<wallet address>>>"  
RECIPIENT_ADDRESS = "<<<wallet address>>>" 
TOKEN_CONTRACT_ADDRESS = "<<<token contract address>>>"
CHAIN_ID = "<<<chain id>>>"
GAS = "<<<gas>>>"
GAS_PRICE = "<<<gas price>>>"

# ERC20 ABI (balanceOf, decimals, and transfer)
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": False, "stateMutability": "view", "type": "function"},
    {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "success", "type": "bool"}], "payable": False, "stateMutability": "nonpayable", "type": "function"},
]

# connect to network
web3 = Web3(Web3.HTTPProvider(RPC_URL))
if not web3.is_connected():
    print("Failed to connect to network.")
    exit()

# load the token contract
token_contract = web3.eth.contract(address=TOKEN_CONTRACT_ADDRESS, abi=ERC20_ABI)

# function to get decimals from token contract
def get_token_decimals(token_contract):
    return token_contract.functions.decimals().call()

# function to check token balance
def get_token_balance(address, decimals):
    balance = token_contract.functions.balanceOf(address).call()
    return balance / (10 ** decimals)  # Convert to human-readable format

# function to send tokens
def send_tokens(private_key, from_address, to_address, amount, decimals):
    amount_in_wei = int(amount * (10 ** decimals))  # Convert to smallest unit
    nonce = web3.eth.get_transaction_count(from_address)

    # Build transaction
    tx = token_contract.functions.transfer(to_address, amount_in_wei).build_transaction({
        'chainId': CHAIN_ID, 
        'gas': GAS,  # Estimated gas limit
        'gasPrice': web3.to_wei(GAS_PRICE, 'gwei'),  
        'nonce': nonce,
    })

    try:
        # Sign and send the transaction
        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        # Check status of the transaction
        if receipt.status == 1:
            return web3.to_hex(tx_hash), True  # Transaction successful
        else:
            return web3.to_hex(tx_hash), False  # Transaction failed
    except Exception as e:
        print(f"Error sending transaction: {e}")
        return None, False

# Main logic
decimals = get_token_decimals(token_contract)
balance = get_token_balance(WALLET_ADDRESS, decimals)

if balance == 0:
    print("No balance")
else:
    print(f"Detected balance: {balance} tokens")
    tx_hash, success = send_tokens(PRIVATE_KEY, WALLET_ADDRESS, RECIPIENT_ADDRESS, balance, decimals)
    if success:
        print(f"Sent {balance} tokens to {RECIPIENT_ADDRESS}. Transaction hash: {tx_hash}")
    elif tx_hash:
        print(f"Transaction failed. Hash: {tx_hash}")
    else:
        print("Transaction could not be sent due to an error.")
