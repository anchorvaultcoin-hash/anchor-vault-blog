---
title: Multisig didn't save them: how $36 million leaked from a single laptop
description: They had six keys instead of one. It was supposed to protect them. Here’s why it didn’t.
date: 2026-08-01
lang: en
slug: multisig-didnt-save-them-how-36-million-leaked-from-a-single
group: multipodpis-ne-spasla-kak-36-millionov-utekli-iz
---

If someone ever told you “switch to multisig, it’s safer” — here’s a story about why that’s only half true.

![Three of six keys lived on this laptop. One compromise, and the multisig threshold was met.](https://anchorvaultcoin-hash.github.io/anchor-vault-blog/img/multipodpis-ne-spasla-kak-36-millionov-utekli-iz.png)
*Three of six keys lived on this laptop. One compromise, and the multisig threshold was met.*

What happened

On June 9, 2026, Humanity Protocol lost over $36 million in its own token. This isn’t some fly-by-night project — Pantera Capital and Jump Crypto are behind it, and at the time it was valued at over a billion. The team did what looks like the right thing: they didn’t keep treasury keys in one place. The Ethereum multisig required a minimum of three signatures out of six. On BNB Chain, three out of five.

That’s the whole point of multisig: if one key gets stolen, it’s not enough. You’d need to steal several, ideally from different people, on different devices, in different locations. One compromised machine shouldn’t bring down the whole system.

It didn’t work. All six Ethereum keys sat on one employee’s single laptop. When that laptop was compromised, the attacker had everything needed to hit the signing threshold at once — not one key, but three. Formally, the “three out of six” condition was met. It’s just that all three came from the same source.

The attacker rewrote the bridge owner to themselves, swapped in malicious code, and drained about 141 million H tokens in one go. On BNB Chain, they repeated the trick with three out of five keys — replacing the code with a version that allowed unlimited minting and printed another 200 million tokens out of thin air.

The project’s founder later told CoinDesk that some keys accidentally ended up in a backup on that same compromised device during setup. Nobody decided to store them together — it just happened by accident in the process.

The token crashed more than 80%.

Why this isn’t a one-off

Look at the major hacks of 2026 and the pattern repeats. The Drift Protocol attack in April, $285 million — not a bug in the code, but social engineering against multisig key holders and a removed timelock on changing the signer set. CertiK’s analysts, in their first-half 2026 review, put it plainly: nearly half of all losses came from just two incidents, and both were about key management and infrastructure, not smart contract vulnerabilities.

The focus has shifted. People used to hunt for bugs in code. Now they go after the people holding the keys — and where those keys physically live.

What the real mistake was

Not the number of signatures. Three out of six is a normal, sensible scheme. The mistake was that “stored separately” and “set up separately” are not the same thing. Three keys sat in three different database fields, but physically — on one disk, behind one password, accessible to one compromised process.

Multisig protects against the theft of a single key. It can’t do anything when compromising one device hands over several keys at once. The threshold counts signatures, not where they came from.

What you can take from this

If you run any scheme with multiple keys, it’s worth checking not “how many keys” but “where they physically live and who can get more than one at a time.” One compromised laptop, one hacked cloud account, one person with access to everything — that’s not multisig anymore. That’s a single key, just sliced into pieces and stacked back in one place.

Second point: the setup process itself. Keys ended up in a backup by accident not because someone made that call, but because nobody checked after setup where everything had landed. Key separation isn’t something you configure once and it works forever. It’s something you need to re-verify by hand from time to time — are those keys actually still separate, or did six months of tweaks and backups quietly bring them back together?
