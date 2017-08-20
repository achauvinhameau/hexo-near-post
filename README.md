Purpose
=======

hexo-near-post is a tool that proposes article to be read near the one
currently consulted. 2 steps in the process, computing of the
proximity of all the posts and widget to display the nearest.

Install
=======

```
sudo pip install --upgrade -r requirements.txt
```

Calculating distance
====================

The python script (no time to build a node one yet)
hexo-nearest-compute.py is comparing all the posts one to one in order
to calculate a distance. Distance is based on number of same words in
both posts including description, tags, category, title.

This needs to be run each time a post is created or modified, no link
yet with the hexo generate process

typical usage:
```
python hexo-nearest-compute.py --path ~/blog/source/
```

Arguments:
 * --path: hexo source directory (where _posts will be found)
 * -f: force rebuild of the database
 * --database: link to the near-post.json file (should be at base of your hexo site)


