#!/bin/sh
### BEGIN INIT INFO
# Provides:          salt-eventsd
# Required-Start:    $remote_fs $network
# Required-Stop:     $remote_fs $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: salt event listening daemon
# Description:       This is a daemon that listens for events and acts upon them
### END INIT INFO

# Author: Michael Prokop <mika@debian.org>

PATH=/sbin:/usr/sbin:/bin:/usr/bin
DESC="salt eventsd control daemon"
NAME=salt-eventsd
DAEMON=/usr/bin/salt-eventsd
DAEMON_ARGS="-d"
PIDFILE=/var/run/$NAME.pid
SCRIPTNAME=/etc/init.d/$NAME

# Exit if the package is not installed
[ -x "$DAEMON" ] || exit 0

# Read configuration variable file if it is present
[ -r /etc/default/$NAME ] && . /etc/default/$NAME

. /lib/lsb/init-functions

do_start() {
    # Return
    #   0 if daemon has been started
    #   1 if daemon was already running
    #   2 if daemon could not be started
    pid=$(pidofproc -p $PIDFILE $DAEMON)
    if [ -n "$pid" ] ; then
        return 1
    fi

    start-stop-daemon --start --quiet --pidfile $PIDFILE --exec $DAEMON -- \
            $DAEMON_ARGS \
            || return 2
}

do_stop() {
    # Return
    #   0 if daemon has been stopped
    #   1 if daemon was already stopped
    #   2 if daemon could not be stopped
    #   other if a failure occurred

    pids=$(pidof -x $DAEMON)

    # if pidof did not work, try looking into the pidfile
    if [ -z $pids ]
    then
        if [ -f ${PIDFILE} ]
        then
            pids=$(cat ${PIDFILE})
        fi  
    fi  
        
    if [ -z $pids ]
    then
        echo -e "\nFailed to determine salt-eventsd's pid" && return 2
    fi  

    if [ $? -eq 0 ] 
    then
        # salt-eventsd listens for signal 15
        echo $pids | xargs kill -15 2&1> /dev/null
        RETVAL=0
    else
        RETVAL=1
    fi  

    [ "$RETVAL" = 2 ] && return 2
    return "$RETVAL"
}

case "$1" in
    start)
        [ "$VERBOSE" != no ] && log_daemon_msg "Starting $DESC" "$NAME"
        do_start
        case "$?" in
            0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
              2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
        esac
        ;;
    stop)
        [ "$VERBOSE" != no ] && log_daemon_msg "Stopping $DESC" "$NAME"
        do_stop
        case "$?" in
            0|1) [ "$VERBOSE" != no ] && log_end_msg 0 ;;
              2) [ "$VERBOSE" != no ] && log_end_msg 1 ;;
        esac
        ;;
    status)
        status_of_proc "$DAEMON" "$NAME" && exit 0 || exit $?
        ;;
    #reload)
        # not implemented
        #;;
    restart|force-reload)
        log_daemon_msg "Restarting $DESC" "$NAME"
        do_stop
        case "$?" in
          0|1)
              do_start
              case "$?" in
                  0) log_end_msg 0 ;;
                  1) log_end_msg 1 ;; # Old process is still running
                  *) log_end_msg 1 ;; # Failed to start
              esac
              ;;
          *)
              # Failed to stop
              log_end_msg 1
              ;;
        esac
        ;;
    *)
        echo "Usage: $SCRIPTNAME {start|stop|status|restart|force-reload}" >&2
        exit 3
        ;;
esac

exit 0
