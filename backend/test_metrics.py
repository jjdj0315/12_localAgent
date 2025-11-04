import asyncio
from app.core.database import get_db
from app.services.metrics_collector import MetricsCollector

async def test_collection():
    async for db in get_db():
        collector = MetricsCollector(db)
        results = await collector.collect_all_metrics('hourly')
        print('메트릭 수집 결과:', results)
        break

if __name__ == "__main__":
    asyncio.run(test_collection())
