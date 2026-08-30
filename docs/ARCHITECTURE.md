# Architecture

```text
Phoenix Gateway
      │ RUN_AUTH / status
      ▼
AusweisApp SDK ───── TcToken / EAC transport ───── Phoenix eID Server
      │                                                   │
      │ APDU / reader                                     │ DV + terminal key
      ▼                                                   ▼
Phoenix virtual eID profile                         Phoenix test CVCA
```

The desktop gateway controls an installed AusweisApp over its local WebSocket
SDK. AusweisApp obtains a TcToken from this service and conducts the EAC
session. The selected virtual card must trust the CVCA that issued the server's
terminal chain.

The CSCA/Document Signer hierarchy is kept separate from the
CVCA/DV/terminal hierarchy. Only test credentials generated for the active
profile are used.

