from datetime import timedelta

import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import MessageRepository
from app.schemas import (
    CentralityItem,
    NetworkAnalyticsResponse,
    NetworkCommunity,
    NetworkEdge,
    NetworkNode,
)

MAX_NODES = 50


class NetworkAnalytics:
    @staticmethod
    async def analyze(db: AsyncSession, group_id: int) -> NetworkAnalyticsResponse:
        messages = await MessageRepository(db).get_by_group(group_id)

        graph = nx.DiGraph()
        for i, msg in enumerate(messages):
            graph.add_node(msg.sender_name)
            if i > 0:
                prev = messages[i - 1]
                if prev.sender_name != msg.sender_name:
                    delta = msg.timestamp - prev.timestamp
                    if delta <= timedelta(minutes=2):
                        weight = graph.get_edge_data(prev.sender_name, msg.sender_name, {}).get("weight", 0) + 1
                        graph.add_edge(prev.sender_name, msg.sender_name, weight=weight)

        if graph.number_of_nodes() == 0:
            return NetworkAnalyticsResponse(
                nodes=[], edges=[], density=0.0, communities=[], centrality=[]
            )

        degrees = dict(graph.degree())
        top_nodes = sorted(degrees.keys(), key=lambda n: degrees[n], reverse=True)[:MAX_NODES]
        subgraph = graph.subgraph(top_nodes).copy()

        nodes = [NetworkNode(id=node, degree=subgraph.degree(node)) for node in subgraph.nodes()]
        edges = [
            NetworkEdge(source=u, target=v, weight=data.get("weight", 1))
            for u, v, data in subgraph.edges(data=True)
        ]

        density = round(nx.density(subgraph), 4) if subgraph.number_of_nodes() > 1 else 0.0

        undirected = subgraph.to_undirected()
        communities_raw = list(nx.community.greedy_modularity_communities(undirected))
        communities = [
            NetworkCommunity(cluster_id=idx, members=sorted(members))
            for idx, members in enumerate(communities_raw)
        ]

        centrality_raw = nx.degree_centrality(subgraph)
        centrality = [
            CentralityItem(user=user, score=round(score, 4))
            for user, score in sorted(centrality_raw.items(), key=lambda x: x[1], reverse=True)
        ]

        return NetworkAnalyticsResponse(
            nodes=nodes,
            edges=edges,
            density=density,
            communities=communities,
            centrality=centrality,
        )
