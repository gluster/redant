## Flask Log Server

Logs are important for two purposes, when we are developing the code and when the code fails and we want to find what went wrong. To access the logs quickly, the flask server tool was created. With a couple of changes in the dev env, users can run a poor man's flask server which server the redant log dir.

1. The log path and the port to be exposed needs to be updated inside the [log_access.ini](./log_access.ini) file.
2. After log path updation, one can simply run `python3 log_access.py`. This will start a debug flask server.

*An important note at this point is that this server is not aimed for production, hence one can simply run the python command but the server will die after certain number of requests. The following points show a path wherein we use pm2 for running the same debug server, but this time pm2 makes sure that the process is spun on death. BUT, BUT, BUT..this is still not how a production server is to be run. The purpose of this log server is to provide a quick peek into the log files and the dirs through the browser and that's it. If need be, one can lookup the ways of running a prod server ( maybe using wsgi or gunicorn combined with apache or nginx).*

3. Install node, followed by npm. Then install pm2. pm2 is basically a tool for those who are lazy enough to create daemons and write systemd files.
4. Post installation of pm2, one can use the [log_access.sh](./log_access.sh) to run the flask server. One just needs to run, `pm2 start log_acceess.sh`. Once you've run this command, pm2 will restart the flask server if it goes down.
5. One can quickly check whether the server is running by opening hostname/ip or server wherein this server is run:port number provided in config ( for example 1.1.1.1.1:5000/ )
