# 1C integration

WFM backend works with 1C through a Windows Gateway:

`WFM backend -> HTTP -> Windows 1C Gateway -> COMConnector -> 1C infobase`

Direct COM is not available from Linux containers. The backend stores connection settings and encrypted secrets, checks gateway health, and requests employee status by INN.
