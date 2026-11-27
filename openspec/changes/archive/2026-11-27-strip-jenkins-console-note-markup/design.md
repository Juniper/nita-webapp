## Context

Jenkins progressive text may include serialized `ConsoleNote` markers encoded
as ANSI escape sequences. Removing ANSI color sequences alone leaves those
markers in the emitted SSE data.

## Decision

Remove the serialized `ESC[8mha:…ESC[0m` marker from each progressive-text
chunk before splitting it into SSE lines. Preserve surrounding text and apply
the existing ANSI escape removal to the remaining output.

## Risks / Trade-offs

The marker format is an implementation detail of Jenkins. Keep the matcher
narrow so unrelated console text is not discarded.
