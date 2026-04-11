---
description: Generate Anki-compatible flashcards from notes, a topic list, or a document
  passage
---

Generate high-quality Anki flashcards from the following source material.

Requirements:
1. Apply the minimum information principle — one atomic concept per card
2. Write fronts as unambiguous active-recall questions
3. Include formal definitions, examples, and counterexamples on backs
4. Vary card types: Basic, Cloze deletion, and Reverse
5. Tag each card: topic + difficulty (easy/medium/hard) + source
6. Use LaTeX dollar notation for all math: `$...$` inline, `$$...$$` display
7. Export using the anki-exporter tool as a .txt import file

Source material: $ARGUMENTS
