import re


def toc(markdown):
    """Table of contents: one "- [Title](#anchor)" line per heading, indented by level."""
    lines = []
    for match in re.finditer(r"^(#{1,6})\s+(.+?)\s*$", markdown, re.M):
        level, title = len(match.group(1)), match.group(2)
        anchor = re.sub(r"[^a-z0-9 -]", "", title.lower()).replace(" ", "-")
        lines.append(f"{'  ' * (level - 1)}- [{title}](#{anchor})")
    return "\n".join(lines)
