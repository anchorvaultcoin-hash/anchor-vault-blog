---
title: The collapse of multisig: why 2026 became the year of the "human factor" in crypto security
description: And how non-custodial storage is changing the game
date: 2026-08-01
lang: en
slug: krah-multipodpisi-pochemu-2026-god-stal-godom-en
group: krah-multipodpisi-pochemu-2026-god-stal-godom
---

## Introduction: The Year the Code Stopped Being the Main Target

![The collapse of multisig: why 2026 became the year of the "human factor" in crypto security](https://anchorvaultcoin-hash.github.io/anchor-vault-blog/img/krah-multipodpisi-pochemu-2026-god-stal-godom.png)

2026 will go down in crypto history as the year the most expensive bug in the system turned out to be... a human.

In the first half of 2026, the crypto industry saw 182 public security incidents with total losses of roughly $9.56 billion. On the surface, that's nearly 60% lower than the same period in 2025. But this calm is deceiving.

Why? Because the drop is entirely due to the fact that the record-breaking Bybit attack in 2025 (a $15 billion loss) wasn't repeated. In reality, the number of incidents is up 50% year-over-year. Attacks haven't weakened — they've shifted direction.

"The most expensive vulnerabilities are no longer in code, but in people," is the unanimous conclusion from the OKX Web3 Security, SlowMist, and OtterSec reports.

## Numbers That Make You Think

The average loss from a single wallet or key compromise incident in the first half of 2026 was around $13 million. For comparison: the average loss from a smart contract exploit — under $1 million.

That's a 13x difference. Hackers have clearly figured out: hacking people pays better than hacking code.

Of the $9.56 billion in losses, only 12.3% was recovered or frozen. The remaining nearly 90% of stolen funds is gone forever.

## Case #1: "Multisig on a Single Laptop" — The Humanity Protocol Lesson

June 9, 2026. Humanity Protocol, backed by Pantera Capital and Jump Crypto with a valuation of over $1 billion, lost more than $36 million of its own H tokens.

How did it happen?

Humanity Protocol used Gnosis Safe multisig wallets:

- On Ethereum: 3-of-6 keys
- On BNB Chain: 3-of-5 keys

Everything looked correct. Multisig is the gold standard of security. But there was one detail.

All six keys on Ethereum and all five keys on BNB Chain were stored on a single employee's laptop.

When that laptop was compromised, the attacker didn't get one key — they got every key needed to sign. Formally, the multisig requirements were met: 3-of-6 and 3-of-5. But those three keys belonged to one person and lived on one device.

Project founder Terence Kwok later explained: "Some of the keys were accidentally reserved on the compromised device during setup."

The result:

- 141 million H tokens stolen on Ethereum
- 200 million H tokens minted out of control on BNB Chain
- Token price crashed 80% — from nearly $1 to $0.05

As analysts rightly noted: "When one person controls enough keys to authorize transactions, the multisig security model is compromised from the start."

## Case #2: Drift Protocol — Six Months of Social Engineering

In April 2026, Drift Protocol lost $285 million.

This wasn't a code attack. It was a six-month social engineering operation.

The attackers, allegedly linked to North Korean hacker groups, spent months embedding themselves in the team's trust. They convinced one of the multisig key holders to sign a series of "harmless" transactions that didn't raise suspicion at first glance.

These transactions gradually gave the attackers control over the system. Once everything was in place — they struck.

The code was flawless. The people weren't.

## Case #3: Bybit — $1.45 Billion Through an Interface Hack

February 2025. Bybit, one of the largest crypto exchanges, lost $1.45 billion.

The attack didn't target smart contracts. The hackers compromised a Safe{Wallet} developer workstation and modified the JavaScript code on the server.

When Bybit's multisig key holders opened the interface to sign a transaction, they saw a legitimate transaction. In reality, they were signing malicious code that handed control of the wallet to the attackers.

"Multisig didn't save them because all signers used the same interface. The hacker only needed to compromise one shared point to fool everyone."

## The Big Takeaway of 2026: Multisig ≠ Security

Multisig is a tool, not a solution. And like any tool, it can be used wrong.

Analysts identify four main weaknesses in current security approaches:

**1. Blind Signing**
Signers approve what they see on screen instead of verifying what the transaction actually does. In the Bybit attack, signers thought they were approving a routine transfer.

**2. Key Concentration**
Keys are generated on internet-connected devices, held by a single founder, sent through chat apps, or held by signers sitting in the same office. One incident compromises everything.

**3. Trust in Infrastructure**
The Kelp DAO attack (a $291 million loss) didn't start with a contract vulnerability — it started with a compromised RPC, the infrastructure connecting the team to the blockchain.

**4. Single Point of Failure in the Signing Process**
When all signers use the same web interface, the same set of RPC nodes, and identical hardware wallets — a hacker only needs to break one shared point to fool everyone.

## What Does Vitalik Buterin Say?

The Ethereum co-founder, known in China as V神 ("God V"), has spoken repeatedly about wallet security. And his position isn't philosophy — it's a practical playbook.

**90% in Multisig**
Vitalik admits he keeps 90% of his crypto in a multisig wallet. He uses an m-of-n scheme — where m is the minimum number of signatures required for a transaction, and n is the total number of key holders.

**Layered Defense**
Buterin advocates for a combined strategy:

- Transaction limits — capping amounts
- Multisig — multiple approvals for large operations
- User intent verification — confirming the transaction does exactly what's intended

**Intent-Based Security**
In February 2026, Vitalik proposed a new framework:

"The user first specifies the action they want to take. The system simulates the transaction result on the blockchain. Only after reviewing the simulation does the user click 'Confirm' or 'Cancel.'"

His key point: "Security and user experience are the same thing. Both are about minimizing the gap between what the user wants to do and what the system actually does."

**Openness and Verifiability**
Vitalik also stresses the importance of open-source code. He recently demonstrated how to manage a multisig wallet through the "Read Contract" function on a block explorer, without any installed app. That's only possible because the contracts are open and verifiable.

## What This Means for You

If you hold crypto — especially significant amounts — the lessons of 2026 should change how you approach security.

**Multisig Is Not a Silver Bullet**
Multisig doesn't protect you when:

- Keys are stored in one place
- Signers use identical interfaces
- There's no independent transaction verification
- Keys are generated on internet-connected devices

**Non-Custodial Vaults Are the New Standard**
This is where non-custodial multi-asset vaults stop being a "nice option" and become a necessity.

A properly built vault:

- Separates keys physically and geographically — no "all keys on one laptop"
- Provides independent verification — each transaction is checked separately
- Doesn't rely on a single interface — multiple confirmation paths
- Has emergency mechanisms — panic withdrawal, pause protection, escrow periods
- Is audited and open-source — as with AnchorVault

## Statistics That Should Worry You

Research on hacked protocols shows: only 19% used multisig wallets, and just 2.4% relied on cold storage.

Most projects that lost billions weren't even using basic security measures.

## Conclusion: Security Is a Process, Not a Product

The most expensive mistake in crypto in 2026 is believing that multisig makes you invulnerable.

Humanity Protocol thought 3-of-6 and 3-of-5 was enough. It wasn't, because the keys were all in one place.

Bybit thought multisig would protect against any attack. It wasn't enough, because every signer saw the same compromised interface.

Drift Protocol thought code security was what mattered most. It wasn't enough, because the attack came through people.

Vitalik Buterin is right: perfect security doesn't exist. But there's layered defense, openness and verifiability, independent verification, and proper key distribution.

In 2026, the most dangerous bug in the system is the person who believes their system is secure enough.

*Data sourced from OKX Web3 Security, SlowMist, OtterSec, and QuillAudits reports, as well as CoinDesk, PANews, Odaily, and Gate.io materials from 2025-2026.* 🐕 Your AnchorVaultCoin on X: @Anchorvaultcoin
♦️ Ethereum on X: @ethereum
