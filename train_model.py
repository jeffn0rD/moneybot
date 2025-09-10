import sys, os; from pathlib import Path; project_root = Path(__file__).parent; sys.path.insert(0, str(project_root)); from libs.models.train_meta import main; import asyncio; asyncio.run(main())
