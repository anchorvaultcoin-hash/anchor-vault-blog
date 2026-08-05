# AnchorVaultCoin Security Blog

Real cryptocurrency theft cases, simple explanations, and practical security lessons for crypto users.

The **AnchorVaultCoin Security Blog** covers real incidents involving stolen cryptocurrency, wallet security, phishing, scams, self-custody, custody risks, and other cryptocurrency security issues.

The purpose of the blog is to explain what happened in real cases, why users were exposed to risk, and what practical lessons can be learned from them — without unnecessary technical jargon.

## Topics

* Cryptocurrency security
* Crypto wallet security
* Self-custody
* Private-key security
* Hardware wallet security
* Phishing
* Crypto scams
* Cryptocurrency theft
* Custody and counterparty risk
* DeFi security
* Web3 security
* Smart-contract security

## AnchorVaultCoin

**AnchorVaultCoin** is a non-custodial crypto security project designed to address risks associated with a single compromised key.

The AnchorVaultCoin security model uses three separate addresses for each vault:

* **Working Key** — used for everyday operations.
* **Spare Key** — kept separately as a backup.
* **Emergency Address** — a separate destination for emergency recovery.

These addresses are intended to remain separate and serve different security purposes.

## Security Audit

AnchorVaultCoin is undergoing an independent security audit by **Hexens**.

The audit is currently in the **retest phase** following remediation of findings from the initial review.

The audit covers the defined AnchorVaultCoin smart-contract scope. The audit does not constitute a guarantee that the entire project, infrastructure, ecosystem, or user environment is free from risk.

## Official Resources

* **Official Website:** https://anchorvaultcoin-hash.github.io/anchor-vault-frontend/landing.html
* **Security Blog:** https://anchorvaultcoin-hash.github.io/anchor-vault-blog/
* **GitHub:** https://github.com/anchorvaultcoin-hash
* **X:** https://x.com/AnchorVaultCoin

## About This Blog

The blog is part of the AnchorVaultCoin project and focuses on cryptocurrency security education through real-world cases and practical explanations.

The articles are written for ordinary crypto users and are intended to make security risks easier to understand.

## How to Add an Article

Place a Markdown file in:

```text
docs/posts/
```

Then run:

```bash
python3 tools/blog_build.py
```

Commit and push the changes.

The build process automatically generates:

* HTML pages
* Article list
* RSS feed
* Sitemap

Each article contains its title, description, publication date, and page address at the beginning of the Markdown file.

## Repository Structure

```text
docs/posts/           Blog articles
tools/blog_build.py   Blog builder
```

The generated website is published through GitHub Pages.
