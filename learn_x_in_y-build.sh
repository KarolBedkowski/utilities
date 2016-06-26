#!/usr/bin/env bash
# Convert source files from https://github.com/adambard/learnxinyminutes-docs
# to epub file.

mkdir -p temp

echo "Sources..."
for i in *.markdown; do
	echo "  $i"
	LANG=${i%%.html.markdown}
	cat > "temp/$i" <<EOF
${LANG}
========================

EOF
	cat "$i" >> "temp/$i"
#	sed 's/^\(\#\+.\+\)$/\#\1/' "$i" >> "temp/$i"
done

echo "Epub..."
cat > temp/epub.meta <<EOF
	<dc:creator opf:role="aut">learnxinyminutes.com</dc:creator>
	<dc:title>Learn X in Y minutes</dc:title>
	<dc:language>english</dc:language>
EOF

echo "PANDOC..."
pandoc --from markdown --to epub \
	-o learn_x_in_y.epub \
	--epub-metadata=temp/epub.meta \
	--toc-depth=1 \
	temp/*.markdown

