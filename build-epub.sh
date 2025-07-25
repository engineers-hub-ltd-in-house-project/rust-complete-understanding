#!/bin/bash

# Build HTML with mdBook first
echo "Building HTML with mdBook..."
mdbook build

# Create temporary directory for EPUB generation
mkdir -p temp_epub

# Create a YAML metadata file for better chapter handling
cat > temp_epub/metadata.yaml << EOF
---
title: "Rust完全理解: 公式ドキュメント網羅とコンピューターサイエンス理論"
author: "Author Name"
language: ja
date: 2025-01-25
publisher: "Publisher Name"
rights: "All rights reserved"
description: "Rustの公式ドキュメントを網羅しつつ、コンピューターサイエンスの理論的背景から解説する包括的な書籍"
toc-title: "目次"
---
EOF

# Create ordered file list based on SUMMARY.md structure
echo "Creating ordered chapter list..."
FILES=""

# Add README
if [ -f "src/README.md" ]; then
    FILES="$FILES src/README.md"
fi

# Add Part I chapters in order
for file in src/part1_foundations/chapter_1.md \
           src/part1_foundations/chapter_1_1.md \
           src/part1_foundations/chapter_1_2.md \
           src/part1_foundations/chapter_2.md \
           src/part1_foundations/chapter_2_1.md \
           src/part1_foundations/chapter_2_2.md \
           src/part1_foundations/chapter_2_3.md \
           src/part1_foundations/chapter_3.md \
           src/part1_foundations/chapter_3_1.md \
           src/part1_foundations/chapter_3_2.md; do
    if [ -f "$file" ]; then
        FILES="$FILES $file"
    fi
done

# Add Part II chapters
for file in src/part2_type_system/chapter_4.md \
           src/part2_type_system/chapter_5.md \
           src/part2_type_system/chapter_6.md; do
    if [ -f "$file" ]; then
        FILES="$FILES $file"
    fi
done

# Add Part III chapters
for file in src/part3_advanced/chapter_7.md \
           src/part3_advanced/chapter_8.md \
           src/part3_advanced/chapter_9.md; do
    if [ -f "$file" ]; then
        FILES="$FILES $file"
    fi
done

# Add Appendix
for file in src/appendix/official_docs_mapping.md \
           src/appendix/glossary.md \
           src/appendix/references.md; do
    if [ -f "$file" ]; then
        FILES="$FILES $file"
    fi
done

# Generate EPUB with individual chapter files
echo "Generating EPUB with Pandoc..."
pandoc temp_epub/metadata.yaml $FILES \
    -o rust-complete-understanding.epub \
    --toc \
    --toc-depth=3 \
    --epub-chapter-level=1 \
    -f markdown+smart \
    -t epub3

# Clean up
rm -rf temp_epub

echo "EPUB generation complete: rust-complete-understanding.epub"