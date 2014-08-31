#!/bin/sh
### BEGIN INIT INFO
# Provides:          he-wp-firmware-bnx2
# Required-Start:    $network $local_fs
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: <Enter a short description of the sortware>
# Description:       <Enter a long description of the software>
#                    <...>
#                    <...>
### END INIT INFO

# Author: root <root@xhdev1.webpack.hosteurope.de>

# PATH should only include /usr/* if it runs after the mountnfs.sh script
PATH=/sbin:/usr/sbin:/bin:/usr/bin
DESC="listening daemon for saltstack events"
NAME="salt-eventsd"
DAEMON=/usr/bin/salt-eventsd
DAEMON_ARGS="-d"             # Arguments to run the daemon with
PIDFILE=/var/run/$NAME.pid
STATUSFILE=/var/run/$NAME.status
SCRIPTNAME=/etc/init.d/$NAME

# Exit if the package is not installed
[ -x $DAEMON ] || exit 0

# Read configuration variable file if it is present
[ -r /etc/default/$NAME ] && . /etc/default/$NAME

# Load the VERBOSE setting and other rcS variables
. /lib/init/vars.sh

# Define LSB log_* functions.
# Depend on lsb-base (>= 3.0-6) to ensure that this file is present.
. /lib/lsb/init-functions

do_start()
{
    start-stop-daemon --start --exec $DAEMON -- $DAEMON_ARGS
}

do_stop()
{
    start-stop-daemon --stop --pidfile /var/run/salt-eventsd.pid --signal 15
}

case "$1" in
  start)
    do_start
  ;;
  stop)
	[ "$VERBOSE" != no ] && log_daemon_msg "Stopping $DESC" "$NAME"
	do_stop
	;;

  status)
       status_of_proc "$DAEMON" "$NAME" && exit 0 || exit $?
       ;;

  restart)
	do_stop
        # do a sleep because the daemon takes 3secs to shutdown
        sleep 3
        do_start
	;;
  *)
	echo "Usage: $SCRIPTNAME {start|stop|status|restart|force-reload}" >&2
	exit 3
	;;
esac

:
