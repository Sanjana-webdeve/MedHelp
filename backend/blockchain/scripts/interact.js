const Web3 = require("web3");
const MedRecord = require("../build/contracts/MedRecord.json");

const init = async () => {
  const web3 = new Web3("http://127.0.0.1:7545"); 
  const id = await web3.eth.net.getId();
  const deployedNetwork = MedRecord.networks[id];
  const contract = new web3.eth.Contract(MedRecord.abi, deployedNetwork.address);

  const accounts = await web3.eth.getAccounts();
  await contract.methods.addRecord("PAT002", "QmHash456").send({ from: accounts[0] });

  const result = await contract.methods.getRecords("PAT002").call();
  console.log(result);
};

init();
