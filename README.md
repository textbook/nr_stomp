nr_stomp
========

STOMP client for Network Rail's public data.

For more information, see [https://datafeeds.networkrail.co.uk][1].

Getting Started
---------------

Once you have installed the package, navigate to a suitable folder and use the 
command `run_client.py create config.cfg` to generate a blank configuration 
file. You can then edit the file to preset various configuration settings (e.g.
username and list of topics). Once you have filled in the configuration file, 
you can use the command `run_client.py run config.cfg` to execute a simple test 
routine.

To integrate `nr_stomp` into your own project, you can access the frames that
`NetworkRailClient.monitor` generates as follows:

    with NetworkRailClient(username, password, **config) as client:
        client.subscribe(topics)
        for frame in client.monitor(number_of_frames):
            ...

  [1]: https://datafeeds.networkrail.co.uk