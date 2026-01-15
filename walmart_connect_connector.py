"""
Fospha Walmart Connect Connector Prototype
==========================================
This module demonstrates how Fospha can integrate with Walmart Connect APIs
to pull both advertising and sales data for retail media measurement.

Designed for Callaway Golf as the example client.

Author: Fospha Product Team
Date: January 2026
"""

import json
import hashlib
import hmac
import base64
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import random


# ==============================================================================
# CONFIGURATION & AUTHENTICATION
# ==============================================================================

class WalmartAPIEnvironment(Enum):
    """Walmart API environments"""
    SANDBOX = "sandbox"
    PRODUCTION = "production"


@dataclass
class WalmartConnectCredentials:
    """OAuth 2.0 credentials for Walmart Connect API"""
    client_id: str
    client_secret: str
    advertiser_id: str
    environment: WalmartAPIEnvironment = WalmartAPIEnvironment.PRODUCTION

    # OAuth tokens (populated after authentication)
    access_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None

    @property
    def is_token_valid(self) -> bool:
        """Check if current token is still valid"""
        if not self.access_token or not self.token_expires_at:
            return False
        return datetime.utcnow() < self.token_expires_at - timedelta(minutes=5)


@dataclass
class WalmartMarketplaceCredentials:
    """Credentials for Walmart Marketplace API (Sales Data)"""
    client_id: str
    client_secret: str
    seller_id: str
    environment: WalmartAPIEnvironment = WalmartAPIEnvironment.PRODUCTION

    access_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


# ==============================================================================
# DATA MODELS - Aligned with Fospha Schema Requirements
# ==============================================================================

@dataclass
class WalmartAdPerformanceData:
    """
    Walmart Connect Advertising Performance Data
    Maps to Fospha's ad platform connector schema

    Reference: Fospha New Connector Development Checklist
    - Must Have: Date, Campaign Name, Campaign ID, Cost, Impressions, Clicks, Market
    - Should Have: Revenue, Conversions, Currency Code
    - Good to Have: Ad set-level granularity, Additional cost metrics
    """
    # Required Fields (Must Have)
    activity_date: str  # DATE - Date of advertising activity
    campaign_id: str    # TEXT - Campaign identifier
    campaign_name: str  # TEXT - Campaign name
    cost: float         # NUMERIC - Ad spend (gross)
    impressions: int    # NUMERIC - Total impressions
    clicks: int         # NUMERIC - Total clicks
    market: str         # TEXT - Advertiser market (e.g., 'US')

    # Should Have Fields
    revenue: float = 0.0           # NUMERIC - Attributed revenue (14-day window)
    conversions: int = 0           # NUMERIC - Attributed units sold
    currency_code: str = "USD"     # TEXT - Currency

    # Good to Have Fields
    ad_group_id: Optional[str] = None
    ad_group_name: Optional[str] = None
    ad_id: Optional[str] = None
    keyword: Optional[str] = None

    # Walmart-Specific Metrics
    in_store_attributed_sales: float = 0.0
    online_attributed_sales: float = 0.0
    new_to_brand_sales: float = 0.0
    new_to_brand_orders: int = 0

    # Calculated Metrics
    ctr: float = 0.0              # Click-through rate
    cpc: float = 0.0              # Cost per click
    roas: float = 0.0             # Return on ad spend

    # Fospha Integration Fields
    channel_group: str = "Walmart Connect"
    source: str = "walmart"
    sales_platform: str = "walmart"

    def __post_init__(self):
        """Calculate derived metrics"""
        if self.impressions > 0:
            self.ctr = (self.clicks / self.impressions) * 100
        if self.clicks > 0:
            self.cpc = self.cost / self.clicks
        if self.cost > 0:
            self.roas = self.revenue / self.cost


@dataclass
class WalmartSalesData:
    """
    Walmart Marketplace Sales Data
    Maps to Fospha's sales channel connector schema

    Reference: Amazon Seller Central connector pattern
    """
    activity_date: str
    profile: str              # Seller/Vendor ID
    country: str              # Market code (US, CA, etc.)
    sales_platform: str = "walmart"
    channel_group: str = "Walmart Organic"
    source: str = "walmart"

    # Sales Metrics
    conversions: int = 0      # Total orders
    revenue: float = 0.0      # Total sales revenue
    units_sold: int = 0       # Total units
    currency_code: str = "USD"

    # Order Details
    order_count: int = 0
    average_order_value: float = 0.0

    def __post_init__(self):
        if self.conversions > 0:
            self.average_order_value = self.revenue / self.conversions


@dataclass
class WalmartHaloData:
    """
    Combined data for Halo Effect measurement
    Similar to Fospha's Amazon Halo model

    Halo Effect = How DTC advertising (Meta, TikTok, Google)
    drives sales on Walmart marketplace
    """
    activity_date: str
    market: str

    # DTC Ad Metrics (from Fospha's existing connectors)
    dtc_ad_spend: float = 0.0
    dtc_impressions: int = 0
    dtc_clicks: int = 0

    # Walmart Metrics
    walmart_ad_spend: float = 0.0
    walmart_revenue: float = 0.0
    walmart_organic_revenue: float = 0.0

    # Calculated Halo Metrics
    total_walmart_revenue: float = 0.0
    unified_roas: float = 0.0
    halo_effect_revenue: float = 0.0


# ==============================================================================
# API CLIENT IMPLEMENTATIONS
# ==============================================================================

class WalmartConnectAPIClient:
    """
    Walmart Connect Advertising API Client

    Based on Walmart Developer Portal documentation:
    - Stats API: Near real-time performance metrics
    - Snapshot Reports API: Historical campaign data
    - Campaign Management API: Campaign CRUD operations
    """

    BASE_URL = "https://advertising.api.walmart.com"
    AUTH_URL = "https://marketplace.walmartapis.com/v3/token"

    # API Endpoints
    ENDPOINTS = {
        "stats": "/api/v1/stats",
        "campaigns": "/api/v1/campaigns",
        "snapshot_reports": "/api/v1/reports/snapshot",
        "item_reports": "/api/v1/reports/items",
        "keyword_reports": "/api/v1/reports/keywords"
    }

    def __init__(self, credentials: WalmartConnectCredentials):
        self.credentials = credentials

    def authenticate(self) -> bool:
        """
        OAuth 2.0 authentication flow

        Production implementation would:
        1. POST to AUTH_URL with client credentials
        2. Receive access_token and expires_in
        3. Store token for subsequent requests
        """
        # Simulated authentication for prototype
        print(f"[AUTH] Authenticating with Walmart Connect API...")
        print(f"[AUTH] Client ID: {self.credentials.client_id[:8]}...")
        print(f"[AUTH] Advertiser ID: {self.credentials.advertiser_id}")

        # In production, this would be an actual OAuth call
        self.credentials.access_token = f"simulated_token_{int(time.time())}"
        self.credentials.token_expires_at = datetime.utcnow() + timedelta(hours=1)

        print(f"[AUTH] Authentication successful. Token expires at {self.credentials.token_expires_at}")
        return True

    def get_campaign_performance(
        self,
        start_date: str,
        end_date: str,
        granularity: str = "daily"
    ) -> List[WalmartAdPerformanceData]:
        """
        Fetch campaign performance data from Walmart Connect

        Uses Snapshot Reports API for historical data
        API Endpoint: GET /api/v1/reports/snapshot

        Parameters:
        - start_date: YYYY-MM-DD
        - end_date: YYYY-MM-DD
        - granularity: daily, weekly, monthly
        """
        if not self.credentials.is_token_valid:
            self.authenticate()

        print(f"\n[API] Fetching campaign performance data...")
        print(f"[API] Date range: {start_date} to {end_date}")
        print(f"[API] Endpoint: {self.BASE_URL}{self.ENDPOINTS['snapshot_reports']}")

        # Simulated API response for Callaway Golf
        # In production, this would be: requests.get(url, headers=headers, params=params)
        return self._generate_sample_ad_data(start_date, end_date)

    def get_realtime_stats(self) -> Dict[str, Any]:
        """
        Fetch near real-time statistics

        Uses Stats API - provides today's metrics
        API Endpoint: GET /api/v1/stats

        Returns: todayAdSpend, todayImpressions, todayClicks, remainingBudget
        """
        if not self.credentials.is_token_valid:
            self.authenticate()

        print(f"\n[API] Fetching real-time stats...")
        print(f"[API] Endpoint: {self.BASE_URL}{self.ENDPOINTS['stats']}")

        # Simulated real-time stats
        return {
            "advertiserId": self.credentials.advertiser_id,
            "asOf": datetime.utcnow().isoformat(),
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
                },
                {
                    "campaignId": "WMC-CG-SB-001",
                    "campaignName": "Callaway Golf - Sponsored Brands",
                    "todayAdSpend": 1234.56,
                    "todayImpressions": 85000,
                    "todayClicks": 2125,
                    "dailyBudget": 3000.00,
                    "dailyRemainingBudget": 1765.44,
                    "status": "ENABLED"
                }
            ]
        }

    def _generate_sample_ad_data(
        self,
        start_date: str,
        end_date: str
    ) -> List[WalmartAdPerformanceData]:
        """Generate sample advertising data for Callaway Golf demo"""

        campaigns = [
            ("WMC-CG-SP-001", "Callaway Golf - Sponsored Products", "Walmart Sponsored Products"),
            ("WMC-CG-SB-001", "Callaway Golf - Sponsored Brands", "Walmart Sponsored Brands"),
            ("WMC-CG-SD-001", "Callaway Golf - Sponsored Display", "Walmart Sponsored Display"),
        ]

        data = []
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current = start

        while current <= end:
            for campaign_id, campaign_name, channel_group in campaigns:
                # Generate realistic-looking metrics
                base_spend = random.uniform(800, 2500)
                base_impressions = int(random.uniform(40000, 120000))
                ctr = random.uniform(0.025, 0.045)
                clicks = int(base_impressions * ctr)
                conversion_rate = random.uniform(0.08, 0.15)
                conversions = int(clicks * conversion_rate)
                aov = random.uniform(85, 250)  # Golf equipment AOV
                revenue = conversions * aov

                # In-store attribution (unique to Walmart)
                in_store_ratio = random.uniform(0.15, 0.35)
                in_store_sales = revenue * in_store_ratio

                data.append(WalmartAdPerformanceData(
                    activity_date=current.strftime("%Y-%m-%d"),
                    campaign_id=campaign_id,
                    campaign_name=campaign_name,
                    cost=round(base_spend, 2),
                    impressions=base_impressions,
                    clicks=clicks,
                    market="US",
                    revenue=round(revenue, 2),
                    conversions=conversions,
                    channel_group=channel_group,
                    in_store_attributed_sales=round(in_store_sales, 2),
                    online_attributed_sales=round(revenue - in_store_sales, 2),
                    new_to_brand_sales=round(revenue * random.uniform(0.2, 0.4), 2),
                    new_to_brand_orders=int(conversions * random.uniform(0.2, 0.4))
                ))

            current += timedelta(days=1)

        return data


class WalmartMarketplaceAPIClient:
    """
    Walmart Marketplace API Client for Sales Data

    Based on Walmart Developer Portal documentation:
    - Orders API: Order history and details
    - Reports API: Sales and performance reports
    """

    BASE_URL = "https://marketplace.walmartapis.com"

    ENDPOINTS = {
        "orders": "/v3/orders",
        "reports": "/v3/reports",
        "items": "/v3/items"
    }

    def __init__(self, credentials: WalmartMarketplaceCredentials):
        self.credentials = credentials

    def authenticate(self) -> bool:
        """OAuth 2.0 authentication for Marketplace API"""
        print(f"[AUTH] Authenticating with Walmart Marketplace API...")
        print(f"[AUTH] Seller ID: {self.credentials.seller_id}")

        self.credentials.access_token = f"mp_token_{int(time.time())}"
        self.credentials.token_expires_at = datetime.utcnow() + timedelta(hours=1)

        print(f"[AUTH] Marketplace authentication successful.")
        return True

    def get_sales_data(
        self,
        start_date: str,
        end_date: str
    ) -> List[WalmartSalesData]:
        """
        Fetch sales data from Walmart Marketplace

        API Endpoint: GET /v3/orders with date range
        Returns aggregated daily sales metrics
        """
        if not self.credentials.access_token:
            self.authenticate()

        print(f"\n[API] Fetching sales data from Walmart Marketplace...")
        print(f"[API] Date range: {start_date} to {end_date}")

        return self._generate_sample_sales_data(start_date, end_date)

    def _generate_sample_sales_data(
        self,
        start_date: str,
        end_date: str
    ) -> List[WalmartSalesData]:
        """Generate sample sales data for Callaway Golf"""

        data = []
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current = start

        while current <= end:
            # Total daily sales (organic + ad-attributed)
            daily_orders = int(random.uniform(150, 400))
            aov = random.uniform(95, 280)
            daily_revenue = daily_orders * aov
            units = int(daily_orders * random.uniform(1.2, 2.0))

            data.append(WalmartSalesData(
                activity_date=current.strftime("%Y-%m-%d"),
                profile=self.credentials.seller_id,
                country="US",
                conversions=daily_orders,
                revenue=round(daily_revenue, 2),
                units_sold=units,
                order_count=daily_orders
            ))

            current += timedelta(days=1)

        return data


# ==============================================================================
# FOSPHA DATA TRANSFORMER
# ==============================================================================

class FosphaDataTransformer:
    """
    Transform Walmart data into Fospha's unified schema

    Following the pattern established by Amazon Seller Central connector:
    - Combine advertising and sales data
    - Calculate organic metrics (Total Sales - Ad-Attributed Sales)
    - Apply market mapping
    - Configure for Fospha modeling (drain/boost channels)
    """

    # Fospha Channel Configuration
    CHANNEL_CONFIG = {
        "Walmart Sponsored Products": {"is_drain": 0, "is_boost": 1},
        "Walmart Sponsored Brands": {"is_drain": 0, "is_boost": 1},
        "Walmart Sponsored Display": {"is_drain": 0, "is_boost": 1},
        "Walmart Organic": {"is_drain": 1, "is_boost": 0}
    }

    # Market Mapping (similar to Amazon marketplace IDs)
    MARKET_MAPPING = {
        "US": {"country_code": "US", "currency": "USD"},
        "CA": {"country_code": "CA", "currency": "CAD"},
        "MX": {"country_code": "MX", "currency": "MXN"}
    }

    def __init__(self):
        self.processed_data = []

    def transform_ad_data(
        self,
        ad_data: List[WalmartAdPerformanceData]
    ) -> List[Dict[str, Any]]:
        """
        Transform advertising data to Fospha schema

        Output schema matches Fospha's ad platform connector requirements
        """
        transformed = []

        for record in ad_data:
            fospha_record = {
                # Required Fields
                "activity_date": record.activity_date,
                "campaign_id": record.campaign_id,
                "campaign_name": record.campaign_name,
                "cost": record.cost,
                "impressions": record.impressions,
                "clicks": record.clicks,
                "market": record.market,

                # Attribution Fields
                "revenue": record.revenue,
                "conversions": record.conversions,
                "currency_code": record.currency_code,

                # Fospha Integration Fields
                "channel_group": record.channel_group,
                "source": record.source,
                "sales_platform": record.sales_platform,

                # Walmart-Specific (for Halo modeling)
                "in_store_attributed_sales": record.in_store_attributed_sales,
                "online_attributed_sales": record.online_attributed_sales,
                "new_to_brand_sales": record.new_to_brand_sales,
                "new_to_brand_orders": record.new_to_brand_orders,

                # Calculated Metrics
                "ctr": record.ctr,
                "cpc": record.cpc,
                "roas": record.roas,

                # Fospha Model Configuration
                "is_drain": self.CHANNEL_CONFIG.get(record.channel_group, {}).get("is_drain", 0),
                "is_boost": self.CHANNEL_CONFIG.get(record.channel_group, {}).get("is_boost", 0)
            }
            transformed.append(fospha_record)

        return transformed

    def transform_sales_data(
        self,
        sales_data: List[WalmartSalesData]
    ) -> List[Dict[str, Any]]:
        """
        Transform sales data to Fospha schema
        """
        transformed = []

        for record in sales_data:
            fospha_record = {
                "activity_date": record.activity_date,
                "profile": record.profile,
                "country": record.country,
                "sales_platform": record.sales_platform,
                "channel_group": record.channel_group,
                "source": record.source,
                "conversions": record.conversions,
                "revenue": record.revenue,
                "units_sold": record.units_sold,
                "currency_code": record.currency_code,
                "order_count": record.order_count,
                "average_order_value": record.average_order_value,

                # Fospha Model Configuration
                "is_drain": self.CHANNEL_CONFIG.get(record.channel_group, {}).get("is_drain", 1),
                "is_boost": self.CHANNEL_CONFIG.get(record.channel_group, {}).get("is_boost", 0)
            }
            transformed.append(fospha_record)

        return transformed

    def calculate_organic_metrics(
        self,
        total_sales: List[WalmartSalesData],
        ad_attributed_sales: List[WalmartAdPerformanceData]
    ) -> List[Dict[str, Any]]:
        """
        Calculate Walmart Organic metrics

        Following Amazon Halo pattern:
        Walmart Organic = Total Walmart Sales - Ad-Attributed Sales
        """
        # Aggregate ad-attributed metrics by date
        ad_by_date = {}
        for ad in ad_attributed_sales:
            date = ad.activity_date
            if date not in ad_by_date:
                ad_by_date[date] = {"revenue": 0, "conversions": 0}
            ad_by_date[date]["revenue"] += ad.revenue
            ad_by_date[date]["conversions"] += ad.conversions

        organic_data = []
        for sale in total_sales:
            date = sale.activity_date
            ad_metrics = ad_by_date.get(date, {"revenue": 0, "conversions": 0})

            organic_revenue = max(0, sale.revenue - ad_metrics["revenue"])
            organic_conversions = max(0, sale.conversions - ad_metrics["conversions"])

            organic_data.append({
                "activity_date": date,
                "channel_group": "Walmart Organic",
                "source": "walmart",
                "sales_platform": "walmart",
                "revenue": round(organic_revenue, 2),
                "conversions": organic_conversions,
                "country": sale.country,
                "currency_code": sale.currency_code,
                "is_drain": 1,
                "is_boost": 0
            })

        return organic_data


# ==============================================================================
# FOSPHA CONNECTOR ORCHESTRATOR
# ==============================================================================

class FosphaWalmartConnector:
    """
    Main connector class that orchestrates the Walmart integration

    This follows Fospha's connector architecture:
    1. Authenticate with APIs
    2. Fetch data (advertising + sales)
    3. Transform to Fospha schema
    4. Calculate derived metrics (organic, halo)
    5. Output for ingestion pipeline
    """

    def __init__(
        self,
        ad_credentials: WalmartConnectCredentials,
        marketplace_credentials: WalmartMarketplaceCredentials,
        client_name: str = "Callaway Golf"
    ):
        self.client_name = client_name
        self.ad_client = WalmartConnectAPIClient(ad_credentials)
        self.marketplace_client = WalmartMarketplaceAPIClient(marketplace_credentials)
        self.transformer = FosphaDataTransformer()

    def run_daily_sync(
        self,
        sync_date: Optional[str] = None,
        lookback_days: int = 7
    ) -> Dict[str, Any]:
        """
        Execute daily data sync

        This is the main entry point for the daily ETL job
        """
        if sync_date is None:
            sync_date = datetime.utcnow().strftime("%Y-%m-%d")

        start_date = (datetime.strptime(sync_date, "%Y-%m-%d") - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        end_date = sync_date

        print(f"\n{'='*60}")
        print(f"FOSPHA WALMART CONNECTOR - Daily Sync")
        print(f"{'='*60}")
        print(f"Client: {self.client_name}")
        print(f"Sync Date: {sync_date}")
        print(f"Lookback Window: {lookback_days} days ({start_date} to {end_date})")
        print(f"{'='*60}\n")

        # Step 1: Authenticate
        print("[STEP 1] Authenticating with Walmart APIs...")
        self.ad_client.authenticate()
        self.marketplace_client.authenticate()

        # Step 2: Fetch advertising data
        print("\n[STEP 2] Fetching advertising performance data...")
        ad_data = self.ad_client.get_campaign_performance(start_date, end_date)
        print(f"[DATA] Retrieved {len(ad_data)} advertising records")

        # Step 3: Fetch sales data
        print("\n[STEP 3] Fetching marketplace sales data...")
        sales_data = self.marketplace_client.get_sales_data(start_date, end_date)
        print(f"[DATA] Retrieved {len(sales_data)} sales records")

        # Step 4: Transform data
        print("\n[STEP 4] Transforming data to Fospha schema...")
        transformed_ads = self.transformer.transform_ad_data(ad_data)
        transformed_sales = self.transformer.transform_sales_data(sales_data)

        # Step 5: Calculate organic metrics
        print("\n[STEP 5] Calculating organic metrics...")
        organic_data = self.transformer.calculate_organic_metrics(sales_data, ad_data)

        # Step 6: Get real-time stats
        print("\n[STEP 6] Fetching real-time statistics...")
        realtime_stats = self.ad_client.get_realtime_stats()

        # Compile results
        results = {
            "client": self.client_name,
            "sync_timestamp": datetime.utcnow().isoformat(),
            "date_range": {"start": start_date, "end": end_date},
            "record_counts": {
                "advertising": len(transformed_ads),
                "sales": len(transformed_sales),
                "organic": len(organic_data)
            },
            "data": {
                "advertising": transformed_ads,
                "sales": transformed_sales,
                "organic": organic_data
            },
            "realtime_stats": realtime_stats,
            "summary": self._calculate_summary(transformed_ads, transformed_sales, organic_data)
        }

        print(f"\n{'='*60}")
        print("SYNC COMPLETE")
        print(f"{'='*60}")

        return results

    def _calculate_summary(
        self,
        ad_data: List[Dict],
        sales_data: List[Dict],
        organic_data: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate summary metrics for the sync"""

        total_ad_spend = sum(r["cost"] for r in ad_data)
        total_ad_revenue = sum(r["revenue"] for r in ad_data)
        total_sales_revenue = sum(r["revenue"] for r in sales_data)
        total_organic_revenue = sum(r["revenue"] for r in organic_data)

        total_impressions = sum(r["impressions"] for r in ad_data)
        total_clicks = sum(r["clicks"] for r in ad_data)
        total_conversions = sum(r["conversions"] for r in ad_data)

        in_store_sales = sum(r.get("in_store_attributed_sales", 0) for r in ad_data)

        return {
            "total_walmart_revenue": round(total_sales_revenue, 2),
            "ad_attributed_revenue": round(total_ad_revenue, 2),
            "organic_revenue": round(total_organic_revenue, 2),
            "in_store_attributed_sales": round(in_store_sales, 2),
            "total_ad_spend": round(total_ad_spend, 2),
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "overall_roas": round(total_ad_revenue / total_ad_spend, 2) if total_ad_spend > 0 else 0,
            "unified_roas": round(total_sales_revenue / total_ad_spend, 2) if total_ad_spend > 0 else 0,
            "halo_effect_multiplier": round(total_sales_revenue / total_ad_revenue, 2) if total_ad_revenue > 0 else 0
        }


# ==============================================================================
# DEMO EXECUTION
# ==============================================================================

def run_demo():
    """
    Run the Walmart Connect Connector demo for Callaway Golf
    """
    print("\n" + "="*70)
    print("  FOSPHA WALMART CONNECT CONNECTOR PROTOTYPE")
    print("  Demonstrating Integration for: CALLAWAY GOLF")
    print("="*70 + "\n")

    # Initialize credentials (would come from secure storage in production)
    ad_credentials = WalmartConnectCredentials(
        client_id="callaway_golf_wmc_client_id",
        client_secret="*****",
        advertiser_id="CG-WALMART-001"
    )

    marketplace_credentials = WalmartMarketplaceCredentials(
        client_id="callaway_golf_mp_client_id",
        client_secret="*****",
        seller_id="CALLAWAY-SELLER-001"
    )

    # Initialize connector
    connector = FosphaWalmartConnector(
        ad_credentials=ad_credentials,
        marketplace_credentials=marketplace_credentials,
        client_name="Callaway Golf"
    )

    # Run daily sync
    results = connector.run_daily_sync(
        sync_date="2026-01-15",
        lookback_days=30
    )

    # Display summary
    print("\n" + "="*70)
    print("  SYNC SUMMARY - Callaway Golf")
    print("="*70)

    summary = results["summary"]
    print(f"\n  Total Walmart Revenue:      ${summary['total_walmart_revenue']:,.2f}")
    print(f"  Ad-Attributed Revenue:      ${summary['ad_attributed_revenue']:,.2f}")
    print(f"  Organic Revenue:            ${summary['organic_revenue']:,.2f}")
    print(f"  In-Store Attributed Sales:  ${summary['in_store_attributed_sales']:,.2f}")
    print(f"\n  Total Ad Spend:             ${summary['total_ad_spend']:,.2f}")
    print(f"  Total Impressions:          {summary['total_impressions']:,}")
    print(f"  Total Clicks:               {summary['total_clicks']:,}")
    print(f"  Total Conversions:          {summary['total_conversions']:,}")
    print(f"\n  Ad Platform ROAS:           {summary['overall_roas']}x")
    print(f"  Unified ROAS (w/ Halo):     {summary['unified_roas']}x")
    print(f"  Halo Effect Multiplier:     {summary['halo_effect_multiplier']}x")

    print("\n" + "="*70 + "\n")

    return results


if __name__ == "__main__":
    results = run_demo()
