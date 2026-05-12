import sys
import os
import asyncio
from decimal import Decimal

# Add backend directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Try imports
try:
    from services.risk_engine import risk_engine
    from rag_service import get_sync_status
    from services.observability import metrics
    from services.redis_manager import redis_manager
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def verify_hardening():
    print("Starting Hardening Verification...")
    print("-" * 50)

    # 1. Test Risk Engine (Daily Loss)
    print("1. Testing Risk Engine (Daily Loss Limit)...")
    risk_report = risk_engine.assess_trade(
        symbol="BTC", 
        quantity=0.1, 
        price=60000, 
        side="BUY", 
        wallet_balance=10000, 
        daily_pnl=-600
    )
    if risk_report.action == "BLOCK" and "Daily Loss Limit Reached" in risk_report.reason:
        print("OK: Risk Engine correctly BLOCKED trade due to daily loss limit.")
    else:
        print(f"FAIL: Risk Engine FAILED daily loss test. Action: {risk_report.action}, Reason: {risk_report.reason}")

    # 2. Test RAG Sync Status
    print("\n2. Testing RAG Sync Status...")
    sync_status = get_sync_status()
    print(f"   Sync Percentage: {sync_status['percent']}%")
    print(f"   Files in ./data: {sync_status['total_files']}")
    print(f"   Indexed Files: {sync_status['indexed_files']}")
    print("OK: RAG Sync Status logic is functional.")

    # 3. Test Redis Rate Limiter
    print("\n3. Testing Redis-backed Rate Limiter...")
    key = "test_rate_limit"
    limit = 2
    window = 10
    
    await redis_manager.client.delete(f"rl:{key}")
    
    r1 = await redis_manager.is_rate_limited(key, limit, window) 
    r2 = await redis_manager.is_rate_limited(key, limit, window) 
    r3 = await redis_manager.is_rate_limited(key, limit, window) 
    
    if not r1 and not r2 and r3:
        print("OK: Redis Rate Limiter correctly blocked the 3rd request.")
    else:
        print(f"FAIL: Redis Rate Limiter FAILED. Results: {r1}, {r2}, {r3}")

    # 4. Verify Observability Summary
    print("\n4. Verifying Observability Metrics Summary...")
    metrics.record_latency("api_request", 150)
    metrics.record_latency("llm_response", 3200)
    summary = metrics.get_summary()
    
    if summary['api_latency'] == '150ms' and summary['llm_response'] == '3.2s':
        print("OK: Observability metrics are being recorded and summarized correctly.")
    else:
        print(f"FAIL: Observability Summary FAILED. Summary: {summary}")

    print("-" * 50)
    print("Verification Complete!")

if __name__ == "__main__":
    asyncio.run(verify_hardening())
