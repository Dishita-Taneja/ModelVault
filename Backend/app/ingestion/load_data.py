import asyncio
import json
import sys
from pathlib import Path

# Add backend directory to python path if executing as script
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.logging import logger
from app.ingestion.service import run_ingestion_pipeline


def main():
    logger.info("Executing ModelVault Data Ingestion CLI...")
    report = asyncio.run(run_ingestion_pipeline())
    print("\n================ INGESTION PIPELINE REPORT ================")
    print(json.dumps(report.model_dump(), indent=2))
    print("============================================================\n")


if __name__ == "__main__":
    main()
