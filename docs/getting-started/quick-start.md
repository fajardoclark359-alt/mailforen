# Quick Start

Complete your first investigation in 5 minutes.

## Prerequisites

- mailforen installed ([Installation](installation.md))
- A suspicious `.eml` file (or use the example below)

---

## Step 1: Create a Case

```bash
mailforen case new "My-First-Investigation" \
  --target "example.com" \
  --desc "Learning mailforen workflow"
```

```
✓ Created case My-First-Investigation (ID: 1)
```

---

## Step 2: Analyze Email Headers

If you have a `.eml` file:

```bash
mailforen email headers suspicious.eml --case-id 1
```

Output includes:
- From, To, Subject, Date, Message-ID
- Received chain (hop-by-hop routing)
- Authentication-Results
- Originating IPs

### No .eml file? Create a test one:

```bash
cat > test.eml << 'EOF'
Return-Path: <attacker@phishersite.com>
Received: from mail.phishersite.com (unknown [203.0.113.100])
    by mx.victim.com (Postfix) with ESMTPS id ABC123
    for <user@victim.com>; Mon, 1 Jan 2024 10:00:00 +0000
Received: from [192.0.2.50] (helo=evil.local)
    by mail.phishersite.com with SMTP id XYZ789
    Mon, 1 Jan 2024 09:59:58 +0000
Authentication-Results: mx.victim.com; spf=fail smtp.mailfrom=phishersite.com
From: "IT Security" <security@company.com>
To: user@victim.com
Subject: URGENT: Password Reset Required
Date: Mon, 1 Jan 2024 10:00:01 +0000
Message-ID: <20240101100001.123@phishersite.com>
X-Mailer: EvilMailer 1.0

Click here to reset: https://bit.ly/fake-reset
EOF

mailforen email headers test.eml --case-id 1
```

---

## Step 3: Check Email Authentication

```bash
mailforen email auth phishersite.com --case-id 1
```

Output shows SPF, DMARC, and MX records. Risk level:
- **medium** — SPF or DMARC missing
- **low** — Both present

---

## Step 4: Investigate Infrastructure

```bash
# Domain DNS records
mailforen domain intel phishersite.com --case-id 1

# IP intelligence (from headers)
mailforen ip intel 203.0.113.100 --case-id 1

# Certificate transparency
mailforen ct search phishersite.com --case-id 1
```

---

## Step 5: Trace URLs

```bash
mailforen url trace "https://bit.ly/fake-reset" --case-id 1
```

Shows redirect chain (max 10 hops).

---

## Step 6: Generate Report

```bash
# HTML (view in browser)
mailforen report generate --case-id 1 --format html

# PDF (for evidence)
mailforen report generate --case-id 1 --format pdf

# JSON (for SIEM)
mailforen report generate --case-id 1 --format json
```

Reports saved to `~/.mailforen/reports/`.

---

## Step 7: Review Case

```bash
mailforen case show 1
```

Shows case summary with all findings, risk levels color-coded.

---

## Next Steps

- Read the [Usage Guide](../usage-guide.md) for advanced workflows
- Browse [CLI Reference](../cli-reference.md) for all commands
- See [Architecture](../architecture.md) for internals
- Check [CONTRIBUTING.md](../contributing.md) to contribute