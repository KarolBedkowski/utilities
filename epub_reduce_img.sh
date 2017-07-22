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
	find . \( -name '*.png' -or -name '*.jpg' \) \
		-print \
		-exec mogrify -resize 600x800\> -define png:compression-level=9 -quality 60  {} ';' \
		-exec leanify -i 5 {} ';'
	NEWFILE="$BASEDIR/${EPUBNAME%.epub}_new.epub"
	zip -0Xq "$NEWFILE" mimetype META-INF
	zip -Xr9Dq "$NEWFILE" ./*
}

main "$1"
