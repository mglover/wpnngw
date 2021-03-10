# wpnngw
## A WordPress-NetNews gateway

### overview

Translate between a WordPress blog and a NetNews group.

Uses the Wordpress REST API to fetch new posts and comments, and to 
create new comments to existing posts.

You must be running the INN news server on the local machine: articles 
are injected using the 'inews' executable.

### environment

wpnngw uses the directory $HOME/wpnngw_groups to store status and 
configuration data for gatewayed groups.  the environment variable 
WPNNGW_HOME can be used to override this.  If this directory does not 
exist, the tools will fail.  Data for each gatewayed group is stored in a subdirectory with the name 
of its gatewayed group.  

The subdirectory for each groups holds:

 * a 'history.json' with the name of the group, the URL of the 
wordpress site, the list of top-level posts, and the timestamp of the 
most recent post or comment that was processed.

 * the directories 'incoming', 'active', and 'processed' which hold 
NetNews-formatted files containing articles that, respectively, are 
awaiting processing, are currently being processed, and have been 
successfully posted to the group.  Any articles with processing errors 
can be found in the 'active' directory.

### usage

addgroup.py does the initial setup of the initial directory, 
subdirectories, and history.json file for a new group gateway.

update_news.py takes a group name as the only parameter, finds new 
articles from the source WordPress site, and posts them to the group

post_comment.py takes the filename of a NetNews-formatted file, parses 
it to determine the site and top-level post it applies to, and posts a 
comment using the REST API.

Posting requires 'rest_allow_anonymous_comments' to be set in the WP
site's config, by adding this line to your theme's functions.php:

add_filter( 'rest_allow_anonymous_comments', '__return_true' );

See:

https://developer.wordpress.org/reference/hooks/rest_allow_anonymous_comments/

user.py is a utility for managing a password file suitable for INN to 
use for authentication.

### TODO

addgroup sets new groups up to fetch all posts starting with the UNIX 
epoch.  This is unlikely what most users want: there should be a 
commandline option to set this.

there is no way to intercept posts through NNTP and get them to 
WordPress.  A python filter is an obvious choice here, but must still be 
written.





