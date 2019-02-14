#! /bin/bash -x
#
# epub_reduce_img.sh
# reduce images in epub file to max 600x800
# Copyright (C) Karol Będkowski <Karol Będkowski@kntbk>, 2017
#
# Distributed under terms of the GPLv3 license.
#
[[ ${DEBUG:-} != "" ]] && set -x

set -o nounset
set -o errexit

function log() {
	echo "[$(date +%Y-%m-%d\ %H:%M:%S)]: $*" >&2
}


function main() {
	TEMPDIR=$(mktemp -d)
	trap "rm -rf -f -- '$TEMPDIR'" EXIT
	EPUBNAME="${1##*/}"
	BASEDIR="$(dirname "$(readlink -f "$1")")"
	cp "$EPUBNAME" "$TEMPDIR/"
	cd "$TEMPDIR"
	unzip "$EPUBNAME"
	rm -f "$EPUBNAME"

	log "png..."
	find . -type f -name '*.png'  \
		-print \
		-exec mogrify -colorspace gray -colors 16 -depth 4 -thumbnail 800x1024 -define png:compression-level=9 -quality 9 {} ';' \
		-exec pngout-linux-pentium4 -f5 {} ';' \
		-exec leanify -i 5 {} ';'
		#-exec mogrify -resize 600x800\> -define png:compression-level=9 -quality 60  {} ';' \

	log "jpg..."
	find . -type f -name '*.jpg'  \
		-print \
		-exec mogrify -thumbnail 800x1024 -quality 85 {} ';' \
		-exec leanify -i 5 {} ';'
		#-exec mogrify -resize 600x800\> -define png:compression-level=9 -quality 60  {} ';' \

	NEWFILE="$BASEDIR/${EPUBNAME%.epub}_new.epub"
	log "New file: $NEWFILE"
	zip -0Xq "$NEWFILE" mimetype
	zip -Xr9Dq "$NEWFILE" META-INF
	zip -Xr9Dq "$NEWFILE" ./*
}

main "$1"
