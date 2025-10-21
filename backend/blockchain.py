from web3 import Web3
import json

ganache_url = "http://127.0.0.1:7545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

with open("blockchain/build/contracts/MedRecord.json") as f:
    med_record_artifact = json.load(f)

contract_address = med_record_artifact["networks"]["5777"]["address"]
abi = med_record_artifact["abi"]
contract = web3.eth.contract(address=contract_address, abi=abi)

def add_med_record(patient_id, ipfs_hash, sender_address, private_key):
    nonce = web3.eth.getTransactionCount(sender_address)
    txn = contract.functions.addRecord(patient_id, ipfs_hash).build_transaction({
        'from': sender_address,
        'nonce': nonce,
        'gas': 3000000,
        'gasPrice': web3.to_wei('20', 'gwei')
    })
    signed_txn = web3.eth.account.sign_transaction(txn, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return web3.to_hex(tx_hash)
