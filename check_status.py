"""Quick status check for the RAG pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend" / "src"))

print("="*70)
print("🔍 RAG PIPELINE STATUS CHECK")
print("="*70)

# Check Python version
print(f"\n📌 Python: {sys.version.split()[0]}")

# Check dependencies
print("\n📦 Dependencies:")
deps = {
    'chromadb': False,
    'sentence_transformers': False,
    'rank_bm25': False,
    'numpy': False,
    'httpx': False,
    'transformers': False,
    'torch': False,
}

for dep in deps.keys():
    try:
        __import__(dep)
        deps[dep] = True
        print(f"   ✓ {dep}")
    except ImportError:
        print(f"   ✗ {dep} - not installed")

# Check core enhancements
print("\n🎯 Core Enhancements:")
enhancements = [
    'athar.rag.retrieval.query_processor',
    'athar.rag.cache',
    'athar.rag.context_builder',
    'athar.rag.error_handling',
    'athar.rag.metrics',
]

all_working = True
for mod in enhancements:
    try:
        __import__(mod)
        print(f"   ✓ {mod.split('.')[-1]}")
    except Exception as e:
        print(f"   ✗ {mod.split('.')[-1]}: {e}")
        all_working = False

# Check data
print("\n💾 Knowledge Base:")
try:
    from athar.rag.pipeline import pipeline
    pipeline.initialize()
    count = pipeline.semantic.count()
    ready = pipeline.is_ready
    
    print(f"   Documents: {count}")
    print(f"   Ready: {ready}")
    print(f"   LLM: {pipeline.llm.provider_name if pipeline.llm else 'None'}")
    
    if count == 0:
        print("\n   ⚠️  Knowledge base empty - run ingestion")
    else:
        print("\n   ✅ Pipeline ready for queries!")
        
except Exception as e:
    print(f"   ✗ Cannot initialize: {e}")

# Summary
print("\n" + "="*70)
print("📋 SUMMARY")
print("="*70)

missing_deps = [k for k, v in deps.items() if not v]
if missing_deps:
    print(f"   Missing dependencies: {', '.join(missing_deps)}")
    print(f"   Install: pip install {' '.join(missing_deps)}")
else:
    print("   ✅ All dependencies installed")

if all_working:
    print("   ✅ All enhancements loaded")
else:
    print("   ⚠️  Some enhancements have issues")

print("="*70)
