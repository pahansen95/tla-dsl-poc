System: TestLib
A simple test system.

The system uses these concepts:
- Client: unique identifier

The system maintains:

Client state:
  Each client has a state
  Initially idle

When a client connects:
  The client must be idle
  Then:
    - Client becomes active

System Constraints:

Valid States:
  All states must be defined

System Guarantees:

Progress:
  Clients eventually connect
