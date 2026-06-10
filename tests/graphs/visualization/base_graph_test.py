import unittest

from app.exceptions.graph_exceptions import (
    DuplicateNodeException,
    DuplicateEdgeException,
    NodeDoesNotExistException,
    EdgeDoesNotExistException,
    InvalidNodeNameException,
)
from app.graphs.visualization.base_graph import BaseGraph, Node, Edge


class TestNode(unittest.TestCase):

    def test_node_creation_without_label(self):
        node = Node("1")
        self.assertEqual(node.get_label(), "1")
        self.assertEqual(node.get_label(), "1")

    def test_node_creation_with_number_as_id(self):
        node = Node(1)
        self.assertEqual(node.get_id(), "1")

    def test_node_creation_with_additional_data(self):
        data = {"color": "red", "shape": "circle"}
        node = Node(1, data=data)
        self.assertEqual(node.get_data(), data)

    def test_node_creation_with_label(self):
        node = Node(1, "node1")
        self.assertEqual(node.get_label(), "node1")

    def test_node_get_data_from_correct_key(self):
        data = {"color": "red", "shape": "circle"}
        node = Node(1, data=data)
        self.assertEqual(node.get_data_from_key("color"), "red")
        self.assertEqual(node.get_data_from_key("shape"), "circle")

    def test_node_get_data_from_incorrect_key(self):
        data = {"color": "red", "shape": "circle"}
        node = Node(1, data=data)
        self.assertEqual(node.get_data_from_key("size"), None)


class TestEdge(unittest.TestCase):

    def test_edge_creation_with_numbers_as_node_ids(self):
        edge = Edge(1, 2)
        self.assertEqual(edge.source, "1")
        self.assertEqual(edge.destination, "2")

    def test_edge_creation_with_default_weight(self):
        edge = Edge(1, 2)
        self.assertEqual(edge.weight, 1)

    def test_edge_creation_with_custom_weight(self):
        edge = Edge(1, 2, 5)
        self.assertEqual(edge.weight, 5)

    def test_edge_get_edge(self):
        edge = Edge(1, 2, 5)
        self.assertEqual(edge.get_edge(), ("1", "2", 5))


class TestBaseGraph(unittest.TestCase):

    def test_default_base_graph_creation(self):
        graph = BaseGraph()
        self.assertEqual(graph.nodes, {})
        self.assertEqual(graph.edges, {})

    def test_adding_nodes_to_graph(self):
        graph = BaseGraph()
        graph.add_node(id=1, label="node1")

        nodes = graph.nodes
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes["1"].get_label(), "node1")

    def test_adding_nodes_with_same_id_throws_exception(self):
        graph = BaseGraph()
        graph.add_node(id=1, label="node1")

        with self.assertRaises(DuplicateNodeException):
            graph.add_node(id=1, label="node2")

    def test_adding_edges_to_graph_with_already_added_nodes(self):
        graph = BaseGraph()
        graph.add_node(id=1, label="node1")
        graph.add_node(id=2, label="node2")

        graph.add_edge(1, 2)

        edges = graph.edges
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[("1", "2")].get_edge(), ("1", "2", 1))

    def test_adding_edges_to_graph_with_not_added_nodes_throws_exception(self):
        graph = BaseGraph()
        with self.assertRaises(NodeDoesNotExistException):
            graph.add_edge(1, 2)

    def test_adding_edges_to_graph_with_weight(self):
        graph = BaseGraph()
        graph.add_node(id=1, label="node1")
        graph.add_node(id=2, label="node2")

        graph.add_edge(1, 2, 5)

        edges = graph.edges
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[("1", "2")].get_edge(), ("1", "2", 5))

    def test_adding_duplicate_edge_to_graph_throws_exception(self):
        graph = BaseGraph()
        graph.add_node(id=1, label="node1")
        graph.add_node(id=2, label="node2")

        graph.add_edge(1, 2, 5)

        with self.assertRaises(DuplicateEdgeException):
            graph.add_edge(1, 2, 5)

    def test_contains_node_without_nodes(self):
        graph = BaseGraph()
        self.assertEqual(graph.contains_node("1"), False)

    def test_contains_node_with_node(self):
        graph = BaseGraph()
        graph.add_node(id=1, label="node1")
        self.assertEqual(graph.contains_node("1"), True)

    def test_contains_node_with_node_id_as_int(self):
        graph = BaseGraph()
        graph.add_node(id=1, label="node1")
        self.assertEqual(graph.contains_node(1), True)

    def test_contains_edge_without_edges(self):
        graph = BaseGraph()
        self.assertEqual(graph.contains_edge("1", "2"), False)

    def test_contains_edge_with_edge(self):
        graph = BaseGraph()
        graph.add_node(1)
        graph.add_node(2)
        graph.add_edge(1, 2)
        self.assertEqual(graph.contains_edge("1", "2"), True)

    def test_contains_edge_with_edge_with_int_ids(self):
        graph = BaseGraph()
        graph.add_node(1)
        graph.add_node(2)
        graph.add_edge(1, 2)
        self.assertEqual(graph.contains_edge(1, 2), True)

    def test_get_node_with_existing_node(self):
        graph = BaseGraph()
        graph.add_node(id=1, label="node1")
        node = graph.get_node("1")
        self.assertEqual(node.id, "1")
        self.assertEqual(node.label, "node1")

    def test_get_node_with_non_existing_node(self):
        graph = BaseGraph()
        with self.assertRaises(NodeDoesNotExistException):
            graph.get_node("1")

    def test_get_edge_with_existing_edge(self):
        graph = BaseGraph()
        graph.add_node(1)
        graph.add_node(2)

        graph.add_edge(1, 2)
        edge = graph.get_edge("1", "2")
        self.assertEqual(edge.source, "1")
        self.assertEqual(edge.destination, "2")

    def test_get_edge_with_non_existing_edge(self):
        graph = BaseGraph()
        with self.assertRaises(EdgeDoesNotExistException):
            graph.get_edge("1", "2")

    def test_get_nodes_returns_empty_list_without_nodes(self):
        graph = BaseGraph()
        self.assertEqual(graph.get_nodes(), [])

    def test_get_nodes_returns_list_of_nodes(self):
        graph = BaseGraph()
        graph.add_node(id=1, label="node1")
        graph.add_node(id=2, label="node2")
        nodes = graph.get_nodes()
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].id, "1")
        self.assertEqual(nodes[1].id, "2")

    def test_get_edges_returns_empty_list_without_edges(self):
        graph = BaseGraph()
        self.assertEqual(graph.get_edges(), [])

    def test_get_edges_returns_list_of_edges(self):
        graph = BaseGraph()
        graph.add_node(1)
        graph.add_node(2)
        graph.add_node(3)

        graph.add_edge(1, 2)
        graph.add_edge(2, 3)
        edges = graph.get_edges()
        self.assertEqual(len(edges), 2)
        self.assertEqual(edges[0].get_edge(), ("1", "2", 1))
        self.assertEqual(edges[1].get_edge(), ("2", "3", 1))

    def test_node_id_with_triple_underscore_throws_exception(self):
        graph = BaseGraph()
        with self.assertRaises(InvalidNodeNameException):
            graph.add_node(id="node1___", label="node1___")

    def test_node_id_colon_substituted_with_trible_underscore_graphviz(self):
        graph = BaseGraph()
        graph.add_node(id="node1:1")
        graphviz_string = graph.get_graphviz_string()

        self.assertTrue(graph.contains_node("node1:1"))
        self.assertTrue("node1___1" in graphviz_string)

    def test_edge_source_colon_substituted_with_trible_underscore_graphviz(self):
        graph = BaseGraph()
        graph.add_node(id="node:1")
        graph.add_node(id="node2")
        graph.add_edge("node:1", "node2")
        graphviz_string = graph.get_graphviz_string()

        self.assertTrue(graph.contains_edge("node:1", "node2"))
        self.assertTrue("node___1 -> node2" in graphviz_string)

    def test_get_node_substitutes_colon_back(self):
        graph = BaseGraph()
        graph.add_node(id="node:1")
        node = graph.get_node("node___1")
        self.assertEqual(node.id, "node:1")

    def test_get_edge_substitutes_colon_back(self):
        graph = BaseGraph()
        graph.add_node(id="node:1")
        graph.add_node(id="node2")
        graph.add_edge("node:1", "node2")
        edge = graph.get_edge("node___1", "node2")
        self.assertEqual(edge.source, "node:1")
        self.assertEqual(edge.destination, "node2")

    def test_set_invisible_edges_applies_invisible_style_to_missing_edges(self):
        fixed_graph = BaseGraph()
        fixed_graph.add_node("node1")
        fixed_graph.add_node("node2")
        fixed_graph.add_node("node3")
        fixed_graph.add_edge("node1", "node2", 3)
        fixed_graph.add_edge("node1", "node3", 4)

        current_graph = BaseGraph()
        current_graph.add_node("node1")
        current_graph.add_node("node2")
        current_graph.add_node("node3")
        current_graph.add_edge("node1", "node2", 3)

        fixed_graph.set_invisible_edges(current_graph.get_edges())
        graphviz_string = fixed_graph.get_graphviz_string()

        self.assertIn("node1 -> node2 [label=3]", graphviz_string)
        self.assertIn("node1 -> node3 [label=4]", graphviz_string)
        self.assertIn('"node1" -> "node3" [style="invis"];', graphviz_string)

    def test_set_invisible_edges_handles_quoted_edge_ids(self):
        fixed_graph = BaseGraph()
        fixed_graph.add_node("Start")
        fixed_graph.add_node("task 1")
        fixed_graph.add_node("End")
        fixed_graph.add_edge("Start", "task 1", None)
        fixed_graph.add_edge("task 1", "End", None)

        current_graph = BaseGraph()
        current_graph.add_node("Start")
        current_graph.add_node("End")

        fixed_graph.set_invisible_nodes(current_graph.get_node_ids())
        fixed_graph.set_invisible_edges(current_graph.get_edges())
        graphviz_string = fixed_graph.get_graphviz_string()

        self.assertIn('Start -> "task 1" [label=""]', graphviz_string)
        self.assertIn('"task 1" -> End [label=""]', graphviz_string)
        self.assertIn('"Start" -> "task 1" [style="invis"];', graphviz_string)
        self.assertIn('"task 1" -> "End" [style="invis"];', graphviz_string)
        self.assertIn('"task 1" [style="invis"];', graphviz_string)


if __name__ == "__main__":
    unittest.main()
