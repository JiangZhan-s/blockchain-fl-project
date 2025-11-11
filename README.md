# Blockchain-FL Project

This project is a simple implementation of a Federated Learning system empowered by Blockchain.

## Project Structure

- `blockchain/`: Contains all the blockchain-related code, including smart contracts and scripts.
  - `contracts/`: Smart contracts for the project.
    - `FederatedLearning.sol`: The main contract for coordinating the FL process.
    - `RewardToken.sol`: An ERC20 token for rewarding participants.
  - `scripts/`: Scripts for deploying and interacting with the contracts.
  - `test/`: Tests for the smart contracts.
  - `hardhat.config.js`: Configuration for the Hardhat development environment.
- `client/`: The FL client application.
  - `client.py`: The main script for the FL client.
  - `models.py`: Definitions of the machine learning models.
  - `data_loader.py`: Script for loading and preprocessing data.
  - `requirements.txt`: Python dependencies for the client.
  - `config.py`: Configuration for the client.
- `aggregator/`: The off-chain aggregator script.
  - `aggregator.py`: The script for aggregating model updates.
