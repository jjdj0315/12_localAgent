"""Quick test to see if llama-cpp-python can load the GGUF model"""
import os
import sys
from pathlib import Path

# Load .env
from dotenv import load_dotenv
load_dotenv()

print(f"Python version: {sys.version}")
print(f"GGUF_MODEL_PATH: {os.getenv('GGUF_MODEL_PATH')}")

model_path = os.getenv("GGUF_MODEL_PATH", "C:/02_practice/12_localAgent/models/qwen2.5-3b-instruct-q4_k_m.gguf")

if not Path(model_path).exists():
    print(f"ERROR: Model file not found at: {model_path}")
    sys.exit(1)

print(f"Model file exists: {model_path}")
print(f"Model file size: {Path(model_path).stat().st_size / 1024 / 1024:.2f} MB")

print("\nAttempting to load model with llama-cpp-python...")
print("This may take 30-60 seconds on CPU...")

try:
    from llama_cpp import Llama
    print("llama_cpp module imported successfully")

    print(f"\nInitializing Llama with:")
    print(f"  model_path={model_path}")
    print(f"  n_ctx=512 (small for test)")
    print(f"  n_threads=4")
    print(f"  verbose=True")

    model = Llama(
        model_path=model_path,
        n_ctx=512,  # Small context for faster loading
        n_threads=4,
        n_gpu_layers=0,
        verbose=True,
    )

    print("\n[SUCCESS] Model loaded successfully!")
    print("Testing generation...")

    output = model("Hello", max_tokens=5, temperature=0.0)
    print(f"Test output: {output}")

    print("\n[SUCCESS] Model is working correctly!")

except ImportError as e:
    print(f"\n[ERROR] Failed to import llama_cpp: {e}")
    print("Install with: pip install llama-cpp-python")
    sys.exit(1)

except Exception as e:
    print(f"\n[ERROR] Failed to load model: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
