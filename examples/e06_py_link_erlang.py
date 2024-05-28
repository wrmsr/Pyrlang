# Python -> link -> Erlang
#
# This example shows:
# 1. Linking to an Erlang process from Python and killing it remotely
# 2. An exit message will be delivered to Pyrlang PID which was linked to it.
#
# Run: `make example6a` in one terminal window, then `make example6b` in another
#

import logging

from term import Atom
from pyrlang.node import Node
from pyrlang.process import Process
from colors import color

LOG = logging.getLogger(color("EXAMPLE6", fg='lime'))


class LinkExample6(Process):
    def __init__(self) -> None:
        Process.__init__(self)

    def handle_one_inbox_message(self, msg):
        #
        # 1.1. Erlang node spawned a process for us and replied with a Pid
        #
        if isinstance(msg, tuple) and msg[0] == Atom("test_link"):
            LOG.info("LinkExample6: Linking to %s and killing", msg)
            n = self.get_node()
            n.link_nowait(self.pid_, msg[1])

            def exit_fn():
                n.exit_process(sender=self.pid_, receiver=msg[1],
                               reason=Atom("example6_link_exit"))
            loop = self.get_node().get_loop()
            loop.call_later(0.5, exit_fn)
        else:
            LOG.info("LinkExample6: Incoming %s", msg)

    def exit(self, reason=None):
        #
        # 1.2. Exiting remote linked process should also exit this process
        #
        LOG.info("LinkExample6: Received EXIT(%s)" % reason)
        Process.exit(self, reason)


def main():
    logging.root.addHandler(logging.StreamHandler())
    logging.root.setLevel(logging.DEBUG)

    node = Node(node_name="py@127.0.0.1", cookie="COOKIE")
    event_loop = node.get_loop()

    #
    # 1. Create a process P1
    #   Send a message to process example6 on the Erlang node with "test_link"
    #   command. This will spawn an Erlang process and tell us the pid.
    #   Reply from Erlang node will trigger next steps above in ExampleProcess6
    #
    p1 = LinkExample6()

    LOG.info("Sending {example6, test_link, %s} to remote 'example6'" % p1.pid_)
    remote_receiver_name = (Atom('erl@127.0.0.1'), Atom("example6"))

    def send_task():
        node.send_nowait(sender=p1.pid_,
                         receiver=remote_receiver_name,
                         message=(Atom("example6"), Atom("test_link"), p1.pid_))

    sleep_sec = 5
    LOG.info("Sleep %d sec" % sleep_sec)

    #
    # 3. End, sending a stop message
    #
    def task_sleep1():
        LOG.info(color("Stopping remote loop", fg="red"))
        node.send_nowait(sender=p1.pid_,
                         receiver=remote_receiver_name,
                         message=(Atom("example6"), Atom("stop")))

    def task_sleep2():
        node.destroy()
        LOG.error("Done")

    event_loop.call_soon(send_task)
    event_loop.call_later(sleep_sec, task_sleep1)
    event_loop.call_later(2 * sleep_sec, task_sleep2)
    node.run()


if __name__ == "__main__":
    main()
