#!/usr/bin/env python3
"""
Anki Exporter Tool
Converts question/answer card data into Anki-compatible plain-text or CSV import files.
"""

import csv
import io
from pathlib import Path
from typing import Any, Dict, List, Optional


def export_deck(
    deck_name: str,
    cards: List[Dict[str, Any]],
    output_format: str = "txt",
    output_path: Optional[str] = None,
    tag_all: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Export flashcard data to an Anki-compatible import file.

    Args:
        deck_name: Name for the Anki deck.
        cards: List of dicts with 'front', 'back', and optional 'tags' keys.
        output_format: 'txt' for Anki plain-text import, 'csv' for spreadsheet review.
        output_path: File path to write (auto-named if omitted).
        tag_all: Tags to apply to every card.

    Returns:
        dict with status, output_path, card_count, message.
    """
    try:
        tag_all = tag_all or []

        if not output_path:
            safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in deck_name)
            safe_name = safe_name.strip().replace(" ", "_")
            output_path = f"{safe_name}.{output_format}"

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if output_format == "txt":
            lines = [
                "# Anki Import File",
                f"# Deck: {deck_name}",
                "# Fields: Front, Back, Tags",
                "# Separator: tab",
                "#notetype:Basic",
                f"#deck:{deck_name}",
                "",
            ]
            for card in cards:
                front = str(card.get("front", "")).replace("\t", " ").replace("\n", "<br>")
                back = str(card.get("back", "")).replace("\t", " ").replace("\n", "<br>")
                card_tags = list(card.get("tags") or []) + tag_all
                tags_str = " ".join(card_tags)
                lines.append(f"{front}\t{back}\t{tags_str}")

            out.write_text("\n".join(lines), encoding="utf-8")

        elif output_format == "csv":
            rows = []
            for card in cards:
                front = str(card.get("front", ""))
                back = str(card.get("back", ""))
                card_tags = list(card.get("tags") or []) + tag_all
                tags_str = " ".join(card_tags)
                rows.append({"deck": deck_name, "front": front, "back": back, "tags": tags_str})

            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=["deck", "front", "back", "tags"])
            writer.writeheader()
            writer.writerows(rows)
            out.write_text(buf.getvalue(), encoding="utf-8")

        else:
            return {
                "status": "error",
                "message": f"Unknown output_format: '{output_format}'. Use 'txt' or 'csv'.",
            }

        return {
            "status": "success",
            "output_path": str(out.resolve()),
            "card_count": len(cards),
            "message": f"Exported {len(cards)} cards to '{out.name}' (format: {output_format}).",
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import fire
    fire.Fire(export_deck)
