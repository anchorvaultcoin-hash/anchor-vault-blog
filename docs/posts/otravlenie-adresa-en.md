---
title: Address poisoning: how copy-pasting from a wallet history cost a person $50 million.
description: He did a test transfer of $50 — all according to security protocols. Within 26 minutes, he lost 50 million. A breakdown of a real case and how to verify an address.
date: 2026-07-31
lang: en
slug: otravlenie-adresa-en
group: otravlenie-adresa
---

I'll start with a story that turns the usual security advice on its head.

![The trial translation was successful — and it was precisely this that served as the signal for the thief.](https://anchorvaultcoin-hash.github.io/anchor-vault-blog/img/otravlenie-adresa.jpg)
*The trial translation was successful — and it was precisely this that served as the signal for the thief.*

In December 2025, someone was about to transfer $50 million in USDT. They acted prudently: first sent a test amount of $50, confirmed the funds arrived, and only then sent the full sum. That's what every security guide recommends.

26 minutes after the test transfer, 49,999,950 USDT went to a thief.

## What happened in those 26 minutes

The test transfer was the trigger. The thief was watching the wallet. Seeing the test transaction, they generated an address within minutes that looked almost identical to the real one — same first characters, same last ones — and sent a tiny transaction from it to the victim's wallet.

Now the wallet's transaction history showed two entries in a row. The real recipient address and a fake one that looked like its mirror image.

The person returned to the wallet, copied the address from recent transactions — as almost everyone does — and sent the money. To the thief.

## Why this works

The mechanics are almost insultingly simple.

A blockchain address is a long string of random characters. Nobody reads the whole thing. The eye checks the beginning and the end: the first four or five characters, the last four or five. Wallets themselves are built this way — they display addresses in abbreviated form, hiding the middle behind an ellipsis.

The thief exploits exactly that. They generate an address whose beginning and end match the target. This isn't hacking, it's brute-forcing on a graphics card until a suitable combination comes up. Then they send a penny transfer — "dust" — so the address settles into your history.

Nothing more is needed. Just wait until you copy the address from history instead of taking it from a trusted source.

## It hits the cautious hardest

Here's the worst part. The FBI warned about such attacks back in April 2024 and noted something important: they work equally well against beginners and experienced users. Because they exploit not ignorance, but habit.

An experienced user is exactly the one who makes a test transfer. They copy the address from history because they trust their own recent transaction more than a letter or a message. The logic is sound — and that's precisely what sets them up.

Second case, January 2026: someone lost 4,556 ETH, about $12 million, in a routine transfer to their own deposit address. The thief had been dusting their wallet for over two months, patiently waiting for a large transaction.

In December and January alone, about $62 million was stolen this way on Ethereum.

## Why it became widespread

Previously, such attacks mostly lived on Tron: fees were negligible, and spreading dust across thousands of transactions was cheap.

In late 2025, the Fusaka upgrade on Ethereum significantly reduced fees. Mass dusting became cheap there too — and the attack moved to Ethereum.

A number that captures the scale: for 67% of new addresses, the first transaction in their history was an incoming dust transfer. Not a transfer from a friend, not a purchase — a setup for a future theft.

In total, over 225 million address poisoning attempts were recorded, with about half a billion dollars in confirmed losses.

## Little hope from the wallet

It's reasonable to expect the wallet to warn you. A study of 53 Ethereum wallets showed the opposite: 17 didn't show transaction history at all, 16 displayed fake transfers without any markings. Only three gave an explicit warning about a known poisoned address.

In other words, in the vast majority of cases, a fake entry will sit in your history exactly like a real one.

## What to do

One short rule: **never copy an address from transaction history**.

History is not an address book. It's a feed of what happened to the wallet, and anyone can write to it.

Instead:

Set up an address book in your wallet. Add the addresses you use regularly — your exchange, your second wallet, your counterparty. Take addresses from there.

If there's no address book, take the address from the original source each time anew: from the withdrawal page on the exchange, from correspondence with the recipient.

Check the entire address, not just the beginning and end. Or at least the middle — that's the part that can't be forged.

If the amount is large, split the transfer. Send a portion, wait for confirmation from the recipient that the funds arrived, and only then send the rest. Take the address for the second part from the original source again, not from history.

Dust transactions that have already arrived don't need to be touched. Don't send them back, don't try to return them — just don't use those addresses. Some wallets let you hide such entries.

## What lies beneath

All three stories share a common trait. No key was stolen, no password was cracked. People signed the transfer themselves — just to the wrong address.

As long as a single-key signature remains the final and irreversible action, the price of one careless second equals the entire balance. A scheme where a large transfer requires confirmation by a second, separate key provides what was most lacking here: a pause between the mistake and its consequences.
