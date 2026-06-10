import graphviz

from app.exceptions.graph_exceptions import (
    DuplicateNodeException,
    DuplicateEdgeException,
    NodeDoesNotExistException,
    EdgeDoesNotExistException,
    InvalidNodeNameException,
)


class Node:
    """Node class for the graph. Each node has an id, a label and a dictionary of data."""

    def __init__(
        self,
        id: str | int,
        label: str = "",
        data: dict[str, str | int | float] | None = None,
        attributes: dict[str, str | int | float] | None = None,
    ) -> None:
        """Initializes the Node object.

        Parameters
        ----------
        id : str | int
            The id of the node.
        label : str, optional
            The label of the node. If not provided, the id is used as the label, by default "".
        data : dict[str, str  |  int  |  float] | None, optional
            A dictionary of data for the node, by default None.
        attributes : dict[str, str | int | float] | None, optional
            Additional Graphviz attributes of the node, by default None.
        """
        self.id: str = str(id)
        if label:
            self.label: str = label
        else:
            self.label: str = str(id)
        self.__data: dict[str, str | int | float] | None = None
        self.attributes: dict[str, str | int | float] | None = {}
        self.set_data(data)
        self.set_attributes(attributes)

    def get_label(self) -> str:
        """Returns the label of the node.

        Returns
        -------
        str
            The label of the node.
        """
        return self.label

    def get_id(self) -> str:
        """Returns the id of the node.

        Returns
        -------
        str
            The id of the node.
        """
        return self.id

    def set_data(self, data: dict[str, str | int | float] | None) -> None:
        """Set the data stored in the node.

        Parameters
        ----------
        data : dict[str, str  |  int  |  float]
            The new node data.
        """
        if data is not None:
            self.__data = data.copy()
        else:
            self.__data = None

    def get_data(self) -> dict[str, str | int | float] | None:
        """Returns the data of the node.

        Returns
        -------
        dict[str, str | int | float]
            The data of the node.
        """
        return self.__data

    def set_attributes(self, attributes: dict[str, str | int | float] | None) -> None:
        """Set the Graphviz attributes of the node.

        Parameters
        ----------
        attributes : dict[str, str  |  int  |  float] | None
            New attributes of the node.
        """
        if attributes is not None:
            self.attributes = attributes.copy()
        else:
            self.attributes = {}

    def get_attributes(self) -> dict[str, str | int | float]:
        """Returns the Graphviz attributes of the node.

        Returns
        -------
        dict[str, str | int | float]
            The attributes of the node.
        """
        return self.attributes

    def get_data_from_key(self, key: str) -> str | int | float | None:
        """Returns the value of the data corresponding to the key.

        Parameters
        ----------
        key : str
            The key of the data.

        Returns
        -------
        str | int | float | None
            The value of the data corresponding to the key.
        """
        if not self.__data:
            return None
        if key not in self.__data:
            return None
        return self.__data[key]


class Edge:
    """Edge class for the graph. Each edge has a source, a destination and a weight."""

    def __init__(
        self,
        source: str | int,
        destination: str | int,
        weight: int = 1,
        data: dict[str, str | int | float] | None = None,
    ) -> None:
        """Initializes the Edge object.

        Parameters
        ----------
        source : str | int
            source node id
        destination : str | int
            destination node id
        weight : int, optional
            weight of the edge, by default 1
        data : dict[str, str | int | float] | None, optional
            Additional data attached to the edge, by default None
        """
        self.source = str(source)
        self.destination = str(destination)
        self.weight = weight
        self.data = data

    def get_edge(self) -> tuple[str, str, int]:
        """Returns the source, destination and weight of the edge.

        Returns
        -------
        tuple[str, str, int]
            The source, destination and weight of the edge.
        """
        return (self.source, self.destination, self.weight)

    def get_data(self) -> dict[str, str | int | float] | None:
        """Return the data attached to the edge."""
        return self.data

    def get_data_from_key(self, key: str) -> str | int | float | None:
        """Return the value stored under ``key`` in the edge data if present."""
        if not self.data:
            return None
        return self.data.get(key)


class BaseGraph:
    """BaseGraph class for the graph. The class contains the nodes and edges of the graph
    and provides methods to add nodes and edges, get nodes and edges, check if a node or edge exists, and get the graphviz string of the graph.
    This class is a wrapper around the graphviz.Digraph class with additional functionality.
    This class is used as a base class for the other graph classes.
    """

    def __init__(
        self,
        **graph_attributes,
    ) -> None:
        """Initializes the BaseGraph object.

        Parameters
        ----------
        **graph_attributes
            Additional attributes for the graph. For further information, see the graphviz documentation.
        """
        self.nodes: dict[str, Node] = {}
        self.edges: dict[tuple[str, str], Edge] = {}

        self.graph = graphviz.Digraph(
            strict=True,
            graph_attr={"fontname": "Montserrat"},
            node_attr={"fontname": "Montserrat"},
            edge_attr={"fontname": "Montserrat"},
        )

        self.graph.attr("graph", **graph_attributes)

        from app.config import colon_substitute

        self.colon_substitute: str = colon_substitute

        # UI feature: optionally highlight Happy Path
        # Separate state so one can toggle highlighting without re-mining the whole model.
        self._highlighted_node_ids: set[str] = set()
        self._invisible_node_ids: set[str] = set()
        self._invisible_edge_ids: set[tuple[str, str]] = set()
        self._highlight_fillcolor = "#FFE08A"
        self._highlight_bordercolor = "#D97B00"

    def clear_highlighted_nodes(self) -> None:
        """Remove all node highlighting."""
        self._highlighted_node_ids = set()

    def highlight_happy_path(self, happy_path_events: set[str] | list[str]) -> None:
        """Highlight nodes of to the given Happy Path activities.

        Direct match -> highlight nodes whose id equals an activity label.
        - Fuzzy miner clusters -> highlight cluster nodes if they contain a Happy Path activity.
        """
        event_set = {str(event) for event in happy_path_events}
        highlighted = {event for event in event_set if self.contains_node(event)}

        for node in self.get_nodes():
            data = node.get_data() or {}
            merged_nodes = data.get("Nodes")
            if not merged_nodes:
                continue

            for merged_node in merged_nodes:
                merged_id = str(merged_node.get("id", ""))
                if merged_id in event_set:
                    highlighted.add(node.get_id())
                    break

        self._highlighted_node_ids = highlighted

    def set_invisible_nodes(self, current_node_ids: list[str]) -> None:
        """Mark nodes missing from the current graph as invisible.

        Parameters
        ----------
        current_node_ids : list[str]
            List of all node ids present in current filtered graph.
        """
        self._invisible_node_ids = set()
        for node in self.get_nodes():
            if node.get_id() not in current_node_ids:
                self._invisible_node_ids.add(node.get_id())

    def update_visible_nodes(self, current_nodes: list[Node]) -> None:
        """Update labels, data and visual attributes of nodes that exist in both graphs.

        Parameters
        ----------
        current_nodes : list[Node]
            The filtered nodes of current graph.
        """
        for node in current_nodes:
            node_id = node.get_id()
            if not self.contains_node(node_id):
                continue

            fixed_node = self.get_node(node_id)
            fixed_node.label = node.get_label()
            fixed_node.set_data(node.get_data())
            fixed_node.set_attributes(node.get_attributes())

    def set_invisible_edges(self, edges: list[Edge]) -> None:
        """Mark edges missing from current graph as invisible.

        Parameters
        ----------
        edges : list[Edge]
            List of all edges that are present in current filtered graph.
        """
        self._invisible_edge_ids = set()

        edge_ids = {(edge.source, edge.destination) for edge in edges}
        for source_id, target_id in self.edges.keys():
            if (
                (source_id, target_id) not in edge_ids
                or source_id in self._invisible_node_ids
                or target_id in self._invisible_node_ids
            ):
                self._invisible_edge_ids.add((source_id, target_id))

    def add_node(
        self,
        id: str | int,
        label: str = "",
        data: dict[str, str | int | float] = None,
        **node_attributes,
    ) -> None:
        """Adds a node to the graph. If the node id contains the colon, it is replaced with the colon substitute.

        Parameters
        ----------
        id : str | int
            The id of the node.
        label : str, optional
            The label of the node, by default "".
        data : dict[str, str  |  int  |  float], optional
            A dictionary of data for the node, by default None.
        **node_attributes
            Additional attributes for the node. For further information, see the graphviz documentation.

        Raises
        ------
        InvalidNodeNameException
            If the id contains the colon substitute.
        DuplicateNodeException
            If the node already exists in the graph.
        """

        if self.colon_substitute in str(id):
            raise InvalidNodeNameException(id)

        if self.contains_node(id):
            raise DuplicateNodeException(id)

        if "filled" not in node_attributes.get("style", ""):
            if "style" in node_attributes:
                node_attributes["style"] += ", filled"
            else:
                node_attributes["style"] = "filled"

        node = Node(id, label, data, attributes=node_attributes.copy())
        self.nodes[node.get_id()] = node

        graphviz_id = self.substitute_colons(node.get_id())
        self.graph.node(graphviz_id, node.get_label(), **node_attributes)

    def add_start_node(self, id: str = "Start") -> None:
        """Adds a start node to the graph.

        Parameters
        ----------
        id : str, optional
            The id of the start node, by default "Start".
        """
        self.add_node(id, shape="circle", style="filled, bold", fillcolor="green")

    def add_end_node(self, id: str = "End") -> None:
        """Adds an end node to the graph.

        Parameters
        ----------
        id : str, optional
            The id of the end node, by default "End".
        """
        self.add_node(id, shape="doublecircle", style="filled, bold", fillcolor="red")

    def add_starting_edges(
        self,
        nodes: list[str | int],
        starting_node: str = "Start",
        weights: list[int] = None,
        **edge_attributes,
    ) -> None:
        """Adds edges from the start node to the nodes in the list.

        Parameters
        ----------
        nodes : list[str  |  int]
            The list of node ids.
        starting_node : str, optional
            The id of the start node, by default "Start".
        weights : list[int], optional
            The list of weights for the edges, by default None.
        """
        if not nodes:
            return

        if "penwidth" not in edge_attributes:
            edge_attributes["penwidth"] = "0.1"

        for node in nodes:
            if weights:
                self.add_edge(
                    starting_node,
                    node,
                    weights[nodes.index(node)],
                    **edge_attributes,
                )
            else:
                self.add_edge(starting_node, node, weight=None, **edge_attributes)

    def add_ending_edges(
        self,
        nodes: list[str | int],
        ending_node: str = "End",
        weights: list[int] = None,
        **edge_attributes,
    ) -> None:
        """Adds edges from the nodes in the list to the end node.

        Parameters
        ----------
        nodes : list[str  |  int]
            The list of node ids.
        ending_node : str, optional
            The id of the end node, by default "End".
        weights : list[int], optional
            The list of weights for the edges, by default None.
        """
        if not nodes:
            return

        if "penwidth" not in edge_attributes:
            edge_attributes["penwidth"] = "0.1"

        for node in nodes:
            if weights:
                self.add_edge(
                    node, ending_node, weights[nodes.index(node)], **edge_attributes
                )
            else:
                self.add_edge(node, ending_node, weight=None, **edge_attributes)

    def add_edge(
        self,
        source_id: str | int,
        target_id: str | int,
        weight: float = 1.0,
        data: dict[str, str | int | float] | None = None,
        **edge_attributes,
    ) -> None:
        """Adds an edge to the graph.

        Parameters
        ----------
        source_id : str | int
            source node id
        target_id : str | int
            target node id
        weight : float, optional
            weight of the edge, by default 1.0
        data : dict[str, str | int | float] | None, optional
            Additional data attached to the edge, by default None

        Raises
        ------
        NodeDoesNotExistException
            If the source or target node does not exist in the graph.
        DuplicateEdgeException
            If the edge already exists in the graph.
        """
        if not self.contains_node(source_id):
            raise NodeDoesNotExistException(source_id)

        if not self.contains_node(target_id):
            raise NodeDoesNotExistException(target_id)

        if self.contains_edge(source_id, target_id):
            raise DuplicateEdgeException(source_id, target_id)

        edge = Edge(source_id, target_id, weight, data=data)
        self.edges[(edge.source, edge.destination)] = edge

        if weight is None:
            label = ""
        else:
            label = str(weight)

        graphviz_source_id = self.substitute_colons(edge.source)
        graphviz_target_id = self.substitute_colons(edge.destination)

        self.graph.edge(
            graphviz_source_id,
            graphviz_target_id,
            label=label,
            **edge_attributes,
        )

    def get_node(self, id: str | int) -> Node:
        """Returns the node with the given id.
        If the node id contains the colon substitute, it is replaced with a colon.

        Parameters
        ----------
        id : str | int
            The id of the node.

        Returns
        -------
        Node
            The node with the given id.

        Raises
        ------
        NodeDoesNotExistException
            If the node does not exist in the graph.
        """
        node_id = str(id).replace(self.colon_substitute, ":")
        if not self.contains_node(node_id):
            raise NodeDoesNotExistException(node_id)
        return self.nodes[str(node_id)]

    def get_edge(self, source: str | int, destination: str | int) -> Edge:
        """Returns the edge with the given source and destination nodes.
        If the node ids contain the colon substitute, it is replaced with a colon.

        Parameters
        ----------
        source : str | int
            source node id
        destination : str | int
            destination node id

        Returns
        -------
        Edge
            The edge with the given source and destination nodes and the weight.

        Raises
        ------
        EdgeDoesNotExistException
            If the edge does not exist in the graph.
        """
        source_id = self.substitute_colons_back(str(source))
        destination_id = self.substitute_colons_back(str(destination))
        if not self.contains_edge(source_id, destination_id):
            raise EdgeDoesNotExistException(source_id, destination_id)
        return self.edges[(source_id, destination_id)]

    def contains_node(self, id: str | int) -> bool:
        """Checks if the node with the given id exists in the graph.

        Parameters
        ----------
        id : str | int
            The id of the node.

        Returns
        -------
        bool
            True if the node exists in the graph, False otherwise.
        """
        return str(id) in self.nodes

    def contains_edge(self, source: str | int, destination: str | int) -> bool:
        """Checks if the edge with the given source and destination nodes exists in the graph.

        Parameters
        ----------
        source : str | int
            source node id
        destination : str | int
            destination node id

        Returns
        -------
        bool
            True if the edge exists in the graph, False otherwise.
        """
        edge = (str(source), str(destination))
        return edge in self.edges

    def get_nodes(self) -> list[Node]:
        """Returns the list of nodes in the graph.

        Returns
        -------
        list[Node]
            The list of nodes in the graph.
        """
        return list(self.nodes.values())

    def get_node_ids(self) -> list[str]:
        """Returns the list of node ids in the graph.

        Returns
        -------
        list[str]
            The list of node ids in the graph.
        """
        return list(self.nodes.keys())

    def get_edges(self) -> list[Edge]:
        """Returns the list of edges in the graph.

        Returns
        -------
        list[Edge]
            The list of edges in the graph.
        """
        return list(self.edges.values())

    def get_graphviz_string(self) -> str:
        """Returns the graphviz string of the graph.

        Returns
        -------
        str
            The graphviz string of the graph.
        """
        source = self.graph.source
        lines = []

        lines.extend(self._make_invisible_edge_lines())
        lines.extend(self._make_invisible_node_lines())
        lines.extend(self._make_highlighted_node_lines())

        closing_brace_index = source.rfind("}")
        if closing_brace_index == -1:
            return source + "\n" + "\n".join(lines)

        return (
            source[:closing_brace_index]
            + "\n"
            + "\n".join(lines)
            + "\n"
            + source[closing_brace_index:]
        )

    def _get_escaped_node_id(self, node_id: str) -> str:
        """Escape a Graphviz node id.

        Parameters
        ----------
        node_id : str
            The node id to quote/escape.

        Returns
        -------
        str
            The escaped Graphviz node id.
        """
        graphviz_node_id = self.substitute_colons(str(node_id))
        # Quote/escape the id so the injected DOT stays valid even if node ids contain special characters.
        escaped_node_id = graphviz_node_id.replace("\\", "\\\\").replace('"', '\\"')
        return escaped_node_id

    def _make_invisible_edge_lines(self) -> list[str]:
        """Create Graphviz lines for edges that are set to invisible.

        Returns
        -------
        list[str]
           Graphviz edges set to invisible.
        """
        lines = []
        for source_id, target_id in self._invisible_edge_ids:
            escaped_source_id = self._get_escaped_node_id(source_id)
            escaped_target_id = self._get_escaped_node_id(target_id)
            lines.append(
                f'\t"{escaped_source_id}" -> "{escaped_target_id}" [style="invis"];'
            )

        return lines

    def _make_invisible_node_lines(self) -> list[str]:
        """Create Graphviz lines for nodes that should be set to invisible.

        Returns
        -------
        list[str]
            Graphviz nodes set to invisible.
        """
        lines = []
        if self._invisible_node_ids:
            for node_id in self._invisible_node_ids:
                escaped_node_id = self._get_escaped_node_id(node_id)
                lines.append(f'\t"{escaped_node_id}" [style="invis"];')

        return lines

    def _make_highlighted_node_lines(self) -> list[str]:
        """Create Graphviz lines for highlighted nodes in fixed graph.

        Returns
        -------
        list[str]
            Graphviz highlighted nodes.
        """
        lines = []
        if self._highlighted_node_ids:
            # Inject "override" node statements before the closing brace.
            # Graphviz merges attributes for the same node id -> safely updates styling.
            for node_id in sorted(self._highlighted_node_ids):
                escaped_node_id = self._get_escaped_node_id(node_id)
                lines.append(
                    f'\t"{escaped_node_id}" '
                    f'[fillcolor="{self._highlight_fillcolor}", color="{self._highlight_bordercolor}", penwidth="2"];'
                )

        return lines

    def get_graphviz_graph(self) -> graphviz.Digraph:
        """Returns the graphviz graph of the graph.

        Returns
        -------
        graphviz.Digraph
            The graphviz graph of the graph.
        """
        return self.graph

    def node_to_string(self, id: str) -> tuple[str, str]:
        """Returns the id and description of the node with the given id.
        Can be overriden/extended in the child classes.

        Parameters
        ----------
        id : str
            The id of the node.

        Returns
        -------
        tuple[str, str]
            The id and description of the node.
        """
        node = self.get_node(id)
        description = ""
        if node.get_data():
            for key, value in node.get_data().items():
                if isinstance(value, float):
                    value = f"{float(value):.2f}"
                description += f"\n**{key}:** {value}"
        return node.get_id(), description

    def edge_to_string(self, source: str, destination: str) -> tuple[str, str]:
        """Return a textual representation for the edge connecting source and destination.
        Can be overridden in child classes for custom formatting.

        Parameters
        ----------
        source : str
            The source node id.
        destination : str
            The destination node id.

        Returns
        -------
        tuple[str, str]
            The edge name and a description containing weight and stored edge_data.
        """
        edge = self.get_edge(source, destination)
        name = f"{edge.source} -> {edge.destination}"
        description = ""
        if edge.get_data():
            for key, value in edge.get_data().items():
                if isinstance(value, float):
                    value = f"{float(value):.2f}"
                description += f"\n**{key}:** {value}"
        return name, description

    def substitute_colons(self, string: str) -> str:
        """Replaces the colon with the colon substitute in the string.

        Parameters
        ----------
        string : str
            The string to replace the colon with the colon substitute.

        Returns
        -------
        str
            The string with the colon substitute.
        """
        return string.replace(":", self.colon_substitute)

    def substitute_colons_back(self, string: str) -> str:
        """Replaces the colon substitute with the colon in the string.

        Parameters
        ----------
        string : str
            The string to replace the colon substitute with the colon.

        Returns
        -------
        str
            The string with the colon.
        """
        return string.replace(self.colon_substitute, ":")
