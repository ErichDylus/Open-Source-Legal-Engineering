"""
This script acts as a centralized random number oracle by using the python `random` library, and using 
`WALLET_ADDRESS' to call a function depending on the result.

NOTE: This file is not audited. Anyone with access to `secrets.env` will have full control 
over `WALLET_ADDRESS` via the private key. Exercise caution and avoid hardcoding sensitive data.

Replace all placeholders marked <<< >>> in secrets.env before running the script.

# --- requirements.txt ---
python-dotenv
web3

# --- secrets.env ---
PRIVATE_KEY=<<<insert private key>>>
RPC_URL=<<<rpc url>>>
WALLET_ADDRESS=<<<wallet address>>>
REQUESTER_ADDRESS=<<<requester address>>>
CHAIN_ID=<<<chain id>>>
GAS_LIMIT=<<<gas limit>>>
GAS_PRICE=<<<gas price>>>

# --- run_script.bat (Windows) ---
@echo off
REM Navigate to the folder containing the Python script
cd /d C:\path\to\pyoracle

REM Check if the virtual environment folder exists; create it if not
if not exist venv (
   echo Creating virtual environment...
   python -m venv venv
)

REM Activate the virtual environment
call venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt

REM Run the Python script
python rand_num_oracle.py

REM Keep the window open after execution
pause

if command line, first create local python environment with `python -m venv venv` and install dependencies
"""

from dotenv import load_dotenv
from random import randint
import os
from web3 import Web3   

# --- Load Environment Variables ---
load_dotenv(dotenv_path="secrets.env")

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URL = os.getenv("RPC_URL")  # RPC URL for the blockchain network
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")  # Sender wallet address, which must have enough gas for the txn
REQUESTER_ADDRESS = os.getenv("REQUESTER_ADDRESS")  # Contract address for the oracle response from `WALLET ADDRESS`
CHAIN_ID = int(os.getenv("CHAIN_ID"))  # Blockchain network chain ID
GAS_LIMIT = int(os.getenv("GAS_LIMIT"))  # Gas limit for transactions
GAS_PRICE = int(os.getenv("GAS_PRICE"))  # Gas price in gwei

min_value = 0 # Update as necessary
max_value = 100 # Update as necessary

# --- Requester contract ABI to return the randint, update as necessary ---
requester_abi = [
    {
        "constant": False,
        "inputs": [{"name": "randomNumber", "type": "uint256"}],
        "name": "updateRandomNumber",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

# --- Connect to Network ---
web3 = Web3(Web3.HTTPProvider(RPC_URL))
if not web3.is_connected():
    print("Failed to connect to network, check RPC_URL.")
    exit()

# --- Load the Token Contract ---
token_contract = web3.eth.contract(address=REQUESTER_ADDRESS, abi=requester_abi)

# --- Send Generated Random Number to Contract ---
def send_random_number_to_contract(random_number):
    # Initialize requester contract
    contract = web3.eth.contract(address=REQUESTER_ADDRESS, abi=requester_abi)

    # Build transaction
    nonce = web3.eth.get_transaction_count(WALLET_ADDRESS)
    tx = contract.functions.updateRandomNumber(random_number).build_transaction({
        'chainId': CHAIN_ID, 
        'gas': GAS_LIMIT,
        'gasPrice': web3.to_wei(GAS_PRICE, 'gwei'),
        'nonce': nonce
    })
    try:
        # Sign and send transaction
        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
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

# --- Main Logic ---
random_number = randint(min_value, max_value)  # Generate the random number

print(f"Generated random number: {random_number}.")  # Print before sending to the contract

tx_hash, success = send_random_number_to_contract(random_number)
if success:
    print(f"Random number: {random_number} provided to {REQUESTER_ADDRESS}. Transaction hash: {tx_hash}")
elif tx_hash:
    print(f"Transaction failed. Hash: {tx_hash}")
else:
    print("Transaction could not be sent due to an error.")

