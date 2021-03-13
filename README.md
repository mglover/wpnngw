# wpnngw
## A WordPress-NetNews gateway

### overview

Translate between a WordPress blog and a NetNews group.

Uses the Wordpress REST API to fetch new posts and comments, and to 
create new comments to existing posts.

Interacts with the INN news server running on the local machine.


### files

All files will be stored in the directory set as 'pathspool' in your 
inn.conf file, in a subdirectory named 'wpnngw'.

the directory $wpnngw/groups stores status and configuration data for 
gatewayed groups.  Data for each gatewayed group is stored in a 
subdirectory with the name of its gatewayed group.

The subdirectory for each groups holds:

 * 'history.json' contains the name of the group, the URL of the 
wordpress site, the list of top-level posts, and the timestamp of the 
most recent post or comment that was processed.

 * 'queue' is a directory holding articles from wordpress that are 
awaiting posting to the newsgroup.

$wpnngw/modqueue is a directory holding articles from newsgroups that are 
awaiting posting to wordpress.  

#### queues

the $group/queue and modqueue directories are designed to handle 
processing failures gracefully (thanks: DJB).  They contain three 
subdirectories:

 * 'new' holds incoming articles that have not yet been processed
 * 'cur' holds articles that are currently being processed, and retains 
any articles that have errors in processing
 * 'fin' holds articles that have successfully beenn processed


### executables

addgroup.py sets up the group directory, queue directory, and history.json 
file for a new gatewayed group.

update_news.py finds new wordpress posts and comments and posts them to 
newsgroups, and sends any newsgroup articles queued for moderation and 
sends them to wordpress.

gwmail.py intercepts articles posted to newsgroups and queues them to be 
posted to wordpress

user.py manages the $pathspool/users file for INN to use for 
authentication.


### wordpress configuration

Posting requires 'rest_allow_anonymous_comments' to be set in the WP
site's config, by adding this line to your theme's functions.php:

add_filter( 'rest_allow_anonymous_comments', '__return_true' );

See:

https://developer.wordpress.org/reference/hooks/rest_allow_anonymous_comments/


### INN configuration

wpnngw hooks into INNs moderation pathway to catch netnews posts and 
forward them to wordpress. 

First, the 'mta' parameter in inn.conf must hold the full path to the 
gwmail.py executable.

Next, all gatewayed groups must have a matching line in the 'moderators' 
file, the email address for that line should be '%s@wpnngw.local'.

Finally, all gatewayed newsgroups need to be marked as moderated.  This 
will cause INN to look in the 'moderators' file to find the moderation 
email address.  addgroup.py will automatically create groups as (or set 
existing groups to) moderated groups.


### wpnngw configuration

wpnngw is written for and probably requires python 3.  it certainly 
requires the following python modules:

 * dateutil (`pip install python-dateutil`)
 * Beautiful Soup (`pip install beautifulsoup4`)
 * lxml (`pip install lxml`)

wpnngw was developed and tested installed into pathspool/wpnngw 
directory. It probably will, and certainly should, work no matter where 
you install it, but YMMV.

Confirm that the INNCONF variable at the top of wpnngw/util.py points to 
your inn.conf file

You will need the full path to the wpnngw/wpnngw directory in PYTHONPATH.

 
### TODO

Convert quoted text<->html

gwmail silently drops all mail not for gatewayed group moderators.

can innd.conf hold configuration data for us?

addgroup sets new groups up to fetch all posts starting with the UNIX 
epoch.  This is unlikely what most users want: there should be a 
commandline option to set this.

