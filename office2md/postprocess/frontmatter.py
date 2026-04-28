import yaml


def add_frontmatter(markdown: str, metadata: dict) -> str:
    frontmatter = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False)
    return f"---\n{frontmatter}---\n\n{markdown}"

