---
title: Coldcard Vulnerability: Seed Phrases Were Not Generated Randomly
description: Coldcard has admitted that some seed phrases were generated predictably rather than at random — and because of this, over $89 million has been drained from accounts that were otherwise set up correctly.
date: 2026-08-05
lang: en
slug: uyazvimost-coldcard-sid-frazy-generirovalis-ne-en
group: uyazvimost-coldcard-sid-frazy-generirovalis-ne
---

On July 30, 2026, 594 BTC — around $38 million at the time — vanished from roughly five hundred Bitcoin wallets in 25 minutes. The owners hadn't clicked phishing links, hadn't entered their seed phrase on any rogue website, and hadn't connected their devices to the internet. Some hadn't opened their wallets in months. The device holding the keys was a Coldcard, one of the most respected hardware wallets on the market, designed specifically to never touch the network.

![A single physical roll of the dice is randomness that no line of code can break.](https://anchorvaultcoin-hash.github.io/anchor-vault-blog/img/uyazvimost-coldcard-sid-frazy-generirovalis-ne.png)
*A single physical roll of the dice is randomness that no line of code can break.*

By that evening, it was clear this wasn't an isolated incident. By early August, the total had grown to $89 million across more than 4,500 addresses. The cause wasn't theft. The cause was that the seed phrases for these wallets had never been truly random in the first place.

**What happened technically**

To create a wallet, the device has to pick a random set of 12 or 24 words — the seed phrase. Everything hinges on how genuinely random that choice is: if the options can be predicted or brute-forced, the wallet is vulnerable, even if it never touched the network and the owner did everything right.

In March 2021, a bug in a single line of code slipped into the Coldcard firmware. It silently switched the device from its dedicated hardware random number generator to a software one — faster, but predictable if you know where it starts. And it started from data that wasn't secret: the chip's unique identifier and timer readings.

Coldcard's developers estimate that instead of the expected 128 bits of entropy (a number of possibilities so vast that enumerating them is impossible), devices running this firmware produced around 40 bits. This isn't a difference of degree — it's the difference between "impossible even for every computer on Earth" and "feasible on a regular gaming PC in reasonable time." The attackers appear to have used automated code analysis to find the vulnerability before the company itself did. The manufacturer, Coinkite, notes the code was always open source.

**Who's affected**

At risk are Coldcard Mk3 units running firmware versions 4.0.1–4.1.9, if the seed phrase was created without additional dice rolls (an option that adds independent randomness) and without a BIP-39 passphrase. Newer models — Mk4, Mk5, Q — use different firmware and, per the company, aren't affected by this specific bug. Wallets from other manufacturers (Trezor, Ledger) are also unaffected — they use different code, and their randomness is drawn from multiple independent sources rather than just one.

It's important to be clear: this isn't a story about "hardware wallets are a bad idea." It's a story about how even perfect user behavior — offline storage, never entering the phrase online, never showing it to anyone — doesn't protect you if the phrase itself was never random to begin with. There's no way for the user to check this: a seed phrase looks equally random regardless of how many real possibilities it was chosen from.

**What to do right now**

If you use a Coldcard, there are three verifiable steps:

Update the firmware. For Mk3, that's version 4.2.0 or newer; for Mk4/Mk5, 5.6.0+; for Q, 1.5.0Q+. Updating firmware doesn't fix an existing seed phrase — it only fixes the generator for future phrases.

Generate a new seed phrase after updating, and move your funds to it. Migrating the old phrase to new firmware doesn't help — the vulnerability wasn't in the firmware per se, but in how the phrase itself was chosen, and that can't be fixed retroactively.

If you're not sure whether you used dice rolls or a passphrase when creating the wallet — assume you didn't. The company's guidance is direct: when in doubt, move your funds. It's safer than gambling.

If you have a Ledger, Trezor, or another manufacturer — this specific vulnerability doesn't affect you.

**The core issue**

This story has an uncomfortable quality: the weakness sat silently for five years, never surfacing, until someone started deliberately hunting for holes in the open-source code. No "how to store crypto properly" checklist warned about this — there was nothing to warn about until the bug was found.

Let's be honest: this isn't a story about a stolen key, but about a key that was never genuinely random in the first place — and a second key wouldn't have helped if it was generated the same broken way. But crypto storage has another, more common problem: even a flawlessly generated key remains a single point of failure if it alone can authorize any transaction. For that second problem, the solution is simple — require a second, separately stored key to confirm large transactions, so that losing or compromising one secret doesn't automatically mean losing everything.
