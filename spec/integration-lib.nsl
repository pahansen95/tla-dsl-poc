System: IntegrationLib

A toy integration library that brokers request/response work for a finite set of clients. The library models what must hold, not how it is implemented.

The system uses these concepts:
- Client Identity: unique identifier from finite set of clients
- Request: uninterpreted request token sent to external service
- Response: uninterpreted response token received from external service

The system maintains:

Client phases:
  Each client has exactly one phase (idle, waiting, done, or error)
  Initially all clients are idle

Pending requests:
  Each client may have one pending request or none
  Initially no clients have pending requests

Answer storage:
  Each client may have one stored response or none
  Initially no clients have stored responses

When a client sends a request:
  The client must be idle
  Then:
    - The client transitions to waiting
    - The request becomes pending for that client
    - All answers remain unchanged

When a client receives a response:
  The client must be waiting
  Then:
    - The client transitions to done
    - The response is stored as the client's answer
    - The pending request is cleared

When a request fails:
  The client must be waiting
  Then:
    - The client transitions to error
    - The pending request is cleared
    - All answers remain unchanged

When a client recovers from error:
  The client must be in error state
  Then:
    - The client transitions to idle
    - Pending requests and answers remain unchanged

System Constraints:

Type Safety:
  All phases must be valid states (idle, waiting, done, or error). All pending values must be valid requests or absent. All answer values must be valid responses or absent.

No Ghost Answers:
  An idle client must never have a stored answer.

System Guarantees:

Termination:
  Every client either remains idle or eventually reaches done phase.