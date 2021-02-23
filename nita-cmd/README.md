# NITA CMD

NITA CMD implements a very simple bash shell based command line interface to NITA.

In order to add new commands simply add a shell script starting with the name nita-cmd_<your command name> to the /usr/local/bin.
    
You can add multiple levels by using more than one underscore (i.e. nita-cmd_jenkins_<command name>).

Make it executable.

Add a script that sends a help message to STDOUT using the suffix _help.

Add inline debug by checking for the environment variable _CLI_RUNNER_DEBUG.

See some examples in the scripts/ directory.

