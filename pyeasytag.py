#!/usr/bin/python
""" Fix tags in files from Jamendo; rename files. """

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
        return str(val[0]) if val else ''

    for key in keys:
        old_v, new_v = _value2str(old.get(key)), _value2str(new.get(key))
        if old_v != new_v:
            print '\t\t%s: %r -> %r' % (key, old_v, new_v)


def filename_from_tags(tags):
    tracknumber = tags.get('tracknumber')
    if tracknumber and tracknumber[0]:
        num = tracknumber[0].split('/')[0]
        fname = '%s. %s' % (num, tags['title'][0])
    else:
        fname = '%s - %s' % (tags['performer'][0], tags['title'][0])
    return unicodedata.normalize('NFKD', fname).encode('ascii', 'ignore')


def _parse_tracknum(tracknum):
    tracknum = tracknum.strip()
    if not tracknum:
        return None, None
    if '/' in tracknum:
        return [int(tr.strip()) for tr in tracknum.split('/')]
    return int(tracknum), None


def _fix_tags(tags, filename, idx, len_files, opts):
    # fix performer
    if not tags.get('performer'):
        if tags.get('artist'):
            artist = tags['artist'][0]
            if 'feat.' in artist:
                artist = artist.split('feat.')[0]
            artist = artist.strip(' [()]')
            tags['performer'] = [artist]
    if len_files == 1:
        # remove track number when only one file
        if 'tracknumber' in tags:
            del tags['tracknumber']
    else:
        if opts.opt_album:
            c_track, c_alltracks = idx, len_files
            tracknumber = tags.get('tracknumber')
            if tracknumber and tracknumber[0]:
                c_track, c_alltracks = _parse_tracknum(tracknumber[0])
                if c_alltracks and c_alltracks != len_files:
                    print ('[W] Wrong all track number in %s '
                           '(current: %s, all files: %s)' %
                           (filename, idx, len_files))
                if not c_alltracks:
                    c_alltracks = len_files
            tags['tracknumber'] = ["%02d/%02d" % (c_track, c_alltracks)]
        else:
            # TODO: single mode?
            if 'tracknumber' in tags:
                del tags['tracknumber']
    return tags


def _fix_jamendo_tags(tags, filename, idx, len_files, _opts):
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
    return tags


def _parse_opt():
    """ Parse cli options. """
    optp = optparse.OptionParser("pyEasyTag")
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
    optp.add_option_group(group)
    group = optparse.OptionGroup(optp, "Options")
    group.add_option('--find-files', '-f', action="store_true", default=False,
                     help='find files in current directory',
                     dest="find_files")
    group.add_option('--album', '-a', action="store_true", default=False,
                     help='treat all files as one album',
                     dest="opt_album")
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


def _accepted_file(filename):
    return os.path.isfile(filename) and \
        os.path.splitext(filename)[1].lower() in ('.mp3', '.ogg')


def _rename_file(filename, tags, opts):
    curr_filename = os.path.basename(filename)
    curr_dir = os.path.dirname(filename)
    ext = os.path.splitext(curr_filename)[1]
    dst_filename = filename_from_tags(tags) + ext
    dst_filename = dst_filename.lower()
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
                dst_name = dst_name.lower()
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


def _find_files(opts, args):
    if opts.find_files:
        files = [fname for fname in os.listdir('.') if _accepted_file(fname)]
    else:
        files = [fname for fname in args if _accepted_file(fname)]
    if not files:
        print 'Error: missing input files'
        exit(-1)

    return files


def main(dirname='.'):
    opts, args = _parse_opt()
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
        if opts.action_fix_tags:
            tags = _fix_tags(tags, files, idx, len(files), opts)
        if opts.debug:
            print '\tUpdated:'
            _print_tags(tags)
        if opts.verbose:
            print '\tChanges:'
            _print_changes(org_tabs, tags)
        if not opts.no_action:
            tags.save()
        if opts.verbose:
            print 'Saving %s done' % filename
        if opts.action_rename:
            _rename_file(filename, tags, opts)


if __name__ == '__main__':
    main()
