# wpnngw
## A WordPress-NetNews gateway

### overview

Translate between a WordPress blog and a NetNews group.

Uses the Wordpress REST API to fetch new posts and comments, and to 
create new comments to existing posts.

You must be running the INN news server on the local machine: articles 
are injected using the 'inews' executable.

### files

this repository should be cloned into the pathspool directory specified 
in inn.conf.  This is usually '/var/spool/news'.  All files will be 
stored in $pathspool/wpnngw ('$wpnngw')

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

addgroup.py sets the group directory, queue directory, and history.json 
file for a new gatewayed group.

update_news.py takes a group names as the only parameters, finds new 
articles from the source WordPress sites, and posts them to the groups

gwmail.py intercepts articles mailed to group moderators and queue's 
them for posting.  

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

First, all gatewayed newsgroups need to be marked as moderated.  This 
will cause INN to look in the 'moderators' file to find the moderation 
email address.

Next, all gatewayed groups must have a matching line in the 'moderators' 
file, the email address for that line should be '%s@wpnngw.local'.

Finally, the 'mta' parameter in inn.conf must hold the full path to the 
gwmail.py executable.


### TODO

Convert quoted text<->html

gwmail silently drops all mail not for gatewayed group moderators.

can innd.conf hold configuration data for us?

addgroup sets new groups up to fetch all posts starting with the UNIX 
epoch.  This is unlikely what most users want: there should be a 
commandline option to set this.

addgroup should(?) run ctlinnd to create the group and set moderation 
status if necessary


