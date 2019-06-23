/* -*- Mode: javascript; tab-width: 4; indent-tabs-mode: nil
   -*- coding=UTF-8 -*-
   Time-stamp: <2018-10-19 07:27:59 alex>

 --------------------------------------------------------------------
 hexo-near-post

 Copyright (C) 2016-2017  Alexandre Chauvin Hameau <ach@meta-x.org>

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
 --------------------------------------------------------------------
*/

"use strict";

var moment = require('moment');
var pathFn = require('path');
var I18n = require('hexo-i18n');

var path = pathFn.join(process.cwd(), 'near-post.json');
var dbNearPost;
var aAllPostsLink = {};

var near_limit = 2.0;
var near_enabled = false;
var near_posts = 3;
var near_heading = 'see also';

var conf = hexo.config.near_post;

if (conf !== undefined) {
    var f = parseFloat(conf.limit);
    if (f >= 0.0) { near_limit = f; }

    var i = parseInt(conf.posts);
    if (i >= 0) { near_posts = i; }

    if (conf.enabled) {
        near_enabled = true;
    }

    if (conf.heading !== undefined) {
        near_heading = conf.heading;
    }
}

if (near_enabled === false) {
    hexo.extend.filter.register('after_post_render', function(data) {
        data.content = data.content.replace(/@@@near_posts@@@/, '');
        return data;
    });
} else {

    hexo.log.info('near-post enabled limit='+near_limit+', posts='+near_posts);

    try {
        dbNearPost = require(path);
        hexo.log.info('read near post database from near-post.json');
    } catch(ex) {
        hexo.log.error('error reading near-post.json');
    }

    hexo.extend.filter.register('after_post_render', function(data) {
        if (dbNearPost === undefined) {
            hexo.log.error('no near post database');

            data.content = data.content.replace(/@@@near_posts@@@/, '');
            return data;
        }

        if (aAllPostsLink === undefined) { return; }

        if (data.layout === "post") {
            var aAdjPosts = [];
            for (var d in dbNearPost) {
                if (dbNearPost.hasOwnProperty(d)) {
                    var o = dbNearPost[d];

                    if (o.distance >= near_limit) {
                        if (o.file1 === data.source || 
                            o.file2 === data.source) {
                            if (o.file1 === data.source && o.file2 in aAllPostsLink) {
                                o.url = aAllPostsLink[o.file2].url;
                                o.title = aAllPostsLink[o.file2].title;
                                o.unixtime = aAllPostsLink[o.file2].time;
                            } else if (o.file1 in aAllPostsLink) {
                                o.url = aAllPostsLink[o.file1].url;
                                o.title = aAllPostsLink[o.file1].title;
                                o.unixtime = aAllPostsLink[o.file1].time;
                            }
                            aAdjPosts.push(o);
                        }
                    }
                }
            }

            aAdjPosts.sort(function(a,b){
                return parseFloat(a.distance) < parseFloat(b.distance);
            });

            if (data.language == "en") {
                if (conf.heading_en !== undefined) {
                    near_heading = conf.heading_en;
                }
            }
            if (data.language == "fr") {
                if (conf.heading_fr !== undefined) {
                    near_heading = conf.heading_fr;
                }
            }

            // build the item list
            var replace = "";
            for (var i in aAdjPosts) {
                if (i < near_posts) {
                    if (aAdjPosts[i].distance >= near_limit ) {
                        if (replace === '') {
                            replace = '<div id="near_posts"><h1>'+near_heading+'</h1><ul>';
                        }

                        replace += '<li>&nbsp;<span class="distance">['+aAdjPosts[i].distance.toFixed(2)+']</span>&nbsp;'+'<a href="'+aAdjPosts[i].url+'">'+aAdjPosts[i].title+'</a></li>';
                    }
                }
            }

            if (replace !== '') {
                replace += '</ul></div>';
            }

            data.content = data.content.replace(/@@@near_posts@@@/, replace);
            return data;
        }
    });

    hexo.extend.filter.register('before_post_render', function(data){
        if (data.layout === 'post') {
            aAllPostsLink[data.source] = {
                'url': data.path,
                'title': data.title,
                'time': moment(data.date).valueOf()
            };
        }
    });
}
