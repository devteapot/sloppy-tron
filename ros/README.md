# ROS 2 Workspace

Target baseline:

- Raspberry Pi 5
- Ubuntu 24.04
- ROS 2 Jazzy LTS

Planned node graph:

- fake body state publisher
- servo bridge node
- camera state node
- audio state node
- gesture action server
- safety watchdog node
- SLOP adapter node

The ROS graph is the body-internal robotics substrate. Sloppy should see the
curated SLOP provider, not arbitrary ROS topics.
