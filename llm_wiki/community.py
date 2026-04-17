from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List, Sequence, Tuple


def _page_key(page) -> Dict[str, object]:
    return {
        "id": page.page_id,
        "title": page.title,
        "path": page.relpath,
        "summary": page.summary,
        "tags": page.tags,
        "topics": page.topics,
        "entities": page.entities,
        "outbound_links": page.outbound_links,
    }


def _fallback_communities(pages: Sequence[object]) -> List[List[str]]:
    groups: Dict[str, List[str]] = defaultdict(list)
    for page in pages:
        key = (page.topics[0] if page.topics else page.relpath.split("/", 1)[0]).strip() or "misc"
        groups[key].append(page.page_id)
    return list(groups.values())


def build_communities(pages: Sequence[object], edges: Sequence[Dict[str, str]], inbound_counts: Counter[str]) -> Tuple[Dict[str, object], Dict[str, object], Dict[str, List[str]]]:
    try:
        import networkx as nx
    except Exception:
        nx = None  # type: ignore[assignment]

    page_map = {page.page_id: page for page in pages}

    if nx and pages:
        graph = nx.Graph()
        for page in pages:
            graph.add_node(page.page_id)
        for edge in edges:
            graph.add_edge(edge["source"], edge["target"])
        if graph.number_of_edges() > 0:
            raw_communities = [sorted(list(group)) for group in nx.algorithms.community.greedy_modularity_communities(graph)]
        else:
            raw_communities = _fallback_communities(pages)
    else:
        raw_communities = _fallback_communities(pages)

    page_to_communities: Dict[str, List[str]] = defaultdict(list)
    communities: List[Dict[str, object]] = []
    inter_edges: Counter[Tuple[str, str]] = Counter()

    for idx, members in enumerate(raw_communities, start=1):
        community_id = f"community-{idx:03d}"
        member_pages = [page_map[page_id] for page_id in members if page_id in page_map]
        tags = Counter()
        topics = Counter()
        entities = Counter()
        for page in member_pages:
            tags.update(page.tags)
            topics.update(page.topics)
            entities.update(page.entities)
            page_to_communities[page.page_id].append(community_id)

        representative = sorted(
            member_pages,
            key=lambda page: (-(len(page.outbound_links) + inbound_counts.get(page.page_id, 0)), page.relpath),
        )[0]
        summary = (
            f"{representative.title} 중심의 지식 군집입니다. "
            f"핵심 주제는 {', '.join(topic for topic, _ in topics.most_common(4)) or 'misc'}이며, "
            f"대표 문서는 {', '.join(page.title for page in member_pages[:4])} 입니다."
        )
        communities.append(
            {
                "id": community_id,
                "size": len(member_pages),
                "representative_page_id": representative.page_id,
                "representative_title": representative.title,
                "representative_path": representative.relpath,
                "summary": summary,
                "top_tags": tags.most_common(8),
                "top_topics": topics.most_common(8),
                "top_entities": entities.most_common(8),
                "page_ids": [page.page_id for page in member_pages],
                "paths": [page.relpath for page in member_pages],
                "titles": [page.title for page in member_pages],
            }
        )

    community_index = {community["id"]: community for community in communities}
    for edge in edges:
        source_communities = page_to_communities.get(edge["source"], [])
        target_communities = page_to_communities.get(edge["target"], [])
        for source_community in source_communities:
            for target_community in target_communities:
                if source_community == target_community:
                    continue
                pair = tuple(sorted((source_community, target_community)))
                inter_edges[pair] += 1

    community_graph = {
        "communities": communities,
        "edges": [
            {"source": source, "target": target, "weight": weight}
            for (source, target), weight in sorted(inter_edges.items())
        ],
    }
    community_summaries = {
        "communities": communities,
        "stats": {
            "community_count": len(communities),
            "largest_community_size": max((community["size"] for community in communities), default=0),
        },
    }
    return community_graph, community_summaries, dict(page_to_communities)
