const GenuineClaims = artifacts.require("GenuineClaims");

module.exports = function (deployer) {
  deployer.deploy(GenuineClaims);
};
