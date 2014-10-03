#!/usr/bin/python
""" Fix tags in files from Jamendo; rename files. """

import os
import re
import unicodedata

import mutagen


_RE_REM_TITLE = re.compile(r'^(.+) - \d\d - (.+)$')
_RE_GET_DATE_FROM_CR = re.compile(r'^(\d\d\d\d)-\d\d-\d\dT')
_RE_CHECK_TRACK_NUM = re.compile(r'^(\d+)/(\d+)')


def _print_tags(tags):
    print '\n'.join('\t' + k + ': ' + str(v)
                    for k, v in sorted(tags.iteritems()))


def filename_from_tags(tags):
    tracknumber = tags.get('tracknumber')
    if tracknumber and tracknumber[0]:
        num = tracknumber[0].split('/')[0]
        fname = '%s. %s' % (num, tags['title'][0])
    else:
        fname = '%s - %s' % (tags['performer'][0], tags['title'][0])
    return unicodedata.normalize('NFKD', fname).encode('ascii', 'ignore')


def process_file(filename, idx, len_files):
    print 'Processing ', filename
    tags = mutagen.File(filename, easy=True)
    _print_tags(tags)
    # fix performer
    if not tags.get('performer'):
        if tags.get('artist'):
            tags['performer'] = [tags['artist'][0]]
    # fix title
    artist = tags.get('artist')
    title = os.path.splitext(os.path.basename(filename))[0]
    if tags.get('title'):
        title = tags['title'][0]
    if title:
        mtitle = _RE_REM_TITLE.match(title)
        if mtitle:
            title = mtitle.group(2)
            tags['artist'] = mtitle.group(1)
    if title and artist and title.startswith(artist[0] + " - "):
        title = title[len(artist[0]) + 3:]
    if title:
        tags['title'] = [title]
    else:
        print '[E]: missing title'
    # fix year
    if not tags.get('date'):
        copyr = tags.get('copyright')
        if copyr and copyr[0]:
            year_re = _RE_GET_DATE_FROM_CR.match(copyr[0])
            if year_re and year_re.group(1):
                tags['date'] = [str(year_re.group(1))]
    # fix tracknumber
    if len_files == 1:
        # remove track number when only one file
        if 'tracknumber' in tags:
            del tags['tracknumber']
    else:
        curr_tracknum = tags.get('tracknumber')
        if curr_tracknum and curr_tracknum[0]:
            if not _RE_CHECK_TRACK_NUM.match(curr_tracknum[0]):
                curr_tracknum = curr_tracknum[0]
                try:
                    curr_tracknum = "%02d" % int(curr_tracknum)
                except ValueError:
                    pass
                tags['tracknumber'] = [curr_tracknum +
                                       '/' +
                                       str(len_files)]
        else:
            tags['tracknumber'] = [("%02d" % idx) + '/' + str(len_files)]
    #print 'Result: '
    _print_tags(tags)
    tags.save()
    print 'Saved\n'
    return tags


def main(dirname='.'):
    files = []
    for fname in os.listdir(dirname):
        fullname = os.path.join(dirname, fname)
        if os.path.isfile(fullname) and \
                os.path.splitext(fname)[1].lower() in ('.mp3', '.ogg'):
            files.append(fullname)
    for idx, filename in enumerate(sorted(files)):
        tags = process_file(filename, idx, len(files))
        curr_filename = os.path.basename(filename)
        ext = os.path.splitext(curr_filename)[1]
        dst_filename = filename_from_tags(tags) + ext
        dst_filename = dst_filename.lower()
        if dst_filename != curr_filename:
            print '\tRename %s -> %s' % (curr_filename, dst_filename)
            os.rename(filename, os.path.join(dirname, dst_filename))


if __name__ == '__main__':
    main()
