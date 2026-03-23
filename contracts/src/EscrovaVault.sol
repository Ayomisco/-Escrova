// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title EscrovaVault
 * @notice Trustless AI-arbitrated escrow on Celo.
 *         Gas paid in cUSD — no native CELO token required by agents.
 *         Arbiter (Escrova agent) resolves disputes using AI reasoning.
 */
contract EscrovaVault is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;

    // ── Enums ──────────────────────────────────────────────────
    enum EscrowStatus {
        OPEN,       // Created, awaiting funding
        FUNDED,     // cUSD deposited, work in progress
        COMPLETED,  // Buyer confirmed, payment released
        DISPUTED,   // Dispute raised, awaiting arbitration
        RESOLVED,   // Arbiter resolved dispute
        REFUNDED    // Deadline passed, buyer refunded
    }

    // ── Structs ────────────────────────────────────────────────
    struct Escrow {
        uint256 id;
        address buyer;
        address seller;
        address arbiter;           // Escrova agent address
        address token;             // cUSD address
        uint256 amount;            // cUSD amount (18 decimals)
        uint256 platformFee;       // 1% fee to sustain agent operations
        uint256 deadline;          // Unix timestamp — seller must deliver by this
        string  criteria;          // Plain English work criteria (stored on-chain)
        string  deliveryHash;      // IPFS hash of delivered work (set by seller)
        EscrowStatus status;
        uint256 createdAt;
        uint256 resolvedAt;
        bool    sellerWins;        // Set by arbiter in RESOLVED state
    }

    // ── State ──────────────────────────────────────────────────
    uint256 public escrowCount;
    mapping(uint256 => Escrow) public escrows;
    mapping(address => uint256[]) public buyerEscrows;
    mapping(address => uint256[]) public sellerEscrows;

    address public platformWallet;  // Receives 1% fee (funds agent compute)
    uint256 public constant FEE_BPS = 100; // 1% in basis points
    uint256 public constant BPS_DENOM = 10000;

    // ── Events ────────────────────────────────────────────────
    event EscrowCreated(uint256 indexed id, address indexed buyer, address indexed seller, uint256 amount, string criteria);
    event EscrowFunded(uint256 indexed id, uint256 amount);
    event DeliverySubmitted(uint256 indexed id, string deliveryHash);
    event EscrowCompleted(uint256 indexed id, address seller, uint256 amount);
    event EscrowDisputed(uint256 indexed id, address raisedBy);
    event EscrowResolved(uint256 indexed id, bool sellerWins, string reasoning);
    event EscrowRefunded(uint256 indexed id, address buyer, uint256 amount);

    // ── Constructor ───────────────────────────────────────────
    constructor(address _platformWallet) Ownable(msg.sender) {
        platformWallet = _platformWallet;
    }

    // ── Create escrow ─────────────────────────────────────────
    /**
     * @notice Create a new escrow. Call approve(cUSD, amount) before this.
     * @param seller The address who will deliver the work
     * @param arbiter The Escrova agent address (resolves disputes)
     * @param token cUSD token address on Celo
     * @param amount Amount in cUSD (18 decimals) — e.g. 10 cUSD = 10e18
     * @param deadlineSeconds Seconds from now until delivery deadline
     * @param criteria Plain English description of what constitutes completion
     */
    function createAndFund(
        address seller,
        address arbiter,
        address token,
        uint256 amount,
        uint256 deadlineSeconds,
        string calldata criteria
    ) external nonReentrant returns (uint256 escrowId) {
        require(seller != address(0) && seller != msg.sender, "Invalid seller");
        require(arbiter != address(0), "Invalid arbiter");
        require(amount > 0, "Amount must be > 0");
        require(deadlineSeconds >= 3600, "Deadline must be >= 1 hour");
        require(bytes(criteria).length > 0, "Criteria required");

        uint256 fee = (amount * FEE_BPS) / BPS_DENOM;
        uint256 totalRequired = amount + fee;

        escrowId = ++escrowCount;

        escrows[escrowId] = Escrow({
            id: escrowId,
            buyer: msg.sender,
            seller: seller,
            arbiter: arbiter,
            token: token,
            amount: amount,
            platformFee: fee,
            deadline: block.timestamp + deadlineSeconds,
            criteria: criteria,
            deliveryHash: "",
            status: EscrowStatus.FUNDED,
            createdAt: block.timestamp,
            resolvedAt: 0,
            sellerWins: false
        });

        buyerEscrows[msg.sender].push(escrowId);
        sellerEscrows[seller].push(escrowId);

        // Transfer total (amount + fee) from buyer
        IERC20(token).safeTransferFrom(msg.sender, address(this), totalRequired);

        emit EscrowCreated(escrowId, msg.sender, seller, amount, criteria);
        emit EscrowFunded(escrowId, totalRequired);
    }

    // ── Seller: submit delivery ───────────────────────────────
    /**
     * @notice Seller submits proof of work delivery (IPFS hash or URL hash)
     */
    function submitDelivery(uint256 escrowId, string calldata deliveryHash) external {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.seller, "Only seller");
        require(e.status == EscrowStatus.FUNDED, "Wrong status");
        require(block.timestamp <= e.deadline, "Deadline passed");
        require(bytes(deliveryHash).length > 0, "Delivery hash required");

        e.deliveryHash = deliveryHash;
        emit DeliverySubmitted(escrowId, deliveryHash);
    }

    // ── Buyer: confirm completion ─────────────────────────────
    /**
     * @notice Buyer confirms work is done. Releases payment to seller.
     */
    function confirmComplete(uint256 escrowId) external nonReentrant {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.buyer, "Only buyer");
        require(e.status == EscrowStatus.FUNDED, "Wrong status");
        require(bytes(e.deliveryHash).length > 0, "No delivery submitted yet");

        e.status = EscrowStatus.COMPLETED;
        e.resolvedAt = block.timestamp;

        // Release to seller
        IERC20(e.token).safeTransfer(e.seller, e.amount);
        // Fee to platform
        IERC20(e.token).safeTransfer(platformWallet, e.platformFee);

        emit EscrowCompleted(escrowId, e.seller, e.amount);
    }

    // ── Buyer or Seller: raise dispute ────────────────────────
    /**
     * @notice Either party can raise a dispute after delivery is submitted.
     *         The Escrova arbiter will then resolve it.
     */
    function raiseDispute(uint256 escrowId) external {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.buyer || msg.sender == e.seller, "Only parties");
        require(e.status == EscrowStatus.FUNDED, "Wrong status");

        e.status = EscrowStatus.DISPUTED;
        emit EscrowDisputed(escrowId, msg.sender);
    }

    // ── Arbiter (Escrova agent): resolve dispute ──────────────
    /**
     * @notice Only the Escrova arbiter agent can call this.
     *         sellerWins=true → pay seller. sellerWins=false → refund buyer.
     *         reasoning is stored on-chain for transparency.
     */
    function resolveDispute(
        uint256 escrowId,
        bool sellerWins,
        string calldata reasoning
    ) external nonReentrant {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.arbiter, "Only arbiter");
        require(e.status == EscrowStatus.DISPUTED, "Not disputed");
        require(bytes(reasoning).length > 0, "Reasoning required");

        e.status = EscrowStatus.RESOLVED;
        e.resolvedAt = block.timestamp;
        e.sellerWins = sellerWins;

        if (sellerWins) {
            IERC20(e.token).safeTransfer(e.seller, e.amount);
        } else {
            IERC20(e.token).safeTransfer(e.buyer, e.amount);
        }
        // Fee to platform in both cases (arbiter worked)
        IERC20(e.token).safeTransfer(platformWallet, e.platformFee);

        emit EscrowResolved(escrowId, sellerWins, reasoning);
    }

    // ── Buyer: claim refund after deadline ────────────────────
    /**
     * @notice If seller misses deadline and no delivery, buyer gets full refund.
     */
    function claimRefund(uint256 escrowId) external nonReentrant {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.buyer, "Only buyer");
        require(e.status == EscrowStatus.FUNDED, "Wrong status");
        require(block.timestamp > e.deadline, "Deadline not passed");
        require(bytes(e.deliveryHash).length == 0, "Delivery was submitted - raise dispute instead");

        e.status = EscrowStatus.REFUNDED;
        e.resolvedAt = block.timestamp;

        // Full refund including fee (seller didn't deliver)
        IERC20(e.token).safeTransfer(e.buyer, e.amount + e.platformFee);

        emit EscrowRefunded(escrowId, e.buyer, e.amount + e.platformFee);
    }

    // ── View helpers ──────────────────────────────────────────
    function getEscrow(uint256 escrowId) external view returns (Escrow memory) {
        return escrows[escrowId];
    }

    function getBuyerEscrows(address buyer) external view returns (uint256[] memory) {
        return buyerEscrows[buyer];
    }

    function getSellerEscrows(address seller) external view returns (uint256[] memory) {
        return sellerEscrows[seller];
    }

    function setPlatformWallet(address newWallet) external onlyOwner {
        platformWallet = newWallet;
    }
}
