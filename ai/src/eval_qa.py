"""Compatibility entry point; evaluation always uses the held-out test split."""
from ai.src.eval.eval_qa import evaluate_qa
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--config", required=True)
    evaluate_qa(parser.parse_args().config)
