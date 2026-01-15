# Fospha Walmart Connect Connector
## Product Requirements Document (PRD)

**Version:** 1.0 (Prototype)
**Date:** January 15, 2026
**Author:** Product Team
**Demo Client:** Callaway Golf

---

## Executive Summary

This document outlines the requirements for integrating Walmart Connect and Walmart Marketplace APIs into Fospha's measurement platform. The connector will enable Fospha clients to measure both their Walmart advertising performance and sales data, including unique access to Walmart's in-store attribution metrics.

### Big Idea Hypothesis

**For:** Brands selling across DTC, Amazon, and Walmart with complex omni-channel media strategies

**Who:** Need unified measurement to understand how their marketing spend influences Walmart marketplace sales

**The Walmart Connector is:** A retail media measurement capability

**That:** Measures how demand-generating media influences revenue across Walmart (online + in-store), allowing brands to optimize budgets based on true unified ROAS

**Unlike:** Manual triangulation between GA4, ad platforms, and Walmart dashboards – which obscures causality and misallocates spend

---

## 1. Integration Architecture

### 1.1 Data Sources

| Source | API | Data Type | Frequency |
|--------|-----|-----------|-----------|
| Walmart Connect | Advertising API | Campaign Performance | Daily |
| Walmart Connect | Stats API | Real-time Metrics | On-demand |
| Walmart Marketplace | Orders API | Sales Data | Daily |
| Walmart Marketplace | Reports API | Revenue Reports | Daily |

### 1.2 Authentication

Both APIs use OAuth 2.0 authentication:
- **Walmart Connect**: Client ID + Client Secret + Advertiser ID
- **Walmart Marketplace**: Client ID + Client Secret + Seller ID

### 1.3 API Endpoints

```
Walmart Connect Ads API:
├── /api/v1/stats          - Real-time performance metrics
├── /api/v1/campaigns      - Campaign management
├── /api/v1/reports/snapshot - Historical campaign data
├── /api/v1/reports/items  - Item-level reporting
└── /api/v1/reports/keywords - Keyword performance

Walmart Marketplace API:
├── /v3/orders             - Order history
├── /v3/reports            - Sales reports
└── /v3/items              - Product catalog
```

---

## 2. Data Schema

### 2.1 Advertising Data (Must Have Fields)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| activity_date | DATE | Date of activity | 2026-01-15 |
| campaign_id | TEXT | Campaign identifier | WMC-CG-SP-001 |
| campaign_name | TEXT | Campaign name | Callaway Golf - Sponsored Products |
| cost | NUMERIC | Ad spend | 2456.78 |
| impressions | INT | Total impressions | 125000 |
| clicks | INT | Total clicks | 3750 |
| market | TEXT | Market code | US |

### 2.2 Attribution Fields (Should Have)

| Field | Type | Description |
|-------|------|-------------|
| revenue | NUMERIC | Attributed revenue (14-day window) |
| conversions | INT | Attributed units sold |
| currency_code | TEXT | Currency (USD, CAD, etc.) |

### 2.3 Walmart-Specific Fields (Unique Value)

| Field | Type | Description |
|-------|------|-------------|
| in_store_attributed_sales | NUMERIC | In-store sales attributed to ads |
| online_attributed_sales | NUMERIC | Online sales attributed to ads |
| new_to_brand_sales | NUMERIC | Revenue from first-time buyers |
| new_to_brand_orders | INT | Orders from first-time buyers |

### 2.4 Fospha Integration Fields

| Field | Type | Description |
|-------|------|-------------|
| channel_group | TEXT | Fospha channel classification |
| source | TEXT | Always "walmart" |
| sales_platform | TEXT | Always "walmart" |
| is_drain | INT | Drain channel flag (1 for organic) |
| is_boost | INT | Boost channel flag (1 for ads) |

---

## 3. Channel Configuration

### 3.1 Channel Groups

| Channel Group | Type | is_drain | is_boost |
|--------------|------|----------|----------|
| Walmart Sponsored Products | Advertising | 0 | 1 |
| Walmart Sponsored Brands | Advertising | 0 | 1 |
| Walmart Sponsored Display | Advertising | 0 | 1 |
| Walmart Organic | Sales | 1 | 0 |

### 3.2 Organic Calculation

Following the Amazon Halo pattern:

```
Walmart Organic Revenue = Total Marketplace Sales - Ad-Attributed Revenue
Walmart Organic Conversions = Total Orders - Ad-Attributed Conversions
```

---

## 4. Halo Effect Measurement

### 4.1 Definition

The Walmart Halo Effect measures how DTC advertising (Meta, Google, TikTok, etc.) drives incremental sales on Walmart's marketplace.

### 4.2 Implementation

The Halo model combines:
1. DTC ad spend from existing Fospha connectors
2. Walmart marketplace sales data
3. Walmart Connect ad-attributed sales

**Unified ROAS Calculation:**
```
Unified ROAS = (DTC Revenue + Walmart Total Revenue) / (DTC Ad Spend + Walmart Ad Spend)

Halo Effect = Walmart Organic Revenue attributed to DTC advertising
```

### 4.3 Dashboard Toggle

Enable `haloToggle=true` in the Fospha dashboard URL to display unified metrics including Walmart Halo.

---

## 5. Technical Implementation

### 5.1 Daily Sync Process

1. **Authentication**: Refresh OAuth tokens
2. **Advertising Data**: Fetch campaign performance (7-day lookback)
3. **Sales Data**: Fetch order data from Marketplace API
4. **Transformation**: Convert to Fospha schema
5. **Organic Calculation**: Compute organic metrics
6. **Ingestion**: Load into Fospha data pipeline

### 5.2 Configuration Parameters

```json
{
  "fa_enabled_conversion_types": [
    {"enabled": true, "short_label": "web", "conversion_type": "web_conversions"},
    {"enabled": true, "short_label": "walmart", "conversion_type": "walmart", "conversion_column": "dda_transactions"}
  ],
  "non_nvr_sales_platform_channel_source": [
    {"sales_platform": "walmart", "channel_group": "Walmart Sponsored Brands", "source": "walmart"},
    {"sales_platform": "walmart", "channel_group": "Walmart Sponsored Products", "source": "walmart"},
    {"sales_platform": "walmart", "channel_group": "Walmart Sponsored Display", "source": "walmart"},
    {"sales_platform": "walmart", "channel_group": "Walmart Organic", "source": "walmart"}
  ]
}
```

### 5.3 Market Mapping

| Walmart Market | Country Code | Currency |
|---------------|--------------|----------|
| US | US | USD |
| Canada | CA | CAD |
| Mexico | MX | MXN |

---

## 6. Client Onboarding

### 6.1 Prerequisites

1. Active Walmart Marketplace Seller account
2. Walmart Connect Advertising account
3. API credentials from Walmart Developer Portal

### 6.2 Onboarding Steps

1. **Credential Collection**: Gather OAuth credentials from client
2. **API Access**: Verify API permissions and rate limits
3. **Connector Setup**: Configure in Fivetran or custom connector
4. **Schema Selection**: Enable required tables only
5. **Model Configuration**: Add FA parameters
6. **Dashboard Setup**: Enable Walmart channels and Halo toggle
7. **Validation**: Compare numbers with Walmart UI

### 6.3 Eligibility Criteria

- Active Walmart seller/advertiser
- Operating in US, CA, or MX markets
- Running concurrent DTC advertising campaigns
- Willing to grant API access

---

## 7. Success Metrics

| Metric | Target |
|--------|--------|
| Data Ingestion Success Rate | >98% |
| Sync Latency | <6 hours |
| Number Match with Walmart UI | 100% |
| Client Adoption (weekly login) | >80% |
| Halo Insight Actionability | >50% of clients report budget decisions |

---

## 8. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| API rate limits | Implement exponential backoff; batch requests |
| Data discrepancies | Daily reconciliation with Walmart UI |
| In-store attribution delay | Document 3-14 day lag in attribution |
| Token expiration | Automated refresh with fallback alerts |
| Multi-market complexity | Start with US; expand to CA/MX in v2 |

---

## 9. Competitive Advantage

### 9.1 Unique Differentiators

1. **In-Store Attribution**: Only Fospha will unify online and in-store sales
2. **Halo Measurement**: Cross-channel attribution to Walmart
3. **Unified Dashboard**: Walmart alongside Amazon, DTC in single view
4. **Daily Granularity**: Near real-time optimization capability

### 9.2 Market Positioning

Fospha becomes the **Total Commerce System of Record** by measuring:
- DTC (Shopify, Custom)
- Amazon (Seller/Vendor Central)
- TikTok Shop
- **Walmart** (NEW)
- Sephora (Roadmap)

---

## 10. Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Alpha | 4 weeks | Internal prototype validation |
| Closed Beta | 6 weeks | 3-5 client pilot (including Callaway Golf) |
| Open Beta | 4 weeks | Extended client access |
| General Availability | - | Full production release |

---

## 11. Resources

- [Walmart Developer Portal](https://developer.walmart.com/)
- [Walmart Connect API Documentation](https://developer.walmart.com/home/us-wmc-ads/)
- [Walmart Marketplace API](https://developer.walmart.com/home/us-mp/)
- [Fospha New Connector Checklist](notion link)
- [Fospha Amazon Halo Documentation](notion link)

---

## Appendix A: Sample API Response

### Walmart Connect Stats API

```json
{
  "advertiserId": "CG-WALMART-001",
  "asOf": "2026-01-15T17:17:52Z",
  "campaigns": [
    {
      "campaignId": "WMC-CG-SP-001",
      "campaignName": "Callaway Golf - Sponsored Products",
      "todayAdSpend": 2456.78,
      "todayImpressions": 125000,
      "todayClicks": 3750,
      "dailyBudget": 5000.00,
      "dailyRemainingBudget": 2543.22,
      "status": "ENABLED"
    }
  ]
}
```

### Fospha Transformed Output

```json
{
  "activity_date": "2026-01-15",
  "campaign_id": "WMC-CG-SP-001",
  "campaign_name": "Callaway Golf - Sponsored Products",
  "cost": 2456.78,
  "impressions": 125000,
  "clicks": 3750,
  "market": "US",
  "revenue": 18234.56,
  "conversions": 89,
  "channel_group": "Walmart Sponsored Products",
  "source": "walmart",
  "sales_platform": "walmart",
  "in_store_attributed_sales": 4567.89,
  "roas": 7.42,
  "is_drain": 0,
  "is_boost": 1
}
```

---

**Document Status:** Draft for Product Team Review
**Next Review:** Stage Gate Meeting TBD
