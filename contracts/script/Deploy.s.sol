// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console} from "forge-std/Script.sol";
import {EscrovaVault} from "../src/EscrovaVault.sol";

contract DeployScript is Script {
    function run() external {
        uint256 deployerKey = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address agentWallet = vm.envAddress("AGENT_WALLET_ADDRESS");

        vm.startBroadcast(deployerKey);

        // Platform wallet = agent wallet (1% fee funds agent compute costs)
        EscrovaVault vault = new EscrovaVault(agentWallet);

        console.log("EscrovaVault deployed:", address(vault));
        console.log("Platform wallet (agent):", agentWallet);
        console.log("Chain ID:", block.chainid);

        vm.stopBroadcast();

        console.log("\n=== ADD TO .env ===");
        console.log("ESCROVA_CONTRACT_ADDRESS=", address(vault));
    }
}
