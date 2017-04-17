#!/usr/bin/env bash
# Convert source files from https://github.com/adambard/learnxinyminutes-docs
# to epub file.
#
[[ $DEBUG != "" ]] && set -x

set -o nounset
set -o errexit


function log() {
	echo "[$(date +%Y-%m-%d\ %H:%M:%S)]: $*" >&2
}


function filter() {
	awk '''
		BEGIN { flag=0; FS="\n" }
		/^```/ { flag=1-flag; }
		/^#/ && flag == 0 { print "#" $0; next }
		{ print }
	'''
}


function prepare() {
	log "Sources..."
	for i in *.markdown; do
		dst="temp/${i,,}"
		log "  $i"
		LANG=${i%%.html.markdown}
		cat > "$dst" <<EOF
${LANG}
========================

EOF
		cat "$i" | filter >> "$dst"
	done

	mv temp/readme.markdown temp/README.markdown
	mv temp/contributing.markdown temp/CONTRIBUTING.markdown
}


function epubmeta() {
	log epubmeta
	cat > temp/TITLE.markdown <<EOF
---
title:
- type: main
  text: Learn X in Y minutes
- type: subtitle
  text: $(date +"%Y-%m-%d %H:%M:%S")
creator:
- role: author
  text: Various
date: $(date +"%Y-%m-%d")
language: eng
---
EOF
}


function main() {
	mkdir -p temp
	rm -f temp/* || true

	prepare
	epubmeta

	log "PANDOC..."
	pandoc --from markdown --to epub \
		-o learn_x_in_y.epub \
		--toc-depth=2 \
		temp/TITLE.markdown temp/README.markdown temp/CONTRIBUTING.markdown \
		$(ls temp/*.markdown | grep -v -e 'README' -e 'CONTRIBUTING' -e 'TITLE' | sort)

	log 'leanify'
	leanify learn_x_in_y.epub

	log 'done'
}


main
