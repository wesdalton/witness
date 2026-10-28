# Scope of the earlier software counterexamples

The v1 Sol counterexamples invalidate two benchmark labels and reproduce locally.
That is a validated result about these recorded candidates. It does not by itself
establish previously unknown upstream bugs or violations of the libraries' own
public promises. No upstream issue or message has been posted.

For Werkzeug, the [release record](https://github.com/pallets/werkzeug/releases)
lists several previous multipart boundary repairs. [Issue 3088](https://github.com/pallets/werkzeug/issues/3088)
concerns leading CRLF leakage at a data-start boundary in 3.1.5 and was closed after
a repair. Our recorded counterexample concerns a trailing CR with small streaming
buffers in the pinned 3.1.9 candidate. These are distinguishable descriptions, but
the targeted search was not an exhaustive issue/source comparison, so priority
remains unestablished.

For Click, [issue 3458](https://github.com/pallets/click/issues/3458) and
[PR 3484](https://github.com/pallets/click/pull/3484) concern parameter-source access
during conversion/eager callbacks; the release record places that repair in 8.4.1.
Our failing local claim also required the initial prompt conversion to see PROMPT.
The [public API documentation](https://click.palletsprojects.com/en/stable/api/)
describes source values and when None is returned, but the inspected description
does not establish that stronger timing guarantee for initial prompt conversion.
Keep the finding as a local contract counterexample unless an upstream promise
and current-source reproduction establish more. Do not relabel it a novel library
defect simply because a stronger model exposed our benchmark error.
