# salt-eventsd

THIS IS STILL IN DEVELOPMENT AND IN ITS EARLY STAGES. NOT READY FOR PRODUCTION YET!

A event-listener daemon for saltstack that writes data into a database

It connects to the salt-masters event-bus and listens for all events. Depending on the configuration,
certain events can be collected into an event-queue and written into a database. 


### Usage Examples
- collect all events with tag 'new_job' to have a job-history that lasts longer than saltstacks job-cache
- collect all job returns by matching on jids returned from minions to have a database with all returns you can index, search, etc.
- collect historic data like load average etc. by collecting events with tag 'load' which are created by your own load-monitoring module
- create and collect your own custom events with the data you want in an external database
- etc.

### Why this is useful / Who needs this?
Currently saltstack does not have an external job-cache that works without a returner. Using returners and by that losing salt encryption
is not always desirable or mabye not even an option. With this daemon, you can collect all data right where its created and returned: on the salt-master.

While saltstacks job-cache works well in smaller environments, in larger environments the job-cache can become a burden for the salt-master. Especially
if the job-cache should be kept for a longer period of time, and im talking weeks and month here. This is where the salt-eventsd jumps in. With the
(current) mysql-backend, its easy to collect data for weeks and weeks without burdening the salt-master to keep track of jobs and their results in the
job-cache. The job-cache can be completely disabled because all the data is in the database, fully indexed, searcheable and easily cleaned up with a 
few querys.

More info will follow soon :-)

### Features
- collect events from the salt-event-bus into a database
- use regular expressions for matching on tags, very flexible and powerful
- create your own sql-query-templates for inserting data into the database 
- fully saltstack-job-cache independant database to hold all data you want in it
- etc.


