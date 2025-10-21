const MedRecord = artifacts.require("MedRecord");

contract("MedRecord", (accounts) => {
  it("should add a medical record", async () => {
    const instance = await MedRecord.deployed();
    await instance.addRecord("PAT001", "QmHash123", { from: accounts[0] });
    const records = await instance.getRecords("PAT001");
    assert.equal(records.length, 1, "Record not added");
  });
});
