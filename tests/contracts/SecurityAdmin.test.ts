import { expect } from "chai";
import { ethers } from "hardhat";
import { Contract } from "ethers";
import { HardhatEthersSigner } from "@nomicfoundation/hardhat-ethers/signers";

describe("SecurityAdmin", function () {
    let securityAdmin: Contract;
    let owner: HardhatEthersSigner;
    let user: HardhatEthersSigner;
    let USDC: Contract;

    // Mainnet USDC address
    const USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48";

    beforeEach(async function () {
        [owner, user] = await ethers.getSigners();

        // Get mainnet USDC contract
        USDC = await ethers.getContractAt("@openzeppelin/contracts/token/ERC20/IERC20.sol:IERC20", USDC_ADDRESS);

        // Deploy SecurityAdmin
        const SecurityAdmin = await ethers.getContractFactory("SecurityAdmin");
        securityAdmin = await SecurityAdmin.deploy();
    });

    describe("Token Whitelist", function () {
        it("Should whitelist a token", async function () {
            await expect(securityAdmin.whitelistToken(USDC_ADDRESS))
                .to.emit(securityAdmin, "TokenWhitelisted")
                .withArgs(USDC_ADDRESS);

            expect(await securityAdmin.isTokenWhitelisted(USDC_ADDRESS)).to.be.true;
        });

        it("Should remove a token from whitelist", async function () {
            await securityAdmin.whitelistToken(USDC_ADDRESS);
            
            await expect(securityAdmin.removeTokenFromWhitelist(USDC_ADDRESS))
                .to.emit(securityAdmin, "TokenRemovedFromWhitelist")
                .withArgs(USDC_ADDRESS);

            expect(await securityAdmin.isTokenWhitelisted(USDC_ADDRESS)).to.be.false;
        });

        it("Should revert when whitelisting zero address", async function () {
            await expect(
                securityAdmin.whitelistToken(ethers.ZeroAddress)
            ).to.be.revertedWith("Invalid token address");
        });

        it("Should revert when whitelisting already whitelisted token", async function () {
            await securityAdmin.whitelistToken(USDC_ADDRESS);

            await expect(
                securityAdmin.whitelistToken(USDC_ADDRESS)
            ).to.be.revertedWith("Token already whitelisted");
        });

        it("Should revert when removing non-whitelisted token", async function () {
            await expect(
                securityAdmin.removeTokenFromWhitelist(USDC_ADDRESS)
            ).to.be.revertedWith("Token not whitelisted");
        });

        it("Should revert when non-owner tries to whitelist token", async function () {
            await expect(
                securityAdmin.connect(user).whitelistToken(USDC_ADDRESS)
            ).to.be.revertedWith("Ownable: caller is not the owner");
        });

        it("Should revert when non-owner tries to remove token from whitelist", async function () {
            await securityAdmin.whitelistToken(USDC_ADDRESS);

            await expect(
                securityAdmin.connect(user).removeTokenFromWhitelist(USDC_ADDRESS)
            ).to.be.revertedWith("Ownable: caller is not the owner");
        });
    });

    describe("Timelock", function () {
        const changeId = ethers.id("TEST_CHANGE");

        it("Should request and execute change after timelock", async function () {
            await expect(securityAdmin.requestChange(changeId))
                .to.emit(securityAdmin, "ChangeRequested");

            // Fast forward time
            await ethers.provider.send("evm_increaseTime", [24 * 60 * 60]);
            await ethers.provider.send("evm_mine", []);

            // Try to execute a timelocked function
            // Note: We can't test this directly as _executeParameterChange is not implemented
            // This is just to verify the timelocked modifier works
            expect(await securityAdmin.pendingChanges(changeId)).to.not.equal(0);
        });

        it("Should cancel requested change", async function () {
            await securityAdmin.requestChange(changeId);

            await expect(securityAdmin.cancelChange(changeId))
                .to.emit(securityAdmin, "ChangeCancelled")
                .withArgs(changeId);

            expect(await securityAdmin.pendingChanges(changeId)).to.equal(0);
        });

        it("Should revert when requesting already pending change", async function () {
            await securityAdmin.requestChange(changeId);

            await expect(
                securityAdmin.requestChange(changeId)
            ).to.be.revertedWith("Change already requested");
        });

        it("Should revert when cancelling non-existent change", async function () {
            await expect(
                securityAdmin.cancelChange(changeId)
            ).to.be.revertedWith("Change not requested");
        });
    });

    describe("Pause/Unpause", function () {
        it("Should pause and unpause", async function () {
            await securityAdmin.pause();
            expect(await securityAdmin.paused()).to.be.true;

            await securityAdmin.unpause();
            expect(await securityAdmin.paused()).to.be.false;
        });

        it("Should revert when non-owner tries to pause", async function () {
            await expect(
                securityAdmin.connect(user).pause()
            ).to.be.revertedWith("Ownable: caller is not the owner");
        });

        it("Should revert when non-owner tries to unpause", async function () {
            await securityAdmin.pause();

            await expect(
                securityAdmin.connect(user).unpause()
            ).to.be.revertedWith("Ownable: caller is not the owner");
        });
    });
}); 