# TokenFi Cross-Chain Staking Data Aggregator

## Overview

This Python-based tool collects and consolidates staking data for the **TokenFi token** across **Ethereum** and **Binance Smart Chain (BSC)**. It interfaces with both on-chain contracts (via Web3) and external APIs (Etherscan & BscScan) to build a unified dataset of all addresses interacting with the TokenFi staking contract, and retrieves their individual staking amounts.

---

## Key Features

- **Cross-Chain Support**
  - Interacts with the TokenFi smart contract on both Ethereum and BSC networks.

- **Web3 Smart Contract Access**
  - Loads and queries smart contracts using a provided ABI.

- **Stake Data Aggregation**
  - Retrieves each user's staking amount and expiration date.
  - Consolidates data into a combined CSV file.

---

## Usage

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Configuration**
   - Ensure you have the following:
     - An `Infura` API key for Ethereum and BSC JSON-RPC endpoints.
     - A `BscScan` API key.
     - The ABI file of the TokenFi contract saved as `contract_abi.json`.

3. **Run the Script**
   ```bash
   python main.py
   ```

4. **Output**
   - The final staking data will be saved as:
     ```
     staking_data_combined.csv
     ```

---

## Requirements

- Python 3.7+
- Web3-compatible smart contract ABI
- API access to Infura and BscScan

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
