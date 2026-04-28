import json
import sys


def main() -> None:
    _prompt = sys.stdin.read()
    print(
        json.dumps(
            {
                "summary": "Mock AI summary for Knowledge Pack validation.",
                "key_points": [],
                "tags": [],
                "entities": [],
                "suggested_links": [],
                "questions_for_search": [],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

