# salt-eventsd

A project based on but not related to saltstack


## The current stable release is tagged as: 0.9.3

If you are already using salt-eventsd, check the changelog for the latest changes and fixes.

Due to public request, i pushed the develop-branch to github for everyone to try out. From today
on, the latest bleeding-edge salt-eventsd will always be in the develop branch with new release
getting tagged.

Please note, that i reserve the right to brake develop. Even though i always test all changes
locally before pushing them to github, it may happen.


### Updating from 0.9 to 0.9.3

See the changelog for improvements in 0.9.3. For more info see installation.txt.

IMPORTANT:
If you're coming from 0.9 make sure, that you make the following changes to your config:

Rename: 'stat_upd' to 'stat_timer'
Add: 'stat_worker: False' (see installation.txt for details on it)


### Availability Notes

#### Pypi

As of Jan 22nd, we are on pypi: https://pypi.python.org/pypi/salt-eventsd/

#### Debian / Ubuntu

A debian-package can be built straight from the repo by running 'dpkg-buildpackage -b'. All dependencies
have to be installed of course.


#### Redhat / CentOS

There are no packages for redhat yet. If you have the knowledge and the ressources to support that, feel
free to submit the necessary changes.


### What it does

A event-listener daemon for saltstack that writes data into mysql, postgres, statistical data into graphite, mongo,
etc. All events that occur on saltstacks eventbus can be handled and pushed to other daemons, databases, etc. You
decide yourself!

The daemon connects to the salt-masters event-bus and listens for all events. Depending on the configuration,
certain events can be collected by their tag and/or function-name and handed down to different workers. The
workers then extract the desired data-fields from the return and process them further in a user-definable way.


### Dependencies

Required python runtime dependencies:

 - salt >= 0.16.2
 - mysql-python
 - argparse
 - pyzmq

Optional/usefull dependencies

 - simplejson (Install with: pip install simplejson)


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
- define Prio1 events that are pushed immediately without queuing them first
- write your own backends with ease (some python knowledge required)
- use regular expressions for matching on events, very flexible and powerful
- have events send to two backends for having a command+return history as well as having the data pushed elsewhere
- create your own sql-query-templates for inserting data into the database
- fully saltstack-job-cache independant database to hold all data you want in it
- example workers are found in the doc-directory


### Testing

py.test is used to run all available tests.

To install all test dependencies you must first install all test dependencies by running

```
$ pip install -r dev-requirements.txt
```

It is reccomended to install all dependencies inside a virtualenv for easy isolation.

To run all tests simply the following in the root folder

```
py.test
```

Good options to use is `-x` for pdb debugging and `-s` for showing prints and log output.



### Benchmark

There is a simple benchmark script that can be used to test the performance of the code manually.

The script setups almost all required mocking and config inside the script.

Dependencies that is required is:

 - mock (pip install mock)

Copy the worker file `doc/share/doc/eventsd_workers/Bench_Worker.py` to `/etc/salt/eventsd_workers/Bench_Worker.py`

Run the script with `python benchmark.py`
