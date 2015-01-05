#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
EPUB info

Display information about epub file.

"""

__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2014"
__version__ = "2014-12-22"
__licence__ = "GPLv2"

VERSION = "0.1"


import os
import optparse
import zipfile
import xml.etree.ElementTree as et
import itertools
import operator


def check_file(filename):
    if not os.path.isfile(filename):
        print 'ERROR: its not a regular file'
        return False
    if not os.access(filename, os.R_OK):
        print 'ERROR: file is not readable'
        return False
    return True


CONTAINER_XML = 'META-INF/container.xml'
ROOTFILES_TAG = "{urn:oasis:names:tc:opendocument:xmlns:container}rootfiles"
ROOTFILE_TAG = "{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"


def get_content_opf_path(containter_xml):
    containter = et.fromstring(containter_xml)
    rootfiles = containter.find(ROOTFILES_TAG)
    if len(rootfiles) == 0:
        raise KeyError("rootfiles not found in container.xml")
    rootfile = rootfiles.find(ROOTFILE_TAG)
    if rootfile is None:
        raise KeyError("rootfile not found in container.xml")
    return rootfile.attrib["full-path"]


def get_opf(epub):
    """ Load content.opf file from epub. """
    try:
        with zipfile.ZipFile(epub, "r") as zipf:
            with zipf.open(CONTAINER_XML) as contf:
                content_filename = get_content_opf_path(contf.read())
            with zipf.open(content_filename, "r") as contentf:
                return contentf.read()
    except zipfile.BadZipfile, err:
        print 'ERROR: Wrong file - %s ' % err
    except KeyError, err:
        print 'ERROR: Wrong file - %s' % err
    except IOError, err:
        print 'ERROR: %s' % err
    return None


OPF_NS = '{http://www.idpf.org/2007/opf}'
MANIFEST_TAG = OPF_NS + 'metadata'
SCHEME_TAG = OPF_NS + "scheme"
ROLE_TAG = OPF_NS + "role"
PURL_NS = '{http://purl.org/dc/elements/1.1/}'


def process_opf_tag(elem):
    """ Process tags from opf namespace."""
    tag = elem.attrib['name']
    subtag = None
    if ':' in tag:
        tag, subtag = tag.split(':', 1)
    content = elem.attrib['content']
    return (tag, subtag, content, None)


def process_purl_tag(elem):
    """ Process tags from purl.org namespace."""
    tag = elem.tag[len(PURL_NS):]
    content = elem.text
    subtag = None
    attrib = elem.attrib.copy()
    if SCHEME_TAG in attrib:
        subtag = attrib.pop(SCHEME_TAG)
    elif ROLE_TAG in attrib:
        subtag = attrib.pop(ROLE_TAG)
    return (tag, subtag, content, attrib)


def process_opf(opf):
    """ Get tags from content opf file. """
    package = et.fromstring(opf)
    if len(package) == 0:
        return
    manifest = package.find(MANIFEST_TAG)
    if len(manifest) == 0:
        return
    for tag in manifest:
        if tag.tag.startswith(OPF_NS):
            if 'name' in tag.attrib:
                yield process_opf_tag(tag)
        elif tag.tag.startswith(PURL_NS):
            yield process_purl_tag(tag)


def get_full_filename(fname):
    """ Expand file path. """
    fname = os.path.expanduser(fname)
    fname = os.path.normpath(fname)
    return fname


def group_tags(elements):
    """ Group elements into groups by tag """
    elements = sorted(elements)
    groups = {key: list(group) for key, group
              in itertools.groupby(elements, key=operator.itemgetter(0))}
    return groups


GROUPS_SORT_PRIO = {
    'title': 0,
    'creator': 1,
    'identifier': 2,
    'language': 3,
    'publisher': 4,
    'subject': 5,
    'date': 6,
    'description': 10,
}


def sort_group_names(groups):
    """ Get sorted group names. Sort by priority and name. """

    def key_func(elem):
        return (GROUPS_SORT_PRIO.get(elem, 99), elem)

    return sorted(groups, key=key_func)


def show(groups):
    """ Display data."""
    for group_name in sort_group_names(groups.iterkeys()):
        group = groups[group_name]
        print '%-10s' % group_name.capitalize()
        for _group, lev2, value, attrs in group:
            print "\t%-10s\t%s" % (lev2 or '',
                                   value.encode('utf-8', errors='ignore')),
            if attrs:
                print '\t',
                print ';'.join(key + '=' + val.encode('utf-8', errors='ignore')
                               for key, val in attrs.iteritems()),
            print
        print


def _parse_opt():
    """ Parse cli options. """
    optp = optparse.OptionParser(usage="%prog [options] files",
                                 version="%prog " + VERSION,
                                 description=__doc__)
#    group = optparse.OptionGroup(optp, "Debug options")
#    group.add_option('--debug', '-d', action="store_true", default=False,
#                     help='enable debug messages')
#    optp.add_option_group(group)
    return optp.parse_args()


def main():
    _opts, args = _parse_opt()
    if not args:
        print 'ERROR: missing files to process'
        exit(-1)
    for fname in args:
        fname = get_full_filename(fname)
        print fname
        if check_file(fname):
            opf = get_opf(fname)
            if opf:
                elements = process_opf(opf)
                groups = group_tags(elements)
                show(groups)
        print

if __name__ == '__main__':
    main()
