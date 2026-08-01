---
title: Multisignature didn't save the day: how $36 million leaked because of a single laptop.
description: They had six keys instead of one. That was supposed to provide protection. Let's break down why it didn't.
date: 2026-08-01
lang: en
slug: multipodpis-ne-spasla-kak-36-millionov-utekli-iz-en
group: multipodpis-ne-spasla-kak-36-millionov-utekli-iz
---

If you've ever been told "switch to multisig, it's safer" — here's a story about why that's only half true.

![Three of the six keys were stored on this laptop. One breach, and the multisig threshold was crossed.](https://anchorvaultcoin-hash.github.io/anchor-vault-blog/img/multipodpis-ne-spasla-kak-36-millionov-utekli-iz.png)
*Three of the six keys were stored on this laptop. One breach, and the multisig threshold was crossed.*

What happened

On June 9, 2026, the Humanity Protocol project had over $36 million stolen in their own token. This isn't a fly-by-night project — it's backed by Pantera Capital and Jump Crypto, with a valuation north of a billion at the time. The team did what's considered the right thing: they didn't keep treasury keys in one place. The Ethereum multisig required at least three signatures out of six. On BNB Chain — three out of five.

The whole point of multisig is this: if one key gets stolen, that's not enough. You need to steal several, ideally from different people, on different devices, in different locations. One compromised machine shouldn't bring down the whole system.

It didn't work. All six keys on Ethereum sat on a single laptop belonging to one employee. When that laptop was hacked, the attacker had everything needed to meet the signing threshold at once — not one key, but three. Formally, the "three out of six" condition was met. It's just that all three came from a single source.

The attacker reassigned the bridge owner to themselves, swapped the code for a malicious version, and drained about 141 million H tokens in one go. On BNB Chain, they repeated the same trick with three out of five keys — there, the code was replaced with a version allowing unlimited minting, and another 200 million tokens were printed out of thin air.

The project's founder later explained to CoinDesk that some keys accidentally ended up in a backup on that same compromised device during setup. No one decided to store them together — it just happened, by accident in the process.

The token crashed by more than 80%.

Why this isn't an isolated case

Looking at the major hacks of 2026, the pattern repeats. The attack on Drift Protocol in April, $285 million — again, not a bug in the code, but social engineering against multisig key holders and a removed timelock on changing the signer set. CertiK analysts, summarizing the first half of 2026, state plainly: nearly half of all losses came from just two incidents, and both were about key management and infrastructure, not smart contract vulnerabilities.

The focus is shifting. Previously, people looked for bugs in code. Now, more often than not, they go after the people holding those keys — and where those keys physically reside.

What the real mistake was

Not the number of signatures. Three out of six is a normal, sensible scheme. The mistake was that "storing separately" and "setting up separately" are not the same thing. Three keys sat in three different database fields, but physically — on one disk, behind one password, accessible to one compromised process.

Multisig protects against the theft of a single key. It can do nothing if the theft of one device yields several keys at once. The threshold counts signatures, not where they came from.

What you can take away from this

If you have some scheme with multiple keys, it's worth checking not "how many keys" but "where they physically sit and who can get more than one at a time." One compromised laptop, one hacked cloud account, one person with access to everything — that's no longer multisig, that's a single key, just sliced into pieces and stacked back together in one place.

The second point is about the setup process itself. The keys ended up in a backup by accident not because someone made that decision, but because no one checked after setup where everything had landed. Key separation isn't something you configure once and it works forever. It's something you need to re-verify by hand from time to time: are these keys actually still separate, or after six months of tweaks and backups have they quietly ended up side by side again.
