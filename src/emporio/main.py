"""Application entry point. Run with python -m emporio.main."""
import argparse
import uvicorn

def main():
    parser = argparse.ArgumentParser(description="Run the local music store prototype.")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    from emporio.web.app import create_app
    uvicorn.run(create_app(), host="127.0.0.1", port=args.port)

if __name__ == "__main__":
    main()
