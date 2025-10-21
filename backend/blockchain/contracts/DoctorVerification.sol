pragma solidity ^0.8.0;

contract DoctorVerification {
    struct Doctor {
        string name;
        string specialization;
        string certificateHash; 
        bool verified;
        address doctorAddress;
    }

    mapping(address => Doctor) public doctors;
    address public admin;

    event DoctorRegistered(address indexed doctor, string name);
    event DoctorVerified(address indexed doctor, bool verified);

    constructor() {
        admin = msg.sender;
    }

    function registerDoctor(
        string memory _name,
        string memory _specialization,
        string memory _certificateHash
    ) public {
        doctors[msg.sender] = Doctor({
            name: _name,
            specialization: _specialization,
            certificateHash: _certificateHash,
            verified: false,
            doctorAddress: msg.sender
        });
        emit DoctorRegistered(msg.sender, _name);
    }

    function verifyDoctor(address _doctor, bool _status) public {
        require(msg.sender == admin, "Only admin can verify doctors");
        doctors[_doctor].verified = _status;
        emit DoctorVerified(_doctor, _status);
    }

    function isDoctorVerified(address _doctor) public view returns (bool) {
        return doctors[_doctor].verified;
    }
}
