import os
import time
import requests
import pandas as pd
from web3 import Web3
import json
import logging

# ----------------------------
# Setup & Configuration
# ----------------------------

logging.basicConfig(level=logging.INFO)

INFURA_KEY = "INFURA_KEY"
BSCSCAN_API_KEY = "BSCSCAN_API_KEY"
CONTRACT_ADDRESS = '0x1e7866b5a5a4f09efd235d28d49568c2fe2f7ecd'
DECIMALS = 10**9

ETH_PROVIDER = f'https://mainnet.infura.io/v3/{INFURA_KEY}'
BSC_PROVIDER = f'https://bsc-mainnet.infura.io/v3/{INFURA_KEY}'
ABI_PATH = 'contract_abi.json'

# ----------------------------
# Web3 Setup
# ----------------------------


def load_contract(web3, abi_path, address):
    """
    Initializes and returns a Web3 contract instance.

    Args:
        web3 (Web3): The Web3 provider instance.
        abi_path (str): The ABI (Application Binary Interface) of the smart contract.
        address (str): The contract address.

    Returns:
        web3.contract.Contract: The contract object.
    """
    with open(abi_path) as f:
        abi = json.load(f)
    return web3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)


web3_eth = Web3(Web3.HTTPProvider(ETH_PROVIDER))
web3_bsc = Web3(Web3.HTTPProvider(BSC_PROVIDER))
contract_eth = load_contract(web3_eth, ABI_PATH, CONTRACT_ADDRESS)
contract_bsc = load_contract(web3_bsc, ABI_PATH, CONTRACT_ADDRESS)

# ----------------------------
# Helper Functions
# ----------------------------


def get_user_stakes(contract, address):
    """
    Fetches staking information for a specific user address.

    Args:
        contract (web3.contract.Contract): The contract object to query.
        address (str): The address to fetch stakes for.

    Returns:
        list or None: A list of stake entries or None if an error occurred.
    """
    try:
        return contract.functions.getUserStakes(address).call()
    except Exception as e:
        logging.error(f"Error fetching stakes for {address}: {e}")
        return None


def fetch_staked_addresses_eth(contract, from_block=0, to_block='latest'):
    """
    Retrieves unique addresses that participated in staking on Ethereum
    by filtering the Staked event.

    Args:
        contract (web3.contract.Contract): The Ethereum contract object.
        from_block (int): The starting block number for the event search.
        to_block (int or str): The ending block number or 'latest'.

    Returns:
        set: A set of unique user addresses who staked.
    """
    try:
        staked_filter = contract.events.Staked.create_filter(fromBlock=from_block, toBlock=to_block)
        events = staked_filter.get_all_entries()
        return {event['args']['user'] for event in events}
    except Exception as e:
        logging.error(f"Failed to fetch staked events: {e}")
        return set()


def fetch_staked_addresses_bsc(api_key, contract_address):
    """
    Retrieves staker addresses on BSC by querying BscScan
    for all transactions involving the given contract.

    Args:
        api_key (str): BscScan API key.
        contract_address (str): The smart contract address on BSC.

    Returns:
        set: A set of unique addresses that interacted with the contract.
    """
    startblock = 34181130
    all_transactions = []
    while True:
        url = (f'https://api.bscscan.com/api?module=account&action=txlist'
               f'&address={contract_address}&startblock={startblock}&sort=asc&apikey={api_key}')
        response = requests.get(url)
        txs = response.json().get('result', [])

        if not txs:
            break

        all_transactions.extend(txs)
        startblock = int(txs[-1]['blockNumber']) + 1
        if len(txs) < 10000:
            break
        time.sleep(1)

    return {tx['from'] for tx in all_transactions}


def build_staking_dataframe(contract, addresses, chain_name):
    """
    Constructs a pandas DataFrame containing staking information for a list of addresses.

    Args:
        contract (web3.contract.Contract): The contract object.
        addresses (iterable): List or set of wallet addresses.
        chain_name (str): Label to indicate the blockchain source (e.g., 'ETH' or 'BSC').

    Returns:
        pandas.DataFrame: DataFrame containing staking data per address, amount, expiration date, chain and total.
    """
    data = []
    for address in addresses:
        stakes = get_user_stakes(contract, address)
        if stakes:
            for stake in stakes:
                data.append({
                    'address': address,
                    'staking_amount': stake[0] / DECIMALS,
                    'expiration_date': stake[1]
                })

    df = pd.DataFrame(data)
    if df.empty:
        return df

    df['expiration_date'] = pd.to_datetime(df['expiration_date'], unit='s')
    df['chain'] = chain_name
    total_staked = df.groupby('address')['staking_amount'].sum().reset_index()
    total_staked.rename(columns={'staking_amount': 'total_staked_amount'}, inplace=True)
    df = df.merge(total_staked, on='address')
    return df

# ----------------------------
# Main Execution
# ----------------------------


def main():
    """
    Main execution function:
    - Fetches staker addresses and staking data from Ethereum and BSC.
    - Builds individual DataFrames for both chains.
    - Merges the results and saves the combined data to CSV.
    """
    logging.info("Fetching Ethereum stakers...")
    stakers_eth = fetch_staked_addresses_eth(contract_eth)
    df_eth = build_staking_dataframe(contract_eth, stakers_eth, 'ETH')
    logging.info(f"ETH Stakers fetched: {len(df_eth)}")

    logging.info("Fetching BSC stakers...")
    stakers_bsc = fetch_staked_addresses_bsc(BSCSCAN_API_KEY, CONTRACT_ADDRESS)
    stakers_bsc_checksum = {web3_bsc.to_checksum_address(addr) for addr in stakers_bsc}
    df_bsc = build_staking_dataframe(contract_bsc, stakers_bsc_checksum, 'BSC')
    logging.info(f"BSC Stakers fetched: {len(df_bsc)}")

    df_combined = pd.concat([df_eth, df_bsc], ignore_index=True)
    df_combined.to_csv('staking_data_combined.csv', index=False)
    logging.info("Data saved to staking_data_combined.csv")


if __name__ == "__main__":
    main()
