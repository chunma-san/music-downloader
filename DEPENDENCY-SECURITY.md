# Dependency security

For the certificate and image-processing fixes:

```sh
python -m pip install --upgrade certifi Pillow -c security-constraints.txt
python -m pip check
spotdl --help
```

Run checks as the account that runs the downloader. Package files installed by an administrator must remain readable by that account. Test image decoding and CLI startup before restarting a service; retain an exact environment backup for rollback.

Optional SpotDL releases may pin legacy FastAPI, Starlette and AnyIO versions. Do not override those requirements blindly or expose a legacy web server. Audit the complete resolved dependency set and use a compatible upstream release or a separately tested replacement. These constraints address only the named packages and are not a claim that every optional dependency is advisory-free.
