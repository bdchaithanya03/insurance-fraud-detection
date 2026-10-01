import json

from web3 import Web3

from backend.config import Config


def record_genuine_claim(claim_id, claim):
    if not Config.CONTRACT_ADDRESS or not Config.CONTRACT_ARTIFACT_PATH.exists():
        return None

    web3 = Web3(Web3.HTTPProvider(Config.GANACHE_RPC_URL))
    if not web3.is_connected():
        return None

    with Config.CONTRACT_ARTIFACT_PATH.open(encoding="utf-8") as artifact_file:
        artifact = json.load(artifact_file)
    contract = web3.eth.contract(
        address=Web3.to_checksum_address(Config.CONTRACT_ADDRESS),
        abi=artifact["abi"],
    )
    sender = web3.eth.accounts[0]
    transaction = contract.functions.recordGenuineClaim(
        int(claim_id),
        claim["policy_number"],
        claim["claimant_name"],
        int(round(float(claim["claim_amount"]) * 100)),
        claim["incident_type"],
        claim["incident_date"],
    ).transact({"from": sender})
    receipt = web3.eth.wait_for_transaction_receipt(transaction)
    return {
        "hash": receipt["transactionHash"].hex(),
        "block_number": receipt["blockNumber"],
    }
