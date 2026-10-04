# RefClash

A tiny read-only preflight for ASCII case-only and file/directory-prefix collisions in Git branch and tag names. Python 3.10+ and Git; no Python dependencies.

## Install and run

Download the single-file `refclash` release asset, then:

```sh
python3 refclash --repo .
python3 refclash --remote https://github.com/check-spelling-sandbox/runner-images-broken-tags.git --json
```

Or clone this repository and run `python3 refclash --repo /path/to/trusted/repository`.
The intentionally collision-bearing public example returns exit code **2**; that is a risk finding, not an execution failure.

For strictly offline inspection of an existing listing:

```sh
git for-each-ref --format='%(objectname)%09%(refname)' refs/heads refs/tags | python3 refclash --stdin --json
```

Default output shows counts and risk categories, never ref names or repository paths. Opt in with `--show-names` only if safe: branch names may contain private project identifiers. ASCII JSON escaping prevents terminal control characters from being emitted in names.

Exit codes: **0** no listed collision; **2** collision risk; **1** UNKNOWN (invalid/unreadable input, Git failure, timeout, invalid remote URL). Usage errors use argparse's conventional exit code 2; automation should parse JSON `status` for distinction.

## Safety

- No fetch, clone, push, rename, ref writes, repairs, sudo or telemetry.
- Local mode queries trusted repositories with `git for-each-ref`; stdin mode executes no subprocess and makes no network request.
- Remote mode is explicit opt-in and uses `git ls-remote` with HTTPS only, interactive prompts disabled and credential helpers disabled. Use public, credential-free URLs.
- Git itself and its environment/configuration must be trusted. Git HTTPS configuration (including rewrites, proxies, headers and TLS settings) can still apply; this utility is not a sandbox and cannot guarantee anonymous access under arbitrary Git config.
- No raw Git errors, URLs, object IDs or input contents in reports. A remote query contacts its server; it is not offline. Names are opt-in, not anonymized.

## Limitations

ASCII A-Z folding only: does not model Unicode normalization or every APFS/filesystem equivalence. Branch and tag namespaces are checked separately. Common directory names with different capitalization but distinct leaf names are not themselves ref collisions. No comparison against existing remote-tracking refs, custom fetch refspecs, packed-ref/reftable behavior, concurrent ref changes, filesystem case sensitivity or permissions. A risk may not break a specific clone; zero findings is **not** a clone/fetch guarantee or a compatibility certificate. Remote listing is a point-in-time snapshot, not validation of all objects.

Input is rejected above 8 MiB; Git commands time out after 30 seconds. Git subprocess output is captured before its size check, so this is not a strict subprocess memory cap. Empty successfully queried repositories produce zero checked refs. Do not pipe a failed producer into stdin and interpret empty input as verified remote success: use remote mode or check the producer's exit status.

## Example

Synthetic input with `refs/tags/V1` and `refs/tags/v1` produces:

```json
{"kind": "ascii_case", "ref_count": 2}
```

Review the names with the repository maintainer and use Git's native tools to choose a supported naming/storage approach. RefClash never changes it for you.

## Test

```sh
python3 -m py_compile refclash
python3 -m unittest discover -s tests -v
```

CI tests on macOS and Linux. Tests include a real temporary Git repository and verify its files are unchanged after inspection.

## References

- https://git-scm.com/docs/git-ls-remote
- https://git-scm.com/docs/git-for-each-ref

MIT licensed. This is an engineering preflight, not evidence of user demand or successful user outcomes.
