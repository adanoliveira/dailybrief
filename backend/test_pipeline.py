#!/usr/bin/env python
from apps.content.tasks import process_top_headlines_pipeline
import json

print("🚀 Starting content enrichment pipeline with AI processing...")
result = process_top_headlines_pipeline()
print("✅ Pipeline completed successfully!")

print("\n📊 Pipeline Summary:")
summary = result.get('pipeline_summary', {})
print(f"  • Total articles processed: {summary.get('total_articles_processed', 0)}")
print(f"  • Successful completions: {summary.get('successful_completions', 0)}")
print(f"  • Pipeline duration: {summary.get('pipeline_duration_ms', 0)/1000:.1f}s")

print("\n📈 Stage Results:")
for stage_name, stage_data in result.items():
    if stage_name.startswith('stage_') and isinstance(stage_data, dict):
        stage_num = stage_name.split('_')[1]
        processed = stage_data.get('processed', 0)
        successful = stage_data.get('successful', 0)
        failed = stage_data.get('failed', 0)
        print(f"  Stage {stage_num}: {successful}/{processed} successful ({failed} failed)")

print("\n🔍 Detailed Results:")
print(json.dumps(result, indent=2, default=str)) 