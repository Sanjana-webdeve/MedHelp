pragma solidity ^0.8.0;

contract MedRecord {
    struct Record {
        string patientId;
        string ipfsHash;   
        address doctor;
        uint timestamp;
    }

    mapping(string => Record[]) private records;

    event RecordAdded(string patientId, address doctor, string ipfsHash, uint timestamp);

    function addRecord(string memory _patientId, string memory _ipfsHash) public {
        Record memory newRecord = Record({
            patientId: _patientId,
            ipfsHash: _ipfsHash,
            doctor: msg.sender,
            timestamp: block.timestamp
        });

        records[_patientId].push(newRecord);
        emit RecordAdded(_patientId, msg.sender, _ipfsHash, block.timestamp);
    }

    function getRecords(string memory _patientId) public view returns (Record[] memory) {
        return records[_patientId];
    }
}
