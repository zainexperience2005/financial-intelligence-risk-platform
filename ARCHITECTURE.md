# Architecture

The repository follows a reusable-kit/domain-application architecture.

```text
src/app -> src/kit
```

`src/kit` contains reusable Agentic AI infrastructure.

`src/app` contains Financial Intelligence & Risk Platform domain logic.

The kit must never import the application.

## Documentation

- [Full system architecture](docs/architecture/system.md)
- [Investigation data flow](docs/architecture/data-flow.md)
- [Security architecture](docs/architecture/security.md)
- [Architecture decisions](docs/adr/)
