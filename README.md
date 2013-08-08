salt-eventsd
============

A event-listener daemon for saltstack that writes data into a database

It connects to the salt-masters event-bus and listens for all events. Depending on the configuration,
certain events can be collected into an event-queue and written into a database. 

Examples:

- collect all events with tag 'new_job' to have a job-history that lasts longer than saltstacks job-cache
- collect all job returns by matching on jids returned from minions to have a database with all returns you can index, search, etc.
- collect historic data like load average etc. by collecting events with tag 'load' which are created by your own load-monitoring module
- create and collect your own custom events with the data you want in an external database
- etc.

Why This is useful:
Currently saltstack does not have an external job-cache that works without a returner. Using returners and by that losing salt encryption
is not always desirable. With this daemon, you can collect all data right where its created and returned: on the salt-master.

More info will follow soon :-)

Features
========
- collect events from the salt-event-bus into a database
- use regular expressions for matching on tags, very flexible and powerful
- create your own sql-query-templates for inserting data into the database 
- fully saltstack-job-cache independant database to hold all data you want in it
- etc.


