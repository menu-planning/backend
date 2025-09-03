# Typeform Proxy Lambda

A lightweight AWS Lambda function that acts as a secure proxy between your private Lambda functions and the Typeform API.

## 🎯 Purpose

### The Problem
- **Main Lambda functions** are deployed in a **private VPC** for security
- **Private VPC** blocks outbound internet access (no NAT Gateway)
- **Typeform API calls** and **webhook delivery** require internet connectivity
- **NAT Gateway** costs ~$45/month + data transfer fees

### The Solution
This proxy Lambda runs in a **public subnet** and acts as a bridge:
- **Outbound**: Your private Lambdas → Proxy → Typeform API
- **Inbound**: Typeform webhooks → Proxy → Your private Lambdas
- **Cost**: ~$0.20/month (vs $45+ for NAT Gateway)

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Your Lambda   │    │  Proxy Lambda    │    │  Typeform API   │
│   (Private VPC) │───▶│  (Public Subnet) │───▶│  (Internet)     │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 💰 Cost Savings

**~$43-45/month** (95%+ cost reduction) by avoiding NAT Gateway costs.

## 🔒 Security

- **Request filtering**: Only allows specific Typeform API endpoints
- **Rate limiting**: 128KB request, 1MB response limits
- **API key protection**: Hidden from client code
- **Timeout protection**: 15-second request timeout

This solution provides secure, cost-effective internet access for your private Lambda functions without the overhead of a NAT Gateway.