# -*- Mode: Python; python-indent-offset: 4 -*-
# -*- coding: utf-8 -*-
#
# Time-stamp: <2018-12-06 18:42:50 alex>
#
# --------------------------------------------------------------------
# hexo-near-post
#
# Copyright (C) 2016-2017  Alexandre Chauvin Hameau <ach@meta-x.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

"""
 parse all posts and compute the similarity level
"""

__version__ = "1.1"
__date__ = "23/06/2019-12:30:49"
__author__ = "Alex Chauvin"

# standard imports
import logging
import os
import sys
import re
import hashlib
import json

import textmining
import yaml
import pprint

# ----------- parse args
try:
    import argparse
    parser = argparse.ArgumentParser(description='hexo-near-post compute')

    parser.add_argument('--log', '-l', metavar='level', default='INFO', type=str, help='log level', nargs='?', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])

    parser.add_argument('--path', '-p', metavar='none', help='path to _posts directory', default='.', nargs='?')

    parser.add_argument('--database', '-d', metavar='none', help='path to near-post.json cache', default='.', nargs='?')

    parser.add_argument('--force', '-f', metavar='none', help='force build of cache', default=False, nargs='?')

    args = parser.parse_args()

except ImportError:
    logging.error('parse error - exit')
    exit()

if args.force is None:
    args.force = True

_logFormat = '%(asctime)-15s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s'
logLevel = logging.ERROR

if args.log == 'INFO':
    logLevel = logging.INFO
if args.log == 'DEBUG':
    logLevel = logging.DEBUG
if args.log == 'WARNING':
    logLevel = logging.WARNING
if args.log == 'ERROR':
    logLevel = logging.ERROR

logging.basicConfig(format=_logFormat, level=logLevel)

logging.info("starting")

# -----------------------------------
def read_stopwords(lang):
    """Returns a set of stopwords read from a file based on the language"""
    _stopwords = set()
    if lang not in ['fr', 'en']:
        logging.error("lang for stopwords not known")
        return

    _f = open(os.path.join(os.path.dirname(sys.argv[0]), 'stopwords-'+lang+'.txt'))
    for line in _f:
        word = line.strip()
        if not word:
            continue
        if word in _stopwords:
            continue
        _stopwords.add(word)
    _f.close()
    return _stopwords

# -----------------------------------
def computeDistance(rows):
    """compute the distance between 2 contents"""
    total = 0
    for i in range(len(rows[1])):
        if rows[1][i] > 0 and rows[2][i] > 0:
            total += rows[1][i] * rows[2][i]

    l = float(len(rows[0]))

    return total*1.0 / l**2 * 1000

# -------------------------------------
def extractYAMLpart(src):
    # extract the yaml part for description and keywords
    inFlag = False
    ylines = []
    for l in src.splitlines():
        if inFlag:
            if l == '---':
                inFlag = False
            else:
                ylines.append(l)
        else:
            if l == '---':
                inFlag = True

    if inFlag:
        logging.error("yaml format not correct in {}".format(fileName))
        return None

    return yaml.load("\n".join(ylines))

# -------------------------------------
def readAndCleanFile(fileName):
    """ read the post file (.md) and clean the content to get only words"""

    logging.debug("read and clean {}".format(fileName))

    _f = open(fileName, 'r')
    src = _f.read()
    _f.close()

    y = extractYAMLpart(src)

    # -------------------------
    def _build(k):
        """ build the string from the information in yaml section """
        if k is None:
            return ""

        if k in y and y[k] is not None:
            if isinstance(y[k], list):
                s = " ".join(y[k])
            else:
                s = y[k]
            return s.encode(encoding='UTF-8', errors='strict')

        return ""
        
    sKeywords = _build('keywords')
    sDescr = _build('description')
    sTags = _build('tags')
    sTitle = _build('title')

    # -------------------------
    def _clean(before, after, s):
        """ clean the content of the post and the descr + keywords """
        changed, subs = re.subn(before, after, s)
        if subs > 0:
            s = changed
        return s + " "

    for before, after in [('\\n', ''),
                          ('---.*---', ''),
                          ('https?:[^ ]*', ''),
                          ('{%[^%]*%}', ' '),
                          ('<!-- (more|less) -->', ''),
                          (r'\[[^\[]*\]\(http[^\)]*\)', ''),
                          ('[.,;:!_]', ' '),
                          ('à', 'a'), ('â', 'a'),
                          ('é', 'e'), ('è', 'e'), ('ê', 'e'), ('ë', 'e'),
                          ('ç', 'c'),
                          ('ù', 'u'),
                          ('<figure class', '</figure>'),
                          ('<twitter-widget ', '</twitter-widget>')]:
        src = _clean(before, after, src)
        sKeywords = _clean(before, after, sKeywords)
        sDescr = _clean(before, after, sDescr)
        sTags = _clean(before, after, sTags)
        sTags = _clean(before, after, sTitle)

    src += sTitle*2 + sDescr*2 + sKeywords*3 + sTags*4
    a = textmining.simple_tokenize_remove_stopwords(src)

    # look at french plural
    aPlurs = ['s', 'x']
    for w in a:
        if w[-1] not in aPlurs:
            for term in aPlurs:
                plur = w+term
                while plur in a:
                    i = a.index(plur)
                    a[i] = w

    return ' '.join(a)

# -------------------------------------
def isPublished(fileName, lang=None):
    """ check if the article is published and if same language as constraint """
    _f = open(fileName, 'r')
    src = _f.read()
    _f.close()

    y = extractYAMLpart(src)

    if lang is not None:
        if 'language' in y:
            if y['language'] != lang:
                return False

    if 'published' in y:
        return y['published']

    return True

# -------------------------------------
def getAllPostsName(lang=None):
    """get all the posts in the standard directory and push these into an array"""
    aPostFiles = []

    # compute all the files together in the path
    for dirname, _, filenames in os.walk(os.path.join(args.path, '_posts')):
        # print path to all filenames.
        for filename in filenames:
            if filename[-3:] == ".md":
                if isPublished(dirname+'/'+filename, lang):
                    dn = re.sub(re.sub('/', '\\/', os.path.join(args.path)), '', dirname)
                    aPostFiles.append(os.path.join(dn, filename))

    return aPostFiles

# -------------------------------------
def processDistance(f1, f2, dDistances, dCleanData):
    """evaluate distance between all the files in the posts directory"""
    k1 = hashlib.sha224(f1).hexdigest()
    k2 = hashlib.sha224(f2).hexdigest()
    k = str(k1)+'-'+str(k2)

    if k in dDistances:
        logging.info("{}-{} already in cache".format(f1, f2))
    else:
        if f1 in dCleanData:
            source1 = dCleanData[f1]
        else:
            source1 = readAndCleanFile(os.path.join(args.path, f1))

        if source1 is not None:
            if f2 in dCleanData:
                source2 = dCleanData[f2]
            else:
                source2 = readAndCleanFile(os.path.join(args.path, f2))

            if source2 is not None:
                tdm = textmining.TermDocumentMatrix()
                tdm.add_doc(source1)
                tdm.add_doc(source2)

                dCleanData[f1] = source1
                dCleanData[f2] = source2

                aRes = []
                for row in tdm.rows(cutoff=1):
                    aRes.append(row)

                d = computeDistance(aRes)

                r = {
                    'distance': d,
                    'file1': f1,
                    'file2': f2
                }

                if d < 0.5:
                    r['confidence'] = "very low"
                elif d < 1.0:
                    r['confidence'] = "low"
                elif d < 3.0:
                    r['confidence'] = "average"
                elif d < 5.0:
                    r['confidence'] = "good"
                else:
                    r['confidence'] = "very good"

                dDistances[k] = r

# -------------------------------------
def main():
    """main function, need to be split"""

    # -------------------------------------
    # init the stopwords for french
    # add the french stopwords to the english already contained in the package
    #
    textmining.stopwords.clear()
    textmining.stopwords.update(read_stopwords('fr'))

    aPostFiles_FR = getAllPostsName('fr')

    # prepare text mining
    dCleanData = {}
    dDistances = {}

    if not args.force and os.path.exists('near-post.json'):
        try:
            _f = open("near-post.json", 'r')
            dDistances = json.load(_f)
            _f.close()
        except IOError:
            logging.warning("access error to the near-post.json file")

    for f1 in aPostFiles_FR:
        logging.info("process distance around {}".format(f1))
        for f2 in aPostFiles_FR:
            if f1 < f2:
                processDistance(f1, f2, dDistances, dCleanData)


    # -------------------------------------
    # init the stopwords for english
    #
    textmining.stopwords.clear()
    textmining.stopwords.update(read_stopwords('en'))

    aPostFiles_FR = getAllPostsName('en')

    if not args.force and os.path.exists('near-post.json'):
        try:
            _f = open("near-post.json", 'r')
            dDistances = json.load(_f)
            _f.close()
        except IOError:
            logging.warning("access error to the near-post.json file")

    for f1 in aPostFiles_FR:
        logging.info("process distance around {}".format(f1))
        for f2 in aPostFiles_FR:
            if f1 < f2:
                processDistance(f1, f2, dDistances, dCleanData)


    logging.info("writing near-post.json file")

    f = open(os.path.join(args.database, "near-post.json"), 'w')
    json.dump(dDistances, f)
    f.close()

if __name__ == "__main__":
    main()
