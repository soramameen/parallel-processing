"""Loaders for graph edge-list files (SNAP format).

The SNAP datasets (e.g. ca-AstroPh) are plain text edge lists: comment lines
begin with ``#``, and each remaining line holds a ``u v`` pair separated by
whitespace (tab or space). Undirected graphs may list each edge in both
directions. Files are commonly gzip-compressed (``*.txt.gz``).
"""

from __future__ import annotations

import gzip
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO

# A vertex to its set of neighbours; matches parallel_processing.cliques.Graph.
Graph = dict[int, set[int]]


@contextmanager
def _open_text(path: Path) -> Iterator[IO[str]]:
    """Open ``path`` as text, transparently handling gzip by extension."""
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            yield handle
    else:
        with path.open("rt", encoding="utf-8") as handle:
            yield handle


def load_edge_list(path: str | Path) -> Graph:
    """Load a SNAP-format edge list into an undirected :data:`Graph`.

    - Lines beginning with ``#`` (comments) are skipped, as are blank lines.
    - Each edge line is ``u v`` with whitespace separation; vertex IDs are
      parsed as ``int``.
    - Self-loops (``u == v``) are dropped; duplicate edges are absorbed by the
      underlying sets, so listing an edge in both directions is harmless.
    - Every vertex seen (including isolated ones with no surviving edges) is
      registered as a key, so isolated vertices still appear as their own
      maximal clique.
    """
    graph: Graph = {}
    with _open_text(Path(path)) as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            u, v = int(parts[0]), int(parts[1])
            graph.setdefault(u, set())
            graph.setdefault(v, set())
            if u == v:
                continue
            graph[u].add(v)
            graph[v].add(u)
    return graph


def edge_count(graph: Graph) -> int:
    """Return the number of undirected edges in ``graph``."""
    return sum(len(neighbours) for neighbours in graph.values()) // 2
