#!/usr/bin/python
# -*- coding: utf8 -*-
""" Fix tags in mp3/ogg files (i.e. from Jamendo); rename files. """

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2014"
__version__ = "2014-12-22"
__licence__ = "GPLv2"

VERSION = "0.4"

import os
import re
import unicodedata
import optparse
from itertools import chain

import mutagen


_RE_REM_TITLE = re.compile(r'^(.+) - \d\d - (.+)$')
_RE_GET_DATE_FROM_CR = re.compile(r'^(\d\d\d\d)-\d\d-\d\dT')
_RE_CHECK_TRACK_NUM = re.compile(r'^(\d+)/(\d+)')


def _print_tags(tags):
    print '\n'.join('\t\t' + k + ': ' + str(v)
                    for k, v in sorted(tags.iteritems()))


def _print_changes(old, new):
    keys = dict((key, None) for key in chain(old.iterkeys(), new.iterkeys()))
    keys = sorted(keys.iterkeys())

    def _value2str(val):
        return val[0].encode(errors='replace') if val else ''

    for key in keys:
        old_v, new_v = _value2str(old.get(key)), _value2str(new.get(key))
        if old_v != new_v:
            print '\t\t%s: %r -> %r' % (key, old_v, new_v)


def _get_tag_value(tags, key):
    value = tags.get(key)
    if value:
        return value[0]
    return None


def _fix_filename_invalid_chars(name):
    return name.replace(u'Ł', 'L').replace('/', '-').replace('\\', '-').\
        replace('?', '').replace(':', '-').replace('*', ' ').\
        replace('  ', ' ')


def filename_from_tags(tags):
    tracknumber = tags.get('tracknumber')
    fname = None
    if tracknumber and tracknumber[0]:
        num = tracknumber[0].split('/')[0]
        fname = '%s. %s' % (num, tags['title'][0])
        discnumber = _get_tag_value(tags, 'discnumber')
        if discnumber:
            fname = str(discnumber) + fname
    else:
        artist = _get_tag_value(tags, _album_artist_tag(tags)) or \
            _get_tag_value(tags, 'artist')
        fname = _get_tag_value(tags, 'title')
        if artist:
            fname = artist + ' - ' + fname
    if not fname:
        return None
    fname = _fix_filename_invalid_chars(fname)
    return unicodedata.normalize('NFKD', fname).\
        encode('ascii', 'ignore').strip()


def filename_from_tags_single(tags):
    artist = _get_tag_value(tags, _album_artist_tag(tags)) or \
        _get_tag_value(tags, 'artist')
    fname = _get_tag_value(tags, 'title')
    if artist:
        fname = artist + ' - ' + fname
    if not fname:
        return None
    fname = _fix_filename_invalid_chars(fname)
    return unicodedata.normalize('NFKD', fname).\
        encode('ascii', 'ignore').strip()


def _parse_tracknum(tracknum):
    tracknum = tracknum.strip()
    if not tracknum:
        return None, None
    if '/' in tracknum:
        return [int(tr.strip()) for tr in tracknum.split('/')]
    return int(tracknum), None


def _album_artist_tag(tags):
    tag = 'albumartist'
    if hasattr(tags, 'ID3') and 'albumartist' not in tags.ID3.valid_keys:
        tag = 'performer'
    return tag


def __fix_tags_albumartist(tags):
    tag = _album_artist_tag(tags)
    if not tags.get(tag):
        if tags.get('artist'):
            artist = tags['artist'][0]
            if ' feat.' in artist:
                artist = artist.split(' feat.')[0]
            if ' feat ' in artist:
                artist = artist.split(' feat ')[0]
            artist = artist.strip(' [()]')
            tags[tag] = [artist]


def __fix_tracknumber_in_title(tags):
    tracknumber = _get_tag_value(tags, 'tracknumber')
    if not tracknumber:
        return tags
    title = _get_tag_value(tags, 'title')
    if not title:
        return tags
    if '/' in tracknumber:
        tnum, _ = tracknumber.split('/', 1)
    else:
        tnum = tracknumber
    if title.startswith(tnum):
        tags['title'] = title[len(tnum):].strip(' .')
        return tags
    discnumber = _get_tag_value(tags, 'discnumber')
    if not discnumber:
        return tags
    prefix = discnumber + tnum
    if title.startswith(prefix):
        tags['title'] = title[len(prefix):].strip(' .')
    return tags


def __fix_tags_album(tags, filename, idx, num_files, opts):
    c_track, c_alltracks = (idx + 1), num_files
    tracknumber = tags.get('tracknumber')
    if tracknumber and tracknumber[0] and not opts.force_renumber:
        c_track, c_alltracks = _parse_tracknum(tracknumber[0])
        if c_track == 0:
            print ('[W] Possible wrong track number'
                   ' - Track=0 for "%s"' % filename)
        if c_alltracks and c_alltracks != num_files:
            print ('[W] Wrong all track number in %s '
                   '(current: %s, all files: %s)' %
                   (filename, c_track, num_files))
        if not c_alltracks:
            c_alltracks = num_files
    tags['tracknumber'] = ["%02d/%02d" % (c_track, c_alltracks)]
    if opts.discnumber:
        if opts.discnumber == '-1':
            if 'discnumber' in tags:
                del tags['discnumber']
        else:
            tags['discnumber'] = [opts.discnumber]


def _fix_tags(tags, filename, idx, num_files, opts):
    __fix_tags_albumartist(tags)
    __fix_tracknumber_in_title(tags)
    if opts.opt_album:
        __fix_tags_album(tags, filename, idx, num_files, opts)
    elif opts.opt_single:
        if 'tracknumber' in tags:
            del tags['tracknumber']
        if 'discnumber' in tags:
            del tags['discnumber']
        if 'album' in tags:
            del tags['album']
    return tags


def __fix_jamendo_tags_year(tags):
    if not tags.get('date'):
        copyr = tags.get('copyright')
        if copyr and copyr[0]:
            year_re = _RE_GET_DATE_FROM_CR.match(copyr[0])
            if year_re and year_re.group(1):
                tags['date'] = [str(year_re.group(1))]


def _fix_jamendo_tags(tags, filename, _idx, num_files, _opts):
    # fix title
    artist = tags.get('artist')
    tags['performer'] = artist
    title = os.path.splitext(os.path.basename(filename))[0]
    if tags.get('title'):
        title = tags['title'][0]
    if title:
        mtitle = _RE_REM_TITLE.match(title)
        if mtitle:
            title = mtitle.group(2)
            tags['artist'] = mtitle.group(1)
    track = tags.get('tracknumber')
    if title and artist:
        if title.startswith(artist[0]):
            titlem = re.match(r'^(.+?) (\d+?) (.+)', title)
            if titlem and track:
                tags['artist'] = [titlem.group(1).strip()]
                title = titlem.group(3).strip()
        track = tags.get('tracknumber')
        if track and track[0] and title.startswith(track[0]):
            title = title[len(track[0]):].strip()
    if title:
        tags['title'] = [title]
    else:
        print '[E]: missing title'
    # fix year
    __fix_jamendo_tags_year(tags)
    return tags


def _fix_youtube_tags(tags, filename, _idx, _num_files, _opts):
    fmatch = re.match(r'(.+?) - (.+?)-(.+?)\....', filename)
    if fmatch:
        tags['artist'] = [fmatch.group(1)]
        tags['title'] = [fmatch.group(2)]
        return tags

    fmatch = re.match(r'(.+?)-(.+?)\....', filename)
    if fmatch:
        tags['title'] = [fmatch.group(1)]
        return tags

    print "[E] can't match filename"
    return tags


def _accepted_file(filename):
    return os.path.isfile(filename) and \
        os.path.splitext(filename)[1].lower() in ('.mp3', '.ogg')


def _rename_file(filename, tags, opts):
    curr_filename = os.path.basename(filename)
    curr_dir = os.path.dirname(filename)
    ext = os.path.splitext(curr_filename)[1]
    if opts.opt_single:
        dst_filename = filename_from_tags_single(tags)
    else:
        dst_filename = filename_from_tags(tags)
    if not dst_filename:
        print "[E] can't build filename from tags for:", curr_filename
        return
    dst_filename = dst_filename.lower() + ext
    if dst_filename != curr_filename:
        print '\tRename %s -> %s' % (curr_filename, dst_filename)
        if not opts.no_action:
            os.rename(filename, os.path.join(curr_dir, dst_filename))


def _rename_dir(dirnames, opts):
    dirnames = [dname
                for dname in dirnames or []
                if os.path.isdir(dname)]
    if not dirnames:
        print '[E] Missing dir names for rename'
        exit(-1)

    for dname in dirnames:
        print 'Processing %s' % dname
        # 1. find first file
        mfiles = [fname for fname in os.listdir(dname)
                  if _accepted_file(os.path.join(dname, fname))]
        dst_name = None
        for mfile in mfiles:
            tags = mutagen.File(os.path.join(dname, mfile), easy=True)
            date = tags.get('date')
            album = tags.get('album')
            if album and album[0]:
                if date and date[0]:
                    date = date[0].split('-')[0]
                    dst_name = " ".join((date, album[0]))
                else:
                    dst_name = album[0]
                dst_name = _fix_filename_invalid_chars(dst_name).lower()
                break
        else:
            print '[E] No media files in %s. Skipping...' % dname
            continue
        if dst_name is None:
            print '[E] No valid tags found in %s. Skipping...' % dname
        elif dst_name != dname:
            print '\tRenaming %s -> %s' % (dname, dst_name)
            if not opts.no_action:
                os.rename(dname, dst_name)


def _find_files(_opts, args):
    files = []
    for fname in args:
        fname = os.path.expanduser(fname)
        if os.path.isdir(fname):
            files.extend(fname
                         for fname in os.listdir(fname)
                         if _accepted_file(fname))
        elif _accepted_file(fname):
            files.append(fname)
    if not files:
        print 'Error: missing input files'
        exit(-1)

    return files


def _parse_opt():
    """ Parse cli options. """
    optp = optparse.OptionParser(version="%prog " + VERSION,
                                 description=__doc__)
    group = optparse.OptionGroup(optp, "Command")
    group.add_option('--rename', '-R', action="store_true", default=False,
                     help='rename files', dest="action_rename")
    group.add_option('--rename-dir', '-D', action="store_true", default=False,
                     help="rename given directory", dest="action_ren_dir")
    group.add_option('--fix-tags', '-F', action="store_true",
                     default=False,
                     help='fix common problems in tags',
                     dest="action_fix_tags")
    group.add_option('--fix-jamendo-tags', '-J', action="store_true",
                     default=False,
                     help='fix tags in files from Jamendo',
                     dest="action_fix_jamendo_tags")
    group.add_option('--fix-youtube-tags', '-Y', action="store_true",
                     default=False,
                     help='fix tags in files from Youtube',
                     dest="action_fix_youtube_tags")
    optp.add_option_group(group)
    group = optparse.OptionGroup(optp, "Options")
    group.add_option('--album', '-a', action="store_true", default=False,
                     help='treat all files as one album (default)',
                     dest="opt_album")
    group.add_option('--single', '-s', action="store_true", default=False,
                     help="don't create album",
                     dest="opt_single")
    group.add_option('--set-disc',
                     dest="discnumber",
                     help="set disc number; use -1 for remove",
                     metavar="DISC")
    group.add_option('--force-renumber', action="store_true",
                     default=False,
                     dest="force_renumber",
                     help="force set track numbers")
    optp.add_option_group(group)
    group = optparse.OptionGroup(optp, "Debug options")
    group.add_option('--debug', '-d', action="store_true", default=False,
                     help='enable debug messages')
    group.add_option('--verbose', '-v', action="store_true", default=False,
                     help='enable more messages')
    group.add_option('--no-action', '-N', action="store_true", default=False,
                     dest="no_action",
                     help="do not write anything; just show what would "
                          "have been done.")
    optp.add_option_group(group)
    return optp.parse_args()


def main(dirname='.'):
    opts, args = _parse_opt()
    if not opts.opt_single:
        opts.opt_album = True
    opts.action_fix_tags |= opts.action_fix_jamendo_tags | \
        opts.action_fix_youtube_tags
    if opts.action_ren_dir:
        _rename_dir(args, opts)
        return
    files = _find_files(opts, args)
    for idx, filename in enumerate(sorted(files)):
        print 'Processing:', filename
        tags = mutagen.File(filename, easy=True)
        org_tabs = dict(tags)
        if opts.debug:
            print '\tOriginal:'
            _print_tags(tags)
        if opts.action_fix_jamendo_tags:
            tags = _fix_jamendo_tags(tags, filename, idx, len(files), opts)
        if opts.action_fix_youtube_tags:
            tags = _fix_youtube_tags(tags, filename, idx, len(files), opts)
        if opts.action_fix_tags:
            tags = _fix_tags(tags, filename, idx, len(files), opts)
        if opts.debug:
            print '\tUpdated:'
            _print_tags(tags)
        if opts.verbose:
            print '\tChanges:'
            _print_changes(org_tabs, tags)
        if not opts.no_action and org_tabs != tags:
            tags.save()
            if opts.verbose:
                print 'Saving %s done' % filename
        elif opts.verbose:
            print 'No changes in %s' % filename
        if opts.action_rename:
            _rename_file(filename, tags, opts)


if __name__ == '__main__':
    main()
