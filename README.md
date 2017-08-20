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

hexo plugin
===========

installation from your hexo site directory:
```
npm install hexo-near-post --save
```

in the _config.yml file, add the following section and configure it as you prefer:
```
near_post:
  enabled: true
  limit: 2
  posts: 3
  heading: see also
```

* enabled could be turned false if you simply want to disable all the
  near post section in your articles
* limit: minimum affinity between post
* posts: number of post to link with if available
* heading: name of the section (h2 tag used)

you can tweek your css for the near_post section:
```
#near_posts {
  h2 {
    font-size: 1.4em;
    margin-bottom: 0px;
  }

  ul {
    margin-left: 20px;
  }
}
```

finaly on each post you want the near_post section to be added, insert a specific tag:
```
@@@near_posts@@@
```

you can add it by default in the scaffolds/post.md file
