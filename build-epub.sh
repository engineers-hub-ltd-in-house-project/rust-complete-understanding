#!/bin/bash

# Build HTML with mdBook first
echo "Building HTML with mdBook..."
mdbook build

# Create temporary directory for EPUB generation
mkdir -p temp_epub

# Copy all markdown files to temp directory
cp -r src/* temp_epub/

# Combine all markdown files in order
echo "Combining markdown files..."
cat > temp_epub/combined.md << EOF
# Rust完全理解: 公式ドキュメント網羅とコンピューターサイエンス理論

EOF

# Add introduction
if [ -f "src/README.md" ]; then
    cat src/README.md >> temp_epub/combined.md
    echo -e "\n\n" >> temp_epub/combined.md
fi

# Add chapters in order (following SUMMARY.md structure)
for chapter in src/part1_foundations/*.md src/part2_type_system/*.md src/part3_advanced/*.md src/appendix/*.md; do
    if [ -f "$chapter" ] && [ "$chapter" != "src/README.md" ]; then
        echo "Adding $chapter..."
        cat "$chapter" >> temp_epub/combined.md
        echo -e "\n\n" >> temp_epub/combined.md
    fi
done

# Generate EPUB with Pandoc
echo "Generating EPUB with Pandoc..."
pandoc temp_epub/combined.md \
    -o rust-complete-understanding.epub \
    --epub-metadata=epub-metadata.xml \
    --epub-cover-image=assets/cover.png \
    --toc \
    --toc-depth=3 \
    -f markdown \
    -t epub3

# Clean up
rm -rf temp_epub

echo "EPUB generation complete: rust-complete-understanding.epub"