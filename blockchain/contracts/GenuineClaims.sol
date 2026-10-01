// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract GenuineClaims {
    struct Claim {
        uint256 claimId;
        string policyNumber;
        string claimantName;
        uint256 amountCents;
        string incidentType;
        string incidentDate;
        uint256 recordedAt;
    }

    mapping(uint256 => Claim) public claims;
    event GenuineClaimRecorded(uint256 indexed claimId, string policyNumber, uint256 recordedAt);

    function recordGenuineClaim(
        uint256 claimId,
        string calldata policyNumber,
        string calldata claimantName,
        uint256 amountCents,
        string calldata incidentType,
        string calldata incidentDate
    ) external {
        require(claims[claimId].claimId == 0, "Claim already recorded");
        claims[claimId] = Claim(claimId, policyNumber, claimantName, amountCents, incidentType, incidentDate, block.timestamp);
        emit GenuineClaimRecorded(claimId, policyNumber, block.timestamp);
    }
}
