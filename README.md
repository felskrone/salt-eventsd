# salt-eventsd 
(a project based on but not related to saltstack)

A event-listener daemon for saltstack that writes data into mysql, postgres, statistical data into graphite, mongo,
etc. All events that occur on saltstacks eventbus can be handled and pushed to other daemons, databases, etc. You
decide yourself!

The daemon connects to the salt-masters event-bus and listens for all events. Depending on the configuration,
certain events can be collected by their tag and/or function-name and handed down to different workers. The 
workers then extract the desired data-fields from the return and process them further in a user-definable way.


### Usage Examples
- collect all events with tag 'new_job' to have a job-history that lasts longer than saltstacks job-cache
- collect all job returns by matching on job-return-tagged event returned from minions to have a database with all returns you can index, search, etc.
- filter events into different backends like graphite, mongodb, mysql, postgres, whatever...
- collect historic data like load average etc. by collecting events with tag 'load' which are created by your own load-monitoring module
- create and collect your own custom backends that process you event-data
- etc.

### Why this is useful / Who needs this?
Currently saltstack does not have an external job-cache that works without a returner. Using returners and by that losing salt encryption
is not always desirable or maybe not even be an option. With this daemon, you can collect all data right where its created and returned: on the salt-master.

While saltstacks job-cache works well in smaller environments, in larger environments the job-cache can become a burden for the salt-master. Especially
if the job-cache should be kept for a longer period of time, and im talking weeks and month here. This is where the salt-eventsd jumps in. With the
default mysql-backend, its easy to collect data for weeks and weeks without burdening the salt-master to keep track of jobs and their results in the
job-cache. 

Saltstacks job-cache can be completely disabled because all the data is in an independent database, fully indexed, searcheable and 
easily cleaned up and/or archived with a few querys.

In larger environments it is also a good idea, to seperate different services from one another. With salt-eventsd you can use saltstack for
communication and salt-eventsd to collect the actual data. The benefit is, that the salt-master does not need to be restarted just because changes
were done for example to a reactor or a runner.

### Features
- collect events from the salt-event-bus into a different backends
- collect a configurable amount of events before pushing them into different backends
- define Prio1 events that are pushed immediately without queing them first
- write your own backends with ease (some python knowledge required)
- use regular expressions for matching on events, very flexible and powerful
- have events send to two backends for having a command+return history as well as having the data pushed elsewhere
- create your own sql-query-templates for inserting data into the database 
- fully saltstack-job-cache independant database to hold all data you want in it
- example workers are found in the doc-directory

